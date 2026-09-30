#!/usr/bin/env python3
"""PI0.5 sorting policy TCP server (vla venv). Isaac client talks pickle-over-TCP.

Protocol: 4-byte big-endian length + pickle payload.

Request:  {"cmd": "infer", "image": uint8 HWC RGB, "state": float32[11], "task": str}
          {"cmd": "ping"} | {"cmd": "shutdown"}
Response: {"ok": True, "actions": float32[T,11], "infer_ms": float, ...} or {"ok": False, "error": str}
"""

from __future__ import annotations

import argparse
import pickle
import socket
import struct
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
import torch

from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS


DEFAULT_PROMPT = (
    "Sort the package on the table by type. If there is no package on the table, keep both "
    "arms still and wait. If it is a black bag, press and hold the bag down with the left "
    "hand, then push it to the left sorting area. If it is a box, press and hold the box "
    "down with the right hand, then push it to the right sorting area."
)


def _recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf.extend(chunk)
    return bytes(buf)


def recv_msg(conn: socket.socket) -> dict[str, Any]:
    (length,) = struct.unpack("!I", _recv_exact(conn, 4))
    if length > 64 * 1024 * 1024:
        raise ValueError(f"payload too large: {length}")
    return pickle.loads(_recv_exact(conn, length))


def send_msg(conn: socket.socket, payload: dict[str, Any]) -> None:
    blob = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    conn.sendall(struct.pack("!I", len(blob)) + blob)


class Pi05Server:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        torch.manual_seed(args.seed)
        np.random.seed(args.seed)
        policy_path = str(args.policy_path)
        config = PreTrainedConfig.from_pretrained(policy_path)
        config.pretrained_path = policy_path
        config.device = args.device
        config.num_inference_steps = args.num_inference_steps
        ds_meta = LeRobotDatasetMetadata(repo_id=args.repo_id, root=str(args.dataset_root))
        self.policy = make_policy(config, ds_meta=ds_meta)
        self.policy.eval()
        if hasattr(self.policy.model, "gradient_checkpointing_disable"):
            self.policy.model.gradient_checkpointing_disable()
        overrides = {
            "device_processor": {"device": args.device},
            "tokenizer_processor": {
                "tokenizer_name": str(args.tokenizer_path),
                "local_files_only": True,
            },
        }
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            policy_cfg=config,
            pretrained_path=policy_path,
            dataset_stats=ds_meta.stats,
            preprocessor_overrides=overrides,
        )
        from lerobot.policies.pi05.joint_relative import validate_relative_pipeline
        validate_relative_pipeline(config, self.preprocessor)
        self.joint_action_representation = config.joint_action_representation
        self.action_dim = int(config.output_features["action"].shape[0])
        self.chunk_size = int(config.chunk_size)
        self.noise_shape = (1, config.chunk_size, config.max_action_dim)
        self.device = torch.device(args.device)
        print(
            f"loaded PI0.5  action_dim={self.action_dim} chunk={self.chunk_size} "
            f"device={args.device} path={policy_path}",
            flush=True,
        )

    def infer(self, image_rgb: np.ndarray, state: np.ndarray, task: str) -> np.ndarray:
        image = np.asarray(image_rgb)
        if image.ndim != 3 or image.shape[-1] not in (3, 4):
            raise ValueError(f"expected HWC RGB, got {image.shape}")
        image = image[..., :3]
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8) if image.max() > 1.5 else (
                np.clip(image * 255.0, 0, 255).astype(np.uint8)
            )
        if image.shape[0] != 480 or image.shape[1] != 640:
            import cv2

            image = cv2.resize(image, (640, 480), interpolation=cv2.INTER_AREA)
        state = np.asarray(state, dtype=np.float32).reshape(-1)
        if state.shape[0] != self.action_dim:
            raise ValueError(f"expected state[{self.action_dim}], got {state.shape}")
        observation: dict[str, Any] = {
            "observation.images.color_0": torch.from_numpy(np.ascontiguousarray(image))
            .to(torch.float32)
            .div(255.0)
            .permute(2, 0, 1)
            .contiguous()
            .unsqueeze(0),
            "observation.state": torch.from_numpy(state.copy()).unsqueeze(0),
            "task": task,
            "robot_type": "",
        }
        self.preprocessor.reset()
        batch = self.preprocessor(observation)
        images, image_masks = self.policy._preprocess_images(batch)
        tokens = batch[OBS_LANGUAGE_TOKENS]
        masks = batch[OBS_LANGUAGE_ATTENTION_MASK]
        noise = torch.randn(self.noise_shape, device=self.device, dtype=torch.float32)
        with torch.inference_mode():
            actions = self.policy.model.sample_actions(
                images,
                image_masks,
                tokens,
                masks,
                noise=noise,
                num_steps=self.args.num_inference_steps,
            )[:, :, : self.action_dim]
            self.postprocessor.reset()
            actions = self.postprocessor(actions)
        if self.joint_action_representation == "state_relative_arm10":
            from lerobot.policies.pi05.joint_relative import joint_action_transform
            actions = joint_action_transform(actions, torch.from_numpy(state.copy()).unsqueeze(0), inverse=True)
        return np.asarray(actions.squeeze(0).detach().cpu().numpy(), dtype=np.float32)

    def warmup(self) -> None:
        dummy = np.full((480, 640, 3), 40, dtype=np.uint8)
        state = np.zeros((self.action_dim,), dtype=np.float32)
        t0 = time.perf_counter()
        acts = self.infer(dummy, state, DEFAULT_PROMPT)
        dt = (time.perf_counter() - t0) * 1000.0
        print(f"warmup chunk={acts.shape}  {dt:.0f} ms", flush=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=18765)
    p.add_argument(
        "--policy-path",
        type=Path,
        default=Path(
            "/home/user/Documents/zoo/sim/lerobot/outputs/"
            "package_sorting_pi05_1gpu_20260909_122124/checkpoints/028562/pretrained_model"
        ),
    )
    p.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/lerobot/lerobot_v3.0"),
    )
    p.add_argument("--repo-id", default="local/package_sorting_unified")
    p.add_argument(
        "--tokenizer-path",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224"),
    )
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--seed", type=int, default=0, help="Deterministic PI0.5 flow-noise seed.")
    p.add_argument("--num-inference-steps", type=int, default=10)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    server = Pi05Server(args)
    server.warmup()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    sock.listen(1)
    print(f"PI05_SERVER_READY {args.host}:{args.port}", flush=True)
    try:
        while True:
            conn, addr = sock.accept()
            conn.settimeout(120.0)
            try:
                req = recv_msg(conn)
                cmd = str(req.get("cmd", "infer"))
                if cmd == "ping":
                    send_msg(conn, {"ok": True, "cmd": "pong"})
                    continue
                if cmd == "reset_seed":
                    seed = int(req["seed"])
                    torch.manual_seed(seed)
                    np.random.seed(seed)
                    send_msg(conn, {"ok": True, "seed": seed})
                    continue
                if cmd == "shutdown":
                    send_msg(conn, {"ok": True, "cmd": "bye"})
                    break
                t0 = time.perf_counter()
                actions = server.infer(req["image"], req["state"], req.get("task") or DEFAULT_PROMPT)
                infer_ms = (time.perf_counter() - t0) * 1000.0
                left = float(np.sqrt(np.mean(actions[:, :5] ** 2)))
                right = float(np.sqrt(np.mean(actions[:, 5:10] ** 2)))
                print(
                    f"infer {infer_ms:.0f} ms  shape={tuple(actions.shape)}  "
                    f"left_rms={left:.3f} right_rms={right:.3f} from={addr}",
                    flush=True,
                )
                send_msg(
                    conn,
                    {
                        "ok": True,
                        "actions": actions,
                        "infer_ms": infer_ms,
                        "left_rms": left,
                        "right_rms": right,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                try:
                    send_msg(conn, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
                except Exception:
                    pass
            finally:
                conn.close()
    finally:
        sock.close()
        print("PI05_SERVER_STOP", flush=True)


if __name__ == "__main__":
    main()
