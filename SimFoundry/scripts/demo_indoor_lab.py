#!/usr/bin/env python3
"""Indoor-lab tour: G1 23 walks between zones and performs visible stump tasks.

Records two mp4s under demo/preview_indoor_lab/:
  - head_d435i_0000.mp4     robot D435i (headset)
  - kit_viewport_0000.mp4   third-person view matching the Kit 3D camera

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/demo_indoor_lab.py \\
      --num_envs 1 --device cuda --viz kit
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="SimFoundry indoor-lab walking tour with dual video capture.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--hold-start-s", type=float, default=4.0, help="Overview hold before the tour.")
parser.add_argument("--task-s", type=float, default=5.0, help="Seconds spent performing each task.")
parser.add_argument("--hold-end-s", type=float, default=4.0, help="Closing overview hold.")
parser.add_argument("--walk-speed", type=float, default=0.48, help="Root translation speed while walking [m/s].")
parser.add_argument(
    "--realtime",
    action=argparse.BooleanOptionalAction,
    default=True,
)
parser.add_argument(
    "--record",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Write headset + 3D viewer mp4s (default on).",
)
parser.add_argument(
    "--record-dir",
    type=str,
    default="",
    help="Output directory for mp4s. Default: SimFoundry/demo/preview_indoor_lab",
)
parser.add_argument("--save-preview", action="store_true", help="Write one RGB frame per task under the record dir.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import numpy as np
import torch

from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.data.scripted import scripted_action, walking_gait
from simfoundry.isaac_envs.indoor_lab_env_cfg import IndoorLabEnvCfg

_ROOT_Z = 0.74

# Rest / pressed / swept poses for kinematic props (world frame).
_DOOR_REST = (3.38, 0.18, 1.025, 0.436)  # x, y, z, yaw
_DOOR_OPEN = (3.52, 0.62, 1.025, 1.65)
_BUTTON_REST = (3.28, -0.82, 0.98, 0.0)
_BUTTON_PRESSED = (3.28, -0.905, 0.98, 0.0)
_CUP_REST = (6.92, 0.38, 0.835, 0.0)
_CUP_PUSHED = (6.93, 0.64, 0.835, 0.0)
_BOX_REST = (4.85, 1.68, 0.79, 0.0)
_BOX_NUDGED = (4.52, 1.68, 0.79, 0.0)
_SWITCH_REST = (5.45, 1.62, 0.77, 0.0)
_SWITCH_PRESSED = (5.45, 1.62, 0.735, 0.0)

_OVERVIEW_EYE = (-1.8, -8.0, 4.6)
_OVERVIEW_LOOK = (4.2, 0.15, 0.85)

# Task close-ups: (eye, lookat)
_TASK_CAM = {
    "wave_hello": ((1.15, 1.55, 1.65), (-0.10, 0.85, 0.95)),
    "push_door": ((1.70, -0.55, 1.55), (3.25, 0.12, 1.05)),
    "press_wall_button": ((2.15, -0.18, 1.45), (3.18, -0.72, 1.00)),
    "push_cup_to_bowl": ((5.35, -1.55, 1.65), (6.80, 0.50, 0.92)),
    "nudge_bottle_left": ((3.85, 0.35, 1.65), (5.05, 1.58, 0.90)),
    "press_table_switch": ((3.95, 0.30, 1.65), (5.30, 1.55, 0.88)),
}


def _yaw_xyzw(yaw: float) -> tuple[float, float, float, float]:
    return (0.0, 0.0, math.sin(yaw * 0.5), math.cos(yaw * 0.5))


def _wrap_pi(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


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
    else:
        raise ValueError(f"unexpected frame shape {arr.shape}")
    if arr.dtype != np.uint8:
        arr = arr.astype(np.float32)
        if arr.max() <= 1.5:
            arr = arr * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def _lerp3(a: tuple[float, ...], b: tuple[float, ...], t: float) -> tuple[float, float, float]:
    t = min(1.0, max(0.0, t))
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _follow_cam(xy_yaw: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    x, y, yaw = xy_yaw
    fx, fy = math.cos(yaw), math.sin(yaw)
    # Stay inside the corridor (y ≈ ±0.86) and the inner room (y ≈ ±2.0).
    back, side, height = 1.85, 0.28, 1.72
    eye = (x - back * fx + side * fy, y - back * fy - side * fx, height)
    look = (x + 0.70 * fx, y + 0.70 * fy, 0.88)
    return eye, look


def _root_pose_tensor(xy_yaw: tuple[float, float, float], z: float, device: torch.device) -> torch.Tensor:
    x, y, yaw = xy_yaw
    qx, qy, qz, qw = _yaw_xyzw(yaw)
    return torch.tensor([[x, y, z, qx, qy, qz, qw]], dtype=torch.float32, device=device)


def _prop_pose_tensor(xyz_yaw: tuple[float, float, float, float], device: torch.device) -> torch.Tensor:
    x, y, z, yaw = xyz_yaw
    qx, qy, qz, qw = _yaw_xyzw(yaw)
    return torch.tensor([[x, y, z, qx, qy, qz, qw]], dtype=torch.float32, device=device)


def _lerp_prop(
    rest: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
    t: float,
) -> tuple[float, float, float, float]:
    t = min(1.0, max(0.0, t))
    yaw = rest[3] + _wrap_pi(target[3] - rest[3]) * t
    return (rest[0] + (target[0] - rest[0]) * t, rest[1] + (target[1] - rest[1]) * t, rest[2] + (target[2] - rest[2]) * t, yaw)


def main() -> None:
    record_dir = Path(args_cli.record_dir) if args_cli.record_dir else ROOT / "demo" / "preview_indoor_lab"
    record_dir.mkdir(parents=True, exist_ok=True)

    env_cfg = IndoorLabEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env_cfg.episode_length_s = 600.0
    env_cfg.events.randomize_cup.params["pose_range"] = {"x": (0.0, 0.0), "y": (0.0, 0.0)}
    # Scripted kinematic walk: free pelvis, no gravity so the gait stays upright.
    env_cfg.scene.robot.spawn.articulation_props.fix_root_link = False
    env_cfg.scene.robot.spawn.rigid_props.disable_gravity = True
    env_cfg.terminations.fallen.params["minimum_height"] = -1.0

    env = ManagerBasedRLEnv(cfg=env_cfg)
    env.reset()

    step_dt = float(env.step_dt)
    hold_start_steps = max(1, int(round(args_cli.hold_start_s / step_dt)))
    task_steps = max(12, int(round(args_cli.task_s / step_dt)))
    hold_end_steps = max(1, int(round(args_cli.hold_end_s / step_dt)))
    cam_blend_steps = max(8, int(round(0.7 / step_dt)))

    zero = torch.zeros((env.num_envs, 23), dtype=torch.float32, device=env.device)
    zero_vel = torch.zeros((env.num_envs, 6), device=env.device, dtype=torch.float32)
    pose = [0.0, 0.0, 0.0]  # x, y, yaw
    global_step = 0
    gait_clock = 0.0
    cam_eye = _OVERVIEW_EYE
    cam_look = _OVERVIEW_LOOK

    print("=" * 72)
    print("SimFoundry indoor lab  WALKING TOUR")
    print(f"  录像目录     : {record_dir}")
    print(f"  头显 mp4     : head_d435i.mp4")
    print(f"  3D视角 mp4   : kit_viewport.mp4")
    print(f"  Kit 头显面板 : streaming_view ← D435i")
    print(f"  行走         : {args_cli.walk_speed:.2f} m/s  脚本步态（非传送）")
    print("=" * 72)

    head_path = record_dir / "head_d435i.mp4"
    view_path = record_dir / "kit_viewport.mp4"
    head_writer = None
    view_writer = None
    if args_cli.record:
        import cv2

        fps = max(1, int(round(1.0 / step_dt)))
        head_writer = cv2.VideoWriter(str(head_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (640, 480))
        view_writer = cv2.VideoWriter(str(view_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (960, 540))
        if not head_writer.isOpened() or not view_writer.isOpened():
            raise RuntimeError(f"failed to open mp4 writers under {record_dir}")

    def _release_writers() -> None:
        nonlocal head_writer, view_writer
        if head_writer is not None:
            head_writer.release()
            head_writer = None
        if view_writer is not None:
            view_writer.release()
            view_writer = None

    import atexit

    atexit.register(_release_writers)

    def _write_frame(writer, frame: torch.Tensor | np.ndarray, size: tuple[int, int]) -> None:
        if writer is None:
            return
        import cv2

        rgb = _to_uint8_hwc(frame)
        h, w = size[1], size[0]
        if rgb.shape[0] != h or rgb.shape[1] != w:
            rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
        writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    def _kit_rgb() -> np.ndarray | None:
        for viz in getattr(env.sim, "visualizers", []):
            if getattr(getattr(viz, "cfg", None), "visualizer_type", None) != "kit":
                continue
            if not hasattr(viz, "render_rgb_array"):
                continue
            frame = viz.render_rgb_array()
            if frame is None:
                return None
            return np.asarray(frame)
        return None

    def _record_step(obs) -> None:
        if not args_cli.record or obs is None:
            return
        _write_frame(head_writer, obs["rgb"][0], (640, 480))
        kit = _kit_rgb()
        if kit is not None and float(np.mean(kit)) > 4.0:
            _write_frame(view_writer, kit, (960, 540))
            return
        cam = env.scene.sensors.get("viewer_cam")
        if cam is None:
            return
        output = getattr(getattr(cam, "data", None), "output", None)
        if output is None or "rgb" not in output:
            return
        rgb = output["rgb"]
        if hasattr(rgb, "torch"):
            rgb = rgb.torch
        _write_frame(view_writer, rgb[0], (960, 540))

    def _pace(t0: float) -> None:
        if not args_cli.realtime:
            return
        delay = t0 + step_dt - time.perf_counter()
        if delay > 0:
            time.sleep(delay)

    def _place_robot(xy_yaw: tuple[float, float, float], z: float | None = None) -> None:
        robot = env.scene["robot"]
        robot.write_root_pose_to_sim_index(root_pose=_root_pose_tensor(xy_yaw, z if z is not None else _ROOT_Z, env.device))
        if hasattr(robot, "write_root_velocity_to_sim_index"):
            robot.write_root_velocity_to_sim_index(root_velocity=zero_vel)

    def _place_prop(name: str, xyz_yaw: tuple[float, float, float, float]) -> None:
        asset = env.scene[name]
        asset.write_root_pose_to_sim_index(root_pose=_prop_pose_tensor(xyz_yaw, env.device))
        if hasattr(asset, "write_root_velocity_to_sim_index"):
            asset.write_root_velocity_to_sim_index(root_velocity=zero_vel)

    def _set_views(eye: tuple[float, float, float], look: tuple[float, float, float]) -> None:
        env.sim.set_camera_view(eye, look)
        cam = env.scene.sensors.get("viewer_cam")
        if cam is None:
            return
        eyes = torch.tensor([eye], dtype=torch.float32, device=env.device).repeat(env.num_envs, 1)
        targets = torch.tensor([look], dtype=torch.float32, device=env.device).repeat(env.num_envs, 1)
        cam.set_world_poses_from_view(eyes, targets)

    def _tick(action: torch.Tensor, xy_yaw: tuple[float, float, float], eye, look, z: float | None = None):
        nonlocal global_step
        if not simulation_app.is_running():
            return None
        t0 = time.perf_counter()
        _place_robot(xy_yaw, z)
        _set_views(eye, look)
        obs, *_ = env.step(action)
        _place_robot(xy_yaw, z)
        _record_step(obs)
        _pace(t0)
        global_step += 1
        return obs

    def _countdown(tag: str, remaining: float) -> None:
        if int(remaining * 10) % 10 == 0 or remaining < 0.15:
            print(f"  {tag}… {remaining:4.1f}s left", flush=True)

    def _blend_cam(src_eye, src_look, dst_eye, dst_look, xy_yaw) -> None:
        nonlocal cam_eye, cam_look
        for i in range(cam_blend_steps):
            if not simulation_app.is_running():
                return
            t = _ease((i + 1) / cam_blend_steps)
            eye = _lerp3(src_eye, dst_eye, t)
            look = _lerp3(src_look, dst_look, t)
            _tick(zero, xy_yaw, eye, look)
        cam_eye, cam_look = dst_eye, dst_look

    def turn_to(target_yaw: float) -> None:
        nonlocal pose, gait_clock, cam_eye, cam_look
        x, y, yaw = pose
        delta = _wrap_pi(target_yaw - yaw)
        if abs(delta) < 0.06:
            pose[2] = target_yaw
            return
        rate = 1.7
        n = max(1, int(abs(delta) / rate / step_dt))
        for i in range(n):
            if not simulation_app.is_running():
                return
            t = (i + 1) / n
            yaw_i = yaw + delta * t
            xy_yaw = (x, y, yaw_i)
            z = _ROOT_Z + 0.012 * abs(math.sin(2.0 * math.pi * 1.55 * gait_clock))
            act_np = walking_gait(gait_clock, amplitude=0.40)
            action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
            eye, look = _follow_cam(xy_yaw)
            _tick(action, xy_yaw, eye, look, z=z)
            gait_clock += step_dt
            cam_eye, cam_look = eye, look
        pose = [x, y, target_yaw]

    def walk_to(end_xy_yaw: tuple[float, float, float], label: str) -> None:
        nonlocal pose, gait_clock, cam_eye, cam_look
        x0, y0, yaw0 = pose
        x1, y1, yaw1 = end_xy_yaw
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        heading = math.atan2(dy, dx) if dist > 0.05 else yaw1
        print(f"[walk] {label}  {dist:.2f} m")
        turn_to(heading)
        x0, y0, _ = pose
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        n = max(1, int(dist / max(args_cli.walk_speed, 0.05) / step_dt))
        for i in range(n):
            if not simulation_app.is_running():
                return
            t = (i + 1) / n
            xy_yaw = (x0 + dx * t, y0 + dy * t, heading)
            z = _ROOT_Z + 0.018 * abs(math.sin(2.0 * math.pi * 1.55 * gait_clock))
            act_np = walking_gait(gait_clock, amplitude=1.0)
            action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
            eye, look = _follow_cam(xy_yaw)
            _tick(action, xy_yaw, eye, look, z=z)
            gait_clock += step_dt
            cam_eye, cam_look = eye, look
        pose = [x1, y1, heading]
        turn_to(yaw1)

    def do_task(task_id: str, title: str, instruction: str, animate: str | None = None) -> None:
        nonlocal cam_eye, cam_look, pose
        print("-" * 72)
        print(f"[{title}]")
        print(f"  指令: {instruction}")
        xy_yaw = (pose[0], pose[1], pose[2])
        follow_eye, follow_look = _follow_cam(xy_yaw)
        close_eye, close_look = _TASK_CAM.get(task_id, (follow_eye, follow_look))
        _blend_cam(cam_eye, cam_look, close_eye, close_look, xy_yaw)

        for i in range(task_steps):
            if not simulation_app.is_running():
                return
            remaining = (task_steps - i) * step_dt
            if i % max(1, int(round(1.0 / step_dt))) == 0:
                _countdown(task_id, remaining)
            act_np = scripted_action(task_id, i, task_steps)
            action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
            phase = i / max(task_steps - 1, 1)

            if animate == "door":
                t = _ease(min(1.0, max(0.0, (phase - 0.20) / 0.55)))
                _place_prop("door", _lerp_prop(_DOOR_REST, _DOOR_OPEN, t))
            elif animate == "button":
                t = _ease(min(1.0, max(0.0, (phase - 0.38) / 0.22)))
                _place_prop("wall_button", _lerp_prop(_BUTTON_REST, _BUTTON_PRESSED, t))
            elif animate == "cup":
                t = _ease(min(1.0, max(0.0, (phase - 0.42) / 0.45)))
                _place_prop("cup", _lerp_prop(_CUP_REST, _CUP_PUSHED, t))
            elif animate == "box":
                t = _ease(min(1.0, max(0.0, (phase - 0.40) / 0.45)))
                _place_prop("lab_box", _lerp_prop(_BOX_REST, _BOX_NUDGED, t))
            elif animate == "switch":
                t = _ease(min(1.0, max(0.0, (phase - 0.42) / 0.22)))
                _place_prop("table_switch", _lerp_prop(_SWITCH_REST, _SWITCH_PRESSED, t))

            obs = _tick(action, xy_yaw, close_eye, close_look)
            # Re-pin kinematic/demo props after physics so the motion stays visible.
            if animate == "door":
                _place_prop("door", _lerp_prop(_DOOR_REST, _DOOR_OPEN, _ease(min(1.0, max(0.0, (phase - 0.20) / 0.55)))))
            elif animate == "button":
                _place_prop("wall_button", _lerp_prop(_BUTTON_REST, _BUTTON_PRESSED, _ease(min(1.0, max(0.0, (phase - 0.38) / 0.22)))))
            elif animate == "cup":
                _place_prop("cup", _lerp_prop(_CUP_REST, _CUP_PUSHED, _ease(min(1.0, max(0.0, (phase - 0.42) / 0.45)))))
            elif animate == "box":
                _place_prop("lab_box", _lerp_prop(_BOX_REST, _BOX_NUDGED, _ease(min(1.0, max(0.0, (phase - 0.40) / 0.45)))))
            elif animate == "switch":
                _place_prop("table_switch", _lerp_prop(_SWITCH_REST, _SWITCH_PRESSED, _ease(min(1.0, max(0.0, (phase - 0.42) / 0.22)))))
            if args_cli.save_preview and obs is not None and i == task_steps // 2:
                import cv2

                rgb = _to_uint8_hwc(obs["rgb"][0])
                path = record_dir / f"tour_{task_id}.png"
                cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                print(f"saved {path}")

        # Keep animated props at their final pose.
        if animate == "door":
            _place_prop("door", _DOOR_OPEN)
        elif animate == "button":
            _place_prop("wall_button", _BUTTON_PRESSED)
        elif animate == "cup":
            _place_prop("cup", _CUP_PUSHED)
        elif animate == "box":
            _place_prop("lab_box", _BOX_NUDGED)
        elif animate == "switch":
            _place_prop("table_switch", _SWITCH_PRESSED)

        _blend_cam(close_eye, close_look, follow_eye, follow_look, xy_yaw)

    def hold_overview(n_steps: int, tag: str) -> None:
        xy_yaw = (pose[0], pose[1], pose[2])
        for i in range(n_steps):
            if not simulation_app.is_running():
                return
            remaining = (n_steps - i) * step_dt
            if i % max(1, int(round(1.0 / step_dt))) == 0:
                _countdown(tag, remaining)
            _tick(zero, xy_yaw, cam_eye, cam_look)

    # --- tour ---
    _place_prop("door", _DOOR_REST)
    _place_prop("wall_button", _BUTTON_REST)
    _place_prop("table_switch", _SWITCH_REST)

    print(f"[phase] hold_start 全景 ({args_cli.hold_start_s:.1f}s)")
    cam_eye, cam_look = _OVERVIEW_EYE, _OVERVIEW_LOOK
    _set_views(cam_eye, cam_look)
    _place_robot((pose[0], pose[1], pose[2]))
    hold_overview(hold_start_steps, "hold_start")

    # Drop from overview to a follow cam before walking.
    start_follow = _follow_cam((pose[0], pose[1], pose[2]))
    _blend_cam(cam_eye, cam_look, start_follow[0], start_follow[1], (pose[0], pose[1], pose[2]))

    walk_to((0.12, 0.50, 1.40), "对人")
    do_task("wave_hello", "1/7  对人示意", "对着前面挥手。")

    walk_to((1.15, 0.0, 0.0), "走廊黄标记")
    print("[3/7  走廊] 已走到地上的标记处")

    walk_to((2.40, 0.02, 0.0), "门前")
    do_task("push_door", "4/7  轻门", "把门推开。", animate="door")

    walk_to((2.82, -0.34, -0.72), "墙面按钮")
    do_task("press_wall_button", "5/7  墙面按钮", "按下墙上的按钮。", animate="button")

    walk_to((3.00, 0.0, 0.0), "回到门洞中线")
    walk_to((4.15, 0.0, 0.0), "进门")
    walk_to((6.26, 0.40, 0.0), "厨房操作台")
    do_task("push_cup_to_bowl", "6/7  厨房操作台", "把杯子推向碗。", animate="cup")

    walk_to((4.95, 1.10, 1.57), "实验矮桌")
    do_task("nudge_bottle_left", "7/7  实验矮桌", "把盒子向左拨开。", animate="box")

    walk_to((5.38, 1.10, 1.57), "桌面开关")
    do_task("press_table_switch", "桌面开关", "按下桌上的开关。", animate="switch")

    print(f"[phase] hold_end 全景 ({args_cli.hold_end_s:.1f}s)")
    xy_yaw = (pose[0], pose[1], pose[2])
    _blend_cam(cam_eye, cam_look, _OVERVIEW_EYE, _OVERVIEW_LOOK, xy_yaw)
    hold_overview(hold_end_steps, "hold_end")

    env.close()
    _release_writers()
    print(f"demo_indoor_lab tour finished after {global_step} env steps.")
    if args_cli.record:
        print(f"videos written under {record_dir}")
        for path in (head_path, view_path):
            if path.is_file():
                print(f"  {path}  ({path.stat().st_size / 1e6:.1f} MB)")
            else:
                print(f"  missing {path}")


if __name__ == "__main__":
    main()
    simulation_app.close()
