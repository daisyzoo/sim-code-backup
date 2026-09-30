#!/usr/bin/env python3
"""Probe the image_server ZMQ stream payload format."""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import cv2
import numpy as np
import yaml
import zmq


FRAME_PAYLOAD_MAGIC = b"XRTIMG1\n"
FRAME_PAYLOAD_HEADER_LEN_BYTES = 4


def request_camera_config(host: str, port: int, timeout_ms: int) -> dict[str, Any] | None:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(f"tcp://{host}:{port}")
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    try:
        socket.send(b"GET_DATA")
        events = dict(poller.poll(timeout=timeout_ms))
        if socket not in events:
            return None
        return socket.recv_json()
    finally:
        socket.close()
        context.term()


def unpack_payload(payload: bytes) -> tuple[bytes, dict[str, Any], bool]:
    if not payload.startswith(FRAME_PAYLOAD_MAGIC):
        return payload, {}, False

    header_start = len(FRAME_PAYLOAD_MAGIC)
    header_end = header_start + FRAME_PAYLOAD_HEADER_LEN_BYTES
    if len(payload) < header_end:
        return payload, {}, False

    metadata_len = int.from_bytes(payload[header_start:header_end], "big")
    metadata_start = header_end
    metadata_end = metadata_start + metadata_len
    if len(payload) < metadata_end:
        return payload, {}, False

    try:
        metadata = json.loads(payload[metadata_start:metadata_end].decode("utf-8"))
    except Exception as exc:
        metadata = {"metadata_decode_error": repr(exc)}
    return payload[metadata_end:], metadata, True


def decode_compressed(body: bytes) -> np.ndarray | None:
    arr = np.frombuffer(body, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def infer_raw_shape(body: bytes, image_shape: list[int] | tuple[int, ...] | None) -> list[str]:
    if not image_shape or len(image_shape) < 2:
        return []

    h, w = int(image_shape[0]), int(image_shape[1])
    candidates = []
    for channels, dtype_name in ((3, "uint8"), (4, "uint8"), (1, "uint8"), (3, "float32")):
        dtype = np.dtype(dtype_name)
        expected = h * w * channels * dtype.itemsize
        if len(body) == expected:
            shape = (h, w) if channels == 1 else (h, w, channels)
            candidates.append(f"{dtype_name}{shape}")
    return candidates


def describe_payload(payload: bytes, image_shape: list[int] | tuple[int, ...] | None) -> str:
    body, metadata, has_magic = unpack_payload(payload)
    decoded = decode_compressed(body)
    first16 = body[:16].hex(" ")
    compressed = "yes" if decoded is not None else "no"
    decoded_shape = None if decoded is None else tuple(decoded.shape)
    raw_candidates = infer_raw_shape(body, image_shape)
    return (
        f"payload_bytes={len(payload)} body_bytes={len(body)} "
        f"xrt_header={has_magic} metadata={metadata} "
        f"body_first16_hex='{first16}' cv2_imdecode={compressed} "
        f"decoded_shape={decoded_shape} raw_shape_candidates={raw_candidates}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="192.168.123.164")
    parser.add_argument("--request-port", type=int, default=60000)
    parser.add_argument("--zmq-port", type=int, default=None, help="Subscribe directly to this ZMQ port.")
    parser.add_argument("--camera", default="head_camera")
    parser.add_argument("--frames", type=int, default=5)
    parser.add_argument("--timeout-ms", type=int, default=3000)
    parser.add_argument("--max-timeouts", type=int, default=3)
    parser.add_argument(
        "--local-config",
        default="unitree_lerobot/cam_config_client.yaml",
        help="Fallback camera config used with --zmq-port or when request_port is unavailable.",
    )
    args = parser.parse_args()

    cam_config = None if args.zmq_port is not None else request_camera_config(args.host, args.request_port, args.timeout_ms)
    if cam_config is None:
        try:
            with open(args.local_config, "r", encoding="utf-8") as f:
                cam_config = yaml.safe_load(f)
            print(f"loaded local config from {args.local_config}")
        except Exception as exc:
            if args.zmq_port is None:
                raise SystemExit(f"No camera config response from tcp://{args.host}:{args.request_port}") from exc
            cam_config = {}

    camera_config = cam_config.get(args.camera, {}) if isinstance(cam_config, dict) else {}
    if args.zmq_port is None:
        if args.camera not in cam_config:
            raise SystemExit(f"Camera '{args.camera}' not in config keys={list(cam_config)}")
        if not camera_config.get("enable_zmq", False):
            raise SystemExit(f"{args.camera} has enable_zmq=false in config: {camera_config}")

    port = int(args.zmq_port if args.zmq_port is not None else camera_config["zmq_port"])
    image_shape = camera_config.get("image_shape")
    print(f"config[{args.camera}]={camera_config}")
    print(f"subscribing tcp://{args.host}:{port}")

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.RCVHWM, 1)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    socket.connect(f"tcp://{args.host}:{port}")
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    try:
        received = 0
        timeouts = 0
        start = time.monotonic()
        while received < args.frames:
            events = dict(poller.poll(timeout=args.timeout_ms))
            if socket not in events:
                timeouts += 1
                elapsed = time.monotonic() - start
                print(f"timeout after {args.timeout_ms} ms; received={received}; elapsed_s={elapsed:.3f}")
                if timeouts >= args.max_timeouts:
                    raise SystemExit(f"No payload received after {timeouts} consecutive timeouts.")
                continue
            payload = socket.recv()
            timeouts = 0
            received += 1
            print(f"frame[{received}]: {describe_payload(payload, image_shape)}")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
