#!/usr/bin/env python3
"""Sorting-station demo: G1 23 U1 rubber hands push kraft box / black mailer.

Primary recording is the robot D435i headset. Kit Perspective also streams D435i.

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/demo_sorting_station.py \\
      --num_envs 1 --device cuda --viz kit --save-preview
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="SimFoundry sorting-station stump demo.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--hold-start-s", type=float, default=2.5)
parser.add_argument("--task-s", type=float, default=7.0)
parser.add_argument("--hold-end-s", type=float, default=2.5)
parser.add_argument("--realtime", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--record", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--record-dir", type=str, default="")
parser.add_argument("--save-preview", action="store_true")
parser.add_argument("--photo-seed", type=int, default=None, help="Seed for parcel albedo draw. Omit for random.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import numpy as np
import torch

from isaaclab.envs import ManagerBasedRLEnv
from isaaclab.utils.math import quat_apply

from simfoundry.data.scripted import scripted_action
from simfoundry.data.sorting_quality import PALM_OFFSET
from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg
from simfoundry.scene_bridge.labels import sync_shipping_labels

from simfoundry.calibration.sorting_station import (
    SORTING_BOX_REST,
    SORTING_MAILER_REST,
    TABLE_TOP_Z,
    reset_sorting_parcels,
)
from simfoundry.robots.g1_assets import clip_sorting_action_offset

# Parcels inset so a push toward -X cannot tip them off the front edge.
_BOX_REST = SORTING_BOX_REST
_MAILER_REST = SORTING_MAILER_REST
_TABLE_TOP = TABLE_TOP_Z
_TABLE_TOP_BOX = SORTING_BOX_REST[2]
_TABLE_TOP_MAILER = SORTING_MAILER_REST[2]
_MAILER_B_REST = (0.52, 0.30, _TABLE_TOP + 0.035 / 2 + 0.002)
# Tight proximity for logging only — parcels move solely via PhysX hand contact.
_TOUCH_XY = 0.12
_TOUCH_Z = 0.08
_PALM_OFFSET = PALM_OFFSET

# Third-person Kit overview: behind-right of robot, clear of backdrop / bins.
_OVERVIEW_EYE = (-1.60, -2.10, 1.85)
_OVERVIEW_LOOK = (0.40, 0.0, 0.78)
_TASK_CAM = {
    "sweep_parcels_apart": ((-1.30, -1.90, 1.65), (0.40, 0.05, 0.80)),
    "push_box_to_bin": ((-1.15, -2.10, 1.55), (0.45, -0.35, 0.75)),
    "nudge_mailer_to_bin": ((-1.15, -1.95, 1.55), (0.45, 0.15, 0.75)),
}

_HAND_PATTERNS = {
    "left": [
        "left_wrist_roll_rubber_hand",
        "left_wrist_roll_link",
        "left_rubber_hand",
    ],
    "right": [
        "right_wrist_roll_rubber_hand",
        "right_wrist_roll_link",
        "right_rubber_hand",
    ],
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


def _pose_tensor(xyz: tuple[float, float, float], device: torch.device) -> torch.Tensor:
    qx, qy, qz, qw = _yaw_xyzw(0.0)
    return torch.tensor([[xyz[0], xyz[1], xyz[2], qx, qy, qz, qw]], dtype=torch.float32, device=device)


def main() -> None:
    record_dir = Path(args_cli.record_dir) if args_cli.record_dir else ROOT / "demo" / "preview_sorting_station"
    record_dir.mkdir(parents=True, exist_ok=True)

    env_cfg = SortingStationEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env_cfg.episode_length_s = 120.0
    env = ManagerBasedRLEnv(cfg=env_cfg)
    env.reset()

    step_dt = float(env.step_dt)
    hold_start = max(1, int(round(args_cli.hold_start_s / step_dt)))
    task_steps = max(16, int(round(args_cli.task_s / step_dt)))
    hold_end = max(1, int(round(args_cli.hold_end_s / step_dt)))
    zero = torch.zeros((env.num_envs, 23), dtype=torch.float32, device=env.device)
    zero_vel = torch.zeros((env.num_envs, 6), dtype=torch.float32, device=env.device)

    robot = env.scene["robot"]
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
            ids, names = robot.find_bodies(f".*{side}.*wrist.*")
            if ids:
                idx = ids[0]
                if hasattr(idx, "item"):
                    idx = idx.item()
                hand_idx[side] = int(idx)
                print(f"  {side} hand fallback: {names[0]}  idx={hand_idx[side]}")
    if len(hand_idx) < 2:
        print(f"  body_names sample: {list(robot.body_names)[:12]} ... {list(robot.body_names)[-8:]}")
        raise RuntimeError(f"could not resolve U1 rubber-hand bodies: {hand_idx}")

    print("=" * 72)
    print("SimFoundry sorting station")
    print(f"  蓝桌 1.50 x 0.60 x 0.025  TABLE_TOP={_TABLE_TOP:.3f}")
    print("  包裹: pick_demo 真图立方体  纸箱 13×8×2.5cm  大袋 15×15×3cm")
    print("  reset: 4 张纸箱图 / 5 张袋图各抽 1 张")
    print("  机器人: G1 23DoF U1 橡胶假手")
    print("  主录像: D435i 头显  Kit 同步 streaming 头显面板")
    print("  任务: 假手物理碰撞推动包裹（无脚本传送）")
    print(f"  录像目录: {record_dir}")
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

    def _wrist_xyz(side: str) -> tuple[float, float, float]:
        idx = hand_idx[side]
        p = robot.data.body_pos_w[0, idx]
        if hasattr(p, "torch"):
            p = p.torch
        return (float(p[0]), float(p[1]), float(p[2]))

    def _sync_labels() -> None:
        """Stickers follow parcel pose (position + rotation), flush on the top face."""
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
        # Force a render so the pose lands before the next RGB read.
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
        except Exception as exc:  # noqa: BLE001 — camera/Warp glitches must not abort demo
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
    touches = {"box": 0, "mailer": 0}

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
        left = _hand_xyz("left")
        right = _hand_xyz("right")
        box = _xyz("parcel_box")
        mailer = _xyz("mailer")
        if _touching(right, box) or _touching(left, box):
            touches["box"] += 1
        if _touching(right, mailer) or _touching(left, mailer):
            touches["mailer"] += 1
        if log:
            rw = _wrist_xyz("right")
            dr = math.hypot(right[0] - box[0], right[1] - box[1])
            dl = math.hypot(left[0] - mailer[0], left[1] - mailer[1])
            jp = robot.data.joint_pos[0]
            if hasattr(jp, "torch"):
                jp = jp.torch
            names = list(robot.joint_names)
            re = float(jp[names.index("right_elbow_joint")]) if "right_elbow_joint" in names else float("nan")
            rsp = float(jp[names.index("right_shoulder_pitch_joint")]) if "right_shoulder_pitch_joint" in names else float("nan")
            print(
                f"    palm {right[0]:.2f},{right[1]:.2f},{right[2]:.2f}  "
                f"wrist_z={rw[2]:.2f} box_z={box[2]:.2f} dxy={dr:.3f} dz={right[2]-box[2]:+.3f}  "
                f"Lpalm_z={left[2]:.2f} mailer_y={mailer[1]:.2f} dxy={dl:.3f}  "
                f"R_sp={rsp:.2f} R_el={re:.2f}"
            )
        _record(obs)
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

    def _task(task_id: str, title: str, instruction: str) -> None:
        print("-" * 72)
        print(f"[{title}]  {instruction}")
        eye, look = _TASK_CAM.get(task_id, (_OVERVIEW_EYE, _OVERVIEW_LOOK))
        obs = None
        for i in range(task_steps):
            if not simulation_app.is_running():
                return
            act = torch.from_numpy(scripted_action(task_id, i, task_steps)).to(env.device)
            action = act.unsqueeze(0).repeat(env.num_envs, 1)
            obs = _tick(action, eye, look, log=(i % 30 == 0))
        _save_head_png(obs, task_id)

    # Seed once (random albedo), then let PhysX settle — never teleport during the task.
    demo_rng = np.random.default_rng(args_cli.photo_seed)
    reset_sorting_parcels(env, single_parcel=False, rng=demo_rng)
    chosen = getattr(env, "_sorting_parcel_photos", {}) or {}
    box_photo = Path(chosen["parcel_box"]).name if chosen.get("parcel_box") else "?"
    mailer_photo = Path(chosen["mailer"]).name if chosen.get("mailer") else "?"
    print(f"  抽中纸箱: {box_photo}")
    print(f"  抽中袋子: {mailer_photo}")
    print("=" * 72)
    print(f"可以开始录像  纸箱={box_photo}  袋子={mailer_photo}")
    print("=" * 72)
    (record_dir / "chosen_photos.json").write_text(
        json.dumps({"parcel_box": box_photo, "mailer": mailer_photo}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        _place("mailer_b", _MAILER_B_REST)
    except (KeyError, AttributeError):
        pass
    _sync_labels()
    _hold(hold_start, _OVERVIEW_EYE, _OVERVIEW_LOOK, "全景（物理静置）")
    settle_obs = _tick(zero, _OVERVIEW_EYE, _OVERVIEW_LOOK)
    _save_head_png(settle_obs, "reset_overview")
    # Re-seat after settle; omit rng so albedo stays the same.
    reset_sorting_parcels(
        env,
        single_parcel=False,
        box_xyz=_BOX_REST,
        mailer_xyz=_MAILER_REST,
    )
    try:
        _place("mailer_b", _MAILER_B_REST)
    except (KeyError, AttributeError):
        pass
    _sync_labels()
    _task("sweep_parcels_apart", "拨开", "假手下压接触台面后，双手把纸盒/黑袋向外拨开。")
    _task("push_box_to_bin", "推纸盒", "右手假手碰到木浆纸盒后，把它推向周转箱。")
    _task("nudge_mailer_to_bin", "拨包裹", "左手假手碰到黑色包裹后，把它拨向周转箱。")
    _hold(hold_end, _OVERVIEW_EYE, _OVERVIEW_LOOK, "收尾全景")

    print(f"near-touch frames  box={touches['box']}  mailer={touches['mailer']}")
    print(f"final box={_xyz('parcel_box')}  mailer={_xyz('mailer')}")
    try:
        print(f"final mailer_b={_xyz('mailer_b')}")
    except (KeyError, AttributeError):
        pass

    if head_writer is not None:
        head_writer.release()
    if view_writer is not None:
        view_writer.release()
    env.close()
    simulation_app.close()
    print("done.")


if __name__ == "__main__":
    main()
