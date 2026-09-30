#!/usr/bin/env python3
"""Closed-loop PI0.5 on SimFoundry sorting station (Isaac client).

Talks to scripts/pi05_policy_server.py (vla venv). Maps 11-D absolute joints
(left 5 + right 5 + waist_yaw) to Isaac 23-D rest-offset actions.

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/demo_pi05_sorting.py \\
      --num_envs 1 --device cuda --viz kit --save-preview
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import socket
import struct
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="PI0.5 closed-loop sorting-station demo.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--hold-start-s", type=float, default=1.5)
parser.add_argument("--task-s", type=float, default=12.0)
parser.add_argument("--hold-end-s", type=float, default=1.0)
parser.add_argument("--horizon", type=int, default=10, help="receding-horizon steps per chunk")
parser.add_argument("--policy-host", default="127.0.0.1")
parser.add_argument("--policy-port", type=int, default=18765)
parser.add_argument("--realtime", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--record", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--record-dir", type=str, default="")
parser.add_argument("--save-preview", action="store_true")
parser.add_argument(
    "--task",
    default=(
        "Sort the package on the table by type. If there is no package on the table, keep both "
        "arms still and wait. If it is a black bag, press and hold the bag down with the left "
        "hand, then push it to the left sorting area. If it is a box, press and hold the box "
        "down with the right hand, then push it to the right sorting area."
    ),
)
parser.add_argument("--box-task", default="", help="Override prompt for box_only closed-loop segment.")
parser.add_argument("--mailer-task", default="", help="Override prompt for mailer_only closed-loop segment.")
parser.add_argument("--wait-task", default="", help="Override prompt for wait_empty closed-loop segment.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.utils.math import quat_apply

from simfoundry.calibration.sorting_station import (
    SORTING_BOX_REST_SINGLE,
    SORTING_MAILER_REST_SINGLE,
    TABLE_TOP_Z,
)
from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg
from simfoundry.data.sorting_quality import PALM_OFFSET
from simfoundry.robots.g1_assets import (
    G1_U1_23DOF_JOINT_NAMES,
    clip_sorting_action_offset,
    u1_sorting_default_qpos_np,
)
from simfoundry.scene_bridge.labels import sync_shipping_labels

_BOX_REST = SORTING_BOX_REST_SINGLE
_MAILER_REST = SORTING_MAILER_REST_SINGLE
_OFF_TABLE = (6.0, 6.0, 0.20)
_TABLE_TOP = TABLE_TOP_Z
_TOUCH_XY = 0.12
_TOUCH_Z = 0.08
_PALM_OFFSET = PALM_OFFSET
_OVERVIEW_EYE = (-1.60, -2.10, 1.85)
_OVERVIEW_LOOK = (0.40, 0.0, 0.78)
_LEFT_ARM = slice(13, 18)
_RIGHT_ARM = slice(18, 23)
_WAIST = 12
_HAND_PATTERNS = {
    "left": ["left_wrist_roll_rubber_hand", "left_wrist_roll_link", "left_rubber_hand"],
    "right": ["right_wrist_roll_rubber_hand", "right_wrist_roll_link", "right_rubber_hand"],
}


def _yaw_xyzw(yaw: float = 0.0) -> tuple[float, float, float, float]:
    return (0.0, 0.0, math.sin(yaw * 0.5), math.cos(yaw * 0.5))


def _to_uint8_hwc(frame) -> np.ndarray:
    if hasattr(frame, "torch"):
        frame = frame.torch
    if isinstance(frame, torch.Tensor):
        x = frame.detach().cpu()
        if x.ndim == 3 and x.shape[0] in (3, 4):
            x = x[:3].permute(1, 2, 0)
        elif x.ndim == 3 and x.shape[-1] in (3, 4):
            x = x[..., :3]
        else:
            raise ValueError(f"unexpected frame shape {tuple(x.shape)}")
        if x.dtype != torch.uint8:
            arr = x.float().numpy()
            if arr.max() <= 1.5:
                arr = arr * 255.0
            return np.clip(arr, 0, 255).astype(np.uint8)
        return x.numpy()
    arr = np.asarray(frame)
    if arr.ndim == 3 and arr.shape[0] in (3, 4):
        arr = np.transpose(arr[:3], (1, 2, 0))
    elif arr.ndim == 3 and arr.shape[-1] in (3, 4):
        arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = arr.astype(np.float32)
        if arr.max() <= 1.5:
            arr = arr * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def _q23_to_state11(q23: np.ndarray) -> np.ndarray:
    q = np.asarray(q23, dtype=np.float32).reshape(-1)
    if q.shape[0] != 23:
        raise ValueError(f"expected 23-DoF q, got {q.shape}")
    return np.concatenate([q[_LEFT_ARM], q[_RIGHT_ARM], q[_WAIST:_WAIST + 1]]).astype(np.float32)


def _abs11_to_offset23(act11: np.ndarray, default_q: np.ndarray) -> np.ndarray:
    q = default_q.astype(np.float32).copy()
    a = np.asarray(act11, dtype=np.float32).reshape(-1)
    q[13:18] = a[0:5]
    q[18:23] = a[5:10]
    q[12] = a[10]
    return clip_sorting_action_offset(q - default_q)


def _send_recv(host: str, port: int, payload: dict, timeout: float = 90.0) -> dict:
    blob = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.settimeout(timeout)
        conn.sendall(struct.pack("!I", len(blob)) + blob)
        header = b""
        while len(header) < 4:
            chunk = conn.recv(4 - len(header))
            if not chunk:
                raise ConnectionError("policy server closed")
            header += chunk
        (length,) = struct.unpack("!I", header)
        data = b""
        while len(data) < length:
            chunk = conn.recv(length - len(data))
            if not chunk:
                raise ConnectionError("policy server closed mid-payload")
            data += chunk
    reply = pickle.loads(data)
    if not reply.get("ok"):
        raise RuntimeError(reply.get("error", "policy infer failed"))
    return reply


def _pose_tensor(xyz: tuple[float, float, float], device: torch.device) -> torch.Tensor:
    qx, qy, qz, qw = _yaw_xyzw(0.0)
    return torch.tensor([[xyz[0], xyz[1], xyz[2], qx, qy, qz, qw]], dtype=torch.float32, device=device)


def main() -> None:
    record_dir = Path(args_cli.record_dir) if args_cli.record_dir else ROOT / "demo" / "preview_pi05_sorting"
    record_dir.mkdir(parents=True, exist_ok=True)

    ping = _send_recv(args_cli.policy_host, args_cli.policy_port, {"cmd": "ping"}, timeout=10.0)
    print(f"policy server ping={ping}")

    env_cfg = SortingStationEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env_cfg.episode_length_s = 180.0
    env = ManagerBasedRLEnv(cfg=env_cfg)
    env.reset()

    step_dt = float(env.step_dt)
    hold_start = max(1, int(round(args_cli.hold_start_s / step_dt)))
    task_steps = max(16, int(round(args_cli.task_s / step_dt)))
    hold_end = max(1, int(round(args_cli.hold_end_s / step_dt)))
    horizon = max(1, int(args_cli.horizon))
    zero = torch.zeros((env.num_envs, 23), dtype=torch.float32, device=env.device)
    zero_vel = torch.zeros((env.num_envs, 6), dtype=torch.float32, device=env.device)
    default_q = u1_sorting_default_qpos_np()

    robot = env.scene["robot"]
    print(f"  robot joints ({len(robot.joint_names)}): {list(robot.joint_names)[:8]}...")
    print(f"  expected U1 order match: {list(robot.joint_names)[:23] == list(G1_U1_23DOF_JOINT_NAMES)}")

    hand_idx: dict[str, int] = {}
    for side, patterns in _HAND_PATTERNS.items():
        for pattern in patterns:
            ids, names = robot.find_bodies(pattern)
            if ids:
                idx = ids[0]
                if hasattr(idx, "item"):
                    idx = idx.item()
                hand_idx[side] = int(idx)
                print(f"  {side} hand body: {names[0]}  idx={hand_idx[side]}")
                break
        if side not in hand_idx:
            raise RuntimeError(f"could not resolve U1 rubber-hand body for {side}")

    print("=" * 72)
    print("PI0.5 closed-loop sorting station")
    print(f"  policy {args_cli.policy_host}:{args_cli.policy_port}  horizon={horizon}")
    print(f"  record {record_dir}")
    print("=" * 72)

    head_writer = None
    view_writer = None
    if args_cli.record:
        import cv2

        fps = max(1, int(round(1.0 / step_dt)))
        head_writer = cv2.VideoWriter(
            str(record_dir / "head_d435i.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (640, 480)
        )
        view_writer = cv2.VideoWriter(
            str(record_dir / "kit_viewport.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (960, 540)
        )

    def _place(name: str, xyz: tuple[float, float, float]) -> None:
        asset = env.scene[name]
        asset.write_root_pose_to_sim_index(root_pose=_pose_tensor(xyz, env.device))
        if hasattr(asset, "write_root_velocity_to_sim_index"):
            asset.write_root_velocity_to_sim_index(root_velocity=zero_vel)

    def _xyz(name: str) -> tuple[float, float, float]:
        p = env.scene[name].data.root_pos_w[0]
        if hasattr(p, "torch"):
            p = p.torch
        return (float(p[0]), float(p[1]), float(p[2]))

    def _hand_xyz(side: str) -> tuple[float, float, float]:
        idx = hand_idx[side]
        p = robot.data.body_pos_w[0, idx]
        q = robot.data.body_quat_w[0, idx]
        if hasattr(p, "torch"):
            p = p.torch
        if hasattr(q, "torch"):
            q = q.torch
        offset = torch.tensor(_PALM_OFFSET, dtype=torch.float32, device=p.device)
        palm = p + quat_apply(q.unsqueeze(0), offset.unsqueeze(0))[0]
        return (float(palm[0]), float(palm[1]), float(palm[2]))

    def _sync_labels() -> None:
        sync_shipping_labels(env)

    def _touching(hand: tuple[float, float, float], obj: tuple[float, float, float]) -> bool:
        dx = hand[0] - obj[0]
        dy = hand[1] - obj[1]
        dz = hand[2] - obj[2]
        return (dx * dx + dy * dy) ** 0.5 < _TOUCH_XY and abs(dz) < _TOUCH_Z

    def _set_views(eye, look) -> None:
        env.sim.set_camera_view(eye, look)
        cam = env.scene.sensors.get("viewer_cam")
        if cam is None:
            return
        eyes = torch.tensor([eye], dtype=torch.float32, device=env.device).repeat(env.num_envs, 1)
        targets = torch.tensor([look], dtype=torch.float32, device=env.device).repeat(env.num_envs, 1)
        try:
            cam.set_world_poses_from_view(eyes, targets)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] viewer_cam pose: {exc}")
        if hasattr(cam, "update"):
            try:
                cam.update(dt=0.0, force_recompute=True)
            except TypeError:
                try:
                    cam.update(0.0)
                except Exception:
                    pass

    def _write_frame(writer, frame, size: tuple[int, int]) -> None:
        if writer is None:
            return
        import cv2

        rgb = _to_uint8_hwc(frame)
        if rgb.shape[0] != size[1] or rgb.shape[1] != size[0]:
            rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
        writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    def _record(obs) -> None:
        if not args_cli.record or obs is None:
            return
        try:
            rgb = obs.get("rgb", None) if isinstance(obs, dict) else None
            if rgb is not None:
                _write_frame(head_writer, rgb[0], (640, 480))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] head record skip: {exc}")
            return
        if view_writer is None:
            return
        try:
            cam = env.scene.sensors.get("viewer_cam")
            if cam is None:
                return
            output = getattr(getattr(cam, "data", None), "output", None)
            if output is None or "rgb" not in output:
                return
            frame = output["rgb"]
            if hasattr(frame, "torch"):
                frame = frame.torch
            _write_frame(view_writer, frame[0], (960, 540))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] viewport record skip: {exc}")

    def _save_head_png(obs, stem: str) -> None:
        if not args_cli.save_preview or obs is None:
            return
        import cv2

        try:
            rgb = obs.get("rgb", None) if isinstance(obs, dict) else None
            if rgb is None:
                return
            cv2.imwrite(str(record_dir / f"{stem}.png"), cv2.cvtColor(_to_uint8_hwc(rgb[0]), cv2.COLOR_RGB2BGR))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] png skip {stem}: {exc}")

    def _obs_q23(obs) -> np.ndarray:
        if isinstance(obs, dict) and "policy" in obs:
            q = obs["policy"]
            if hasattr(q, "torch"):
                q = q.torch
            arr = q[0].detach().cpu().numpy() if isinstance(q, torch.Tensor) else np.asarray(q[0])
            if arr.shape[-1] == 23:
                return arr.astype(np.float32)
        jp = robot.data.joint_pos[0]
        if hasattr(jp, "torch"):
            jp = jp.torch
        return jp.detach().cpu().numpy().astype(np.float32)[:23]

    def _clip_action(action: torch.Tensor) -> torch.Tensor:
        off = clip_sorting_action_offset(action[0].detach().cpu().numpy())
        return torch.from_numpy(off).to(action.device).unsqueeze(0)

    def _tick(action: torch.Tensor, eye, look, log: bool = False):
        if not simulation_app.is_running():
            return None
        t0 = time.perf_counter()
        action = _clip_action(action)
        _set_views(eye, look)
        obs, *_ = env.step(action)
        _sync_labels()
        _record(obs)
        if log:
            left = _hand_xyz("left")
            right = _hand_xyz("right")
            box = _xyz("parcel_box")
            mailer = _xyz("mailer")
            print(
                f"    Rpalm {right[0]:.2f},{right[1]:.2f},{right[2]:.2f}  "
                f"box {box[0]:.2f},{box[1]:.2f}  Lpalm {left[0]:.2f},{left[1]:.2f}  "
                f"mailer {mailer[0]:.2f},{mailer[1]:.2f}"
            )
        if args_cli.realtime:
            delay = t0 + step_dt - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
        return obs

    def _hold(n: int, eye, look, label: str) -> None:
        print(f"[{label}]")
        for _ in range(n):
            if not simulation_app.is_running():
                return
            _tick(zero, eye, look)

    log_path = record_dir / "infer_log.jsonl"
    log_fp = log_path.open("w", encoding="utf-8")
    summary: list[dict] = []

    def _closed_loop(task_id: str, title: str, n_steps: int) -> dict:
        print("-" * 72)
        print(f"[{title}]  closed-loop PI0.5  steps={n_steps} horizon={horizon}")
        eye, look = _OVERVIEW_EYE, _OVERVIEW_LOOK
        obs = None
        chunk: np.ndarray | None = None
        cursor = 0
        touches = {"box": 0, "mailer": 0}
        touches_by_hand = {"left_box": 0, "right_box": 0, "left_mailer": 0, "right_mailer": 0}
        palm_start = {"left": _hand_xyz("left"), "right": _hand_xyz("right")}
        palm_max_displacement = {"left": 0.0, "right": 0.0}
        start_box, start_mailer = _xyz("parcel_box"), _xyz("mailer")
        infers = 0
        last_meta: dict = {}
        for i in range(n_steps):
            if not simulation_app.is_running():
                break
            if chunk is None or cursor >= min(horizon, int(chunk.shape[0])):
                rgb = None
                if isinstance(obs, dict):
                    rgb = obs.get("rgb")
                if rgb is None:
                    obs = _tick(zero, eye, look)
                    rgb = obs.get("rgb") if isinstance(obs, dict) else None
                image = _to_uint8_hwc(rgb[0])
                state11 = _q23_to_state11(_obs_q23(obs))
                t0 = time.perf_counter()
                if task_id == "box_only":
                    infer_task = getattr(args_cli, "box_task", None) or args_cli.task
                elif task_id == "mailer_only":
                    infer_task = getattr(args_cli, "mailer_task", None) or args_cli.task
                else:
                    infer_task = getattr(args_cli, "wait_task", None) or args_cli.task
                reply = _send_recv(
                    args_cli.policy_host,
                    args_cli.policy_port,
                    {"cmd": "infer", "image": image, "state": state11, "task": infer_task},
                )
                chunk = np.asarray(reply["actions"], dtype=np.float32)
                cursor = 0
                infers += 1
                last_meta = {
                    "infer_ms": reply.get("infer_ms"),
                    "left_rms": reply.get("left_rms"),
                    "right_rms": reply.get("right_rms"),
                }
                rec = {
                    "task_id": task_id,
                    "step": i,
                    "infer": infers,
                    "state11": state11.tolist(),
                    "act0": chunk[0].tolist(),
                    "wall_ms": (time.perf_counter() - t0) * 1000.0,
                    **last_meta,
                }
                log_fp.write(json.dumps(rec) + "\n")
                log_fp.flush()
                print(
                    f"  infer#{infers} @{i}  {last_meta.get('infer_ms', 0):.0f} ms  "
                    f"L={last_meta.get('left_rms'):.3f} R={last_meta.get('right_rms'):.3f}"
                )
                if infers == 1:
                    _save_head_png(obs, f"{task_id}_t0")
            act11 = chunk[cursor]
            cursor += 1
            offset = _abs11_to_offset23(act11, default_q)
            action = torch.from_numpy(offset).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
            obs = _tick(action, eye, look, log=(i % 30 == 0))
            left, right = _hand_xyz("left"), _hand_xyz("right")
            for side, palm in (("left", left), ("right", right)):
                start = palm_start[side]
                palm_max_displacement[side] = max(
                    palm_max_displacement[side],
                    float(sum((palm[j] - start[j]) ** 2 for j in range(3)) ** 0.5),
                )
            box, mailer = _xyz("parcel_box"), _xyz("mailer")
            left_box, right_box = _touching(left, box), _touching(right, box)
            left_mailer, right_mailer = _touching(left, mailer), _touching(right, mailer)
            touches_by_hand["left_box"] += int(left_box)
            touches_by_hand["right_box"] += int(right_box)
            touches_by_hand["left_mailer"] += int(left_mailer)
            touches_by_hand["right_mailer"] += int(right_mailer)
            if right_box or left_box:
                touches["box"] += 1
            if right_mailer or left_mailer:
                touches["mailer"] += 1
        _save_head_png(obs, f"{task_id}_end")
        end_box, end_mailer = _xyz("parcel_box"), _xyz("mailer")
        result = {
            "task_id": task_id,
            "title": title,
            "steps": n_steps,
            "infers": infers,
            "touches": touches,
            "touches_by_hand": touches_by_hand,
            "palm_max_displacement": palm_max_displacement,
            "start_box": start_box,
            "end_box": end_box,
            "start_mailer": start_mailer,
            "end_mailer": end_mailer,
            "box_xy_delta": (end_box[0] - start_box[0], end_box[1] - start_box[1]),
            "mailer_xy_delta": (end_mailer[0] - start_mailer[0], end_mailer[1] - start_mailer[1]),
        }
        print(
            f"  done infers={infers} touches={touches}  "
            f"box Δxy={result['box_xy_delta']}  mailer Δxy={result['mailer_xy_delta']}"
        )
        return result

    try:
        _place("parcel_box", _BOX_REST)
        _place("mailer", _OFF_TABLE)
        try:
            _place("mailer_b", _OFF_TABLE)
        except (KeyError, AttributeError):
            pass
        _sync_labels()
        _hold(hold_start, _OVERVIEW_EYE, _OVERVIEW_LOOK, "静置：桌上只有纸盒")
        _place("parcel_box", _BOX_REST)
        _place("mailer", _OFF_TABLE)
        _sync_labels()
        summary.append(_closed_loop("box_only", "推纸盒（右手）", task_steps))

        _hold(8, _OVERVIEW_EYE, _OVERVIEW_LOOK, "切换场景")
        _place("parcel_box", _OFF_TABLE)
        _place("mailer", _MAILER_REST)
        _sync_labels()
        _hold(hold_start, _OVERVIEW_EYE, _OVERVIEW_LOOK, "静置：桌上只有黑袋")
        _place("mailer", _MAILER_REST)
        _place("parcel_box", _OFF_TABLE)
        _sync_labels()
        summary.append(_closed_loop("mailer_only", "拨黑袋（左手）", task_steps))

        _hold(8, _OVERVIEW_EYE, _OVERVIEW_LOOK, "切换空桌")
        _place("parcel_box", _OFF_TABLE)
        _place("mailer", _OFF_TABLE)
        _sync_labels()
        _hold(hold_start, _OVERVIEW_EYE, _OVERVIEW_LOOK, "静置：空桌等待")
        summary.append(_closed_loop("wait_empty", "空桌等待（双臂静止）", max(45, task_steps // 4)))
        _hold(hold_end, _OVERVIEW_EYE, _OVERVIEW_LOOK, "收尾")
    finally:
        log_fp.close()

    payload = {"summary": summary, "horizon": horizon, "task_s": args_cli.task_s, "prompt": args_cli.task}
    (record_dir / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (record_dir / "preview.html").write_text(
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>PI0.5 分拣台仿真推理</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 1rem; background: #1a1a1a; color: #eee; }
    video { max-width: 100%; background: #000; border-radius: 8px; }
    h2 { margin-top: 1.5rem; }
    a { color: #7cb3ff; }
  </style>
</head>
<body>
  <h1>PI0.5 分拣台仿真推理</h1>
  <p>先纸盒、后黑袋。头显 D435i + Kit 第三人称。</p>
  <h2>头显 D435i</h2>
  <video controls src="head_d435i.mp4"></video>
  <h2>Kit 第三人称</h2>
  <video controls src="kit_viewport.mp4"></video>
</body>
</html>
""",
        encoding="utf-8",
    )

    if head_writer is not None:
        head_writer.release()
    if view_writer is not None:
        view_writer.release()
    env.close()
    simulation_app.close()
    print(json.dumps(payload["summary"], indent=2))
    print("done.")


if __name__ == "__main__":
    main()
