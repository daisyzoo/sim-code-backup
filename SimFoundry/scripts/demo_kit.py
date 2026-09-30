#!/usr/bin/env python3
"""Kit-viewport demo — default: ≤10s silky pick-cup.

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/demo_kit.py \\
      --num_envs 1 --device cuda --viz kit
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="SimFoundry Kit demo (pick-cup ≤10s by default).")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--task-id", default="pick_cup")
parser.add_argument(
    "--duration-s",
    type=float,
    default=9.0,
    help="Approximate wall-clock length when --realtime is on (default 9s, under 10s).",
)
parser.add_argument("--hold-start-s", type=float, default=0.8, help="Brief settle before motion.")
parser.add_argument("--hold-end-s", type=float, default=1.0, help="Hold lifted cup at the end.")
parser.add_argument(
    "--realtime",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Pace env.step() to wall clock (default: on).",
)
parser.add_argument("--loops", type=int, default=1, help="Repeat the motion this many times.")
parser.add_argument("--save-preview", action="store_true", help="Write RGB frames under demo/preview_kit/")
parser.add_argument(
    "--attach-cup",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Kinematically attach cup to right wrist after grasp phase (reliable pick demo).",
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import numpy as np
import torch

from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.data.scripted import scripted_action
from simfoundry.isaac_envs.kitchen_env_cfg import KitchenCounterEnvCfg
from simfoundry.robots import local_inspire_usd
from simfoundry.scene_package import filter_tasks, load_named_scene

# Palm offset relative to wrist yaw / rubber-hand body (meters, body frame approx world-aligned).
_CUP_PALM_OFFSET = torch.tensor([0.12, -0.02, 0.02], dtype=torch.float32)


def _to_uint8_hwc(frame: torch.Tensor) -> np.ndarray:
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


def _zeros(num_envs: int, device: str | torch.device) -> torch.Tensor:
    return torch.zeros((num_envs, 23), dtype=torch.float32, device=device)


def _find_grasp_body(robot) -> int:
    """Prefer palm / finger stubs present on Nucleus g1.usd."""
    names = list(robot.body_names)
    for pattern in (
        "right_palm_link",
        "right_zero_link",
        "right_one_link",
        "right_elbow_roll_link",
        "right_elbow_pitch_link",
    ):
        if pattern in names:
            body_id = names.index(pattern)
            print(f"  grasp body : {pattern} (id={body_id})")
            return body_id
    raise RuntimeError(f"no right-hand / wrist body found; have {names}")


def _attach_cup_to_body(env: ManagerBasedRLEnv, body_id: int) -> None:
    robot = env.scene["robot"]
    cup = env.scene["cup"]
    pos = robot.data.body_pos_w[:, body_id].clone()
    quat = robot.data.body_quat_w[:, body_id].clone()
    offset = _CUP_PALM_OFFSET.to(device=pos.device, dtype=pos.dtype).unsqueeze(0)
    # Rotate offset by body quaternion (w,x,y,z).
    w, x, y, z = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
    ox, oy, oz = offset[:, 0], offset[:, 1], offset[:, 2]
    # q * v * q^{-1}
    tx = 2.0 * (y * oz - z * oy)
    ty = 2.0 * (z * ox - x * oz)
    tz = 2.0 * (x * oy - y * ox)
    rx = ox + w * tx + (y * tz - z * ty)
    ry = oy + w * ty + (z * tx - x * tz)
    rz = oz + w * tz + (x * ty - y * tx)
    root_pose = torch.cat([pos + torch.stack([rx, ry, rz], dim=-1), quat], dim=-1)
    cup.write_root_pose_to_sim_index(root_pose=root_pose)
    zero_vel = torch.zeros((env.num_envs, 6), device=pos.device, dtype=pos.dtype)
    if hasattr(cup, "write_root_velocity_to_sim_index"):
        cup.write_root_velocity_to_sim_index(root_velocity=zero_vel)
    elif hasattr(cup, "write_root_com_velocity_to_sim_index"):
        cup.write_root_com_velocity_to_sim_index(root_velocity=zero_vel)


def main() -> None:
    package = load_named_scene("kitchen_counter_placeholder")
    tasks = {t.task_id: t for t in filter_tasks(package, "stump")}
    if args_cli.task_id not in tasks:
        raise SystemExit(f"unknown stump task {args_cli.task_id}; have {sorted(tasks)}")
    task = tasks[args_cli.task_id]

    env_cfg = KitchenCounterEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env_cfg.episode_length_s = max(args_cli.duration_s + 10.0, 30.0)
    # Cup XY jitter disabled for scripted pick/reach demos (re-enable for domain rand).
    env_cfg.events.randomize_cup.params["pose_range"] = {"x": (0.0, 0.0), "y": (0.0, 0.0)}
    env = ManagerBasedRLEnv(cfg=env_cfg)
    env.reset()

    step_dt = float(env.step_dt)
    hold_start_steps = max(1, int(round(args_cli.hold_start_s / step_dt)))
    hold_end_steps = max(1, int(round(args_cli.hold_end_s / step_dt)))
    motion_budget_s = max(
        3.0,
        args_cli.duration_s - args_cli.hold_start_s - args_cli.hold_end_s,
    )
    motion_steps_total = max(40, int(round(motion_budget_s / step_dt)))
    motion_steps = max(24, motion_steps_total // max(args_cli.loops, 1))

    preview_dir = ROOT / "demo" / "preview_kit"
    if args_cli.save_preview:
        preview_dir.mkdir(parents=True, exist_ok=True)

    grasp_body = None
    if args_cli.attach_cup and task.task_id == "pick_cup":
        grasp_body = _find_grasp_body(env.scene["robot"])

    inspire = local_inspire_usd()
    print("=" * 72)
    print("SimFoundry Kit demo")
    print(f"  scene      : {package.scene_id}")
    print(f"  task       : {task.task_id}")
    print(f"  instruction: {task.instruction}")
    print(f"  objects    : YCB mug/bowl/bottle USD + plate primitive")
    print(f"  g1_inspire : {inspire if inspire else 'not converted yet (run convert_g1_urdf.py)'}")
    print(f"  step_dt    : {step_dt:.4f}s")
    print(f"  hold_start : {args_cli.hold_start_s:.1f}s")
    print(f"  motion     : ~{motion_budget_s:.1f}s  ({motion_steps} steps × {args_cli.loops})")
    print(f"  hold_end   : {args_cli.hold_end_s:.1f}s")
    print(f"  realtime   : {args_cli.realtime}")
    print(f"  attach_cup : {bool(grasp_body is not None)}")
    print("=" * 72)

    total_steps_planned = hold_start_steps + motion_steps * args_cli.loops + hold_end_steps
    preview_marks = {0, total_steps_planned // 2, total_steps_planned - 1}

    def _pace(t0: float) -> None:
        if not args_cli.realtime:
            return
        target = t0 + step_dt
        delay = target - time.perf_counter()
        if delay > 0:
            time.sleep(delay)

    def _maybe_attach(motion_step: int, horizon: int) -> None:
        if grasp_body is None:
            return
        phase = motion_step / max(horizon - 1, 1)
        if phase >= 0.48:
            _attach_cup_to_body(env, grasp_body)

    def _step(action: torch.Tensor, global_step: int, motion_step: int | None = None) -> int:
        if not simulation_app.is_running():
            return global_step
        t0 = time.perf_counter()
        if motion_step is not None:
            _maybe_attach(motion_step, motion_steps)
        obs, *_ = env.step(action)
        if motion_step is not None:
            _maybe_attach(motion_step, motion_steps)
        _pace(t0)
        if args_cli.save_preview and global_step in preview_marks:
            import cv2

            rgb = _to_uint8_hwc(obs["rgb"][0])
            path = preview_dir / f"kit_frame_{global_step:04d}.png"
            cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            print(f"saved {path}")
        return global_step + 1

    global_step = 0
    zero = _zeros(env.num_envs, env.device)

    print(f"[phase] hold_start ({args_cli.hold_start_s:.1f}s)")
    for _ in range(hold_start_steps):
        if not simulation_app.is_running():
            break
        global_step = _step(zero, global_step)

    for loop_i in range(args_cli.loops):
        print(f"[phase] motion loop {loop_i + 1}/{args_cli.loops} ({motion_steps} steps)")
        for step in range(motion_steps):
            if not simulation_app.is_running():
                break
            act_np = scripted_action(task.task_id, step, motion_steps)
            action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
            global_step = _step(action, global_step, motion_step=step)

    print(f"[phase] hold_end ({args_cli.hold_end_s:.1f}s)")
    final_np = scripted_action(task.task_id, motion_steps - 1, motion_steps)
    final = torch.from_numpy(final_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
    for _ in range(hold_end_steps):
        if not simulation_app.is_running():
            break
        if grasp_body is not None:
            _attach_cup_to_body(env, grasp_body)
        global_step = _step(final, global_step, motion_step=motion_steps - 1)

    env.close()
    print(f"demo_kit finished after {global_step} env steps.")


if __name__ == "__main__":
    main()
    simulation_app.close()
