#!/usr/bin/env python3
"""Collect scripted stump trajectories for VLA / WAM.

Usage (from IsaacLab, Newton headless, 1 env):

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/collect_seed.py \\
        --scene-id sorting_station_g1_23 \\
        --task-id push_box_to_bin --num-episodes 200 --unitree --quality-gate \\
        --out-dir ../SimFoundry/datasets/sorting_station_g1_23_0831 \\
        --unitree-out ../SimFoundry/datasets/sorting_station_g1_23_unitree_0831

Sorting stump tasks use **one task per dataset tree** (see ``simfoundry/data/dataset_layout.py``):
  push_box_to_bin      → datasets/sorting_station_g1_23_0831
  nudge_mailer_to_bin  → datasets/sorting_station_g1_23_mailer_0831
  sweep_parcels_apart  → datasets/sorting_station_g1_23_sweep_0831
Omit ``--out-dir`` for sorting tasks to pick these defaults automatically.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.embodiment import REAL_TELEOP_FPS

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Collect SimFoundry seed trajectories.")
parser.add_argument("--scene-id", default="kitchen_counter_placeholder")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--num-episodes", type=int, default=4)
parser.add_argument("--steps", type=int, default=120, help="Horizon (ignored for sorting + --quality-gate; uses ~195± jitter).")
parser.add_argument("--task-id", default="push_cup_to_bowl")
parser.add_argument(
    "--task-mix",
    default="",
    help="Sorting only: comma list task:count, e.g. push_box_to_bin:12,nudge_mailer_to_bin:12,wait_no_package:8",
)
parser.add_argument("--requires-ee", default="stump")
parser.add_argument("--out-dir", default="")
parser.add_argument(
    "--unitree",
    action="store_true",
    help="Also write Unitree episode_*/data.json beside npz (pick_cup_soring_0824 layout).",
)
parser.add_argument("--unitree-out", default="", help="Unitree task dir (default: <out-dir>_unitree).")
parser.add_argument("--unitree-fps", type=float, default=REAL_TELEOP_FPS)
parser.add_argument(
    "--quality-gate",
    action="store_true",
    help="Sorting station only: save episode only if no penetration, hand contact, push out of frame.",
)
parser.add_argument(
    "--max-attempts",
    type=int,
    default=40,
    help="Max rollouts per requested episode when --quality-gate is set.",
)
parser.add_argument(
    "--wipe",
    action="store_true",
    help="Delete existing npz/unitree/lerobot outputs for this scene before collecting.",
)
parser.add_argument(
    "--push-assist",
    action="store_true",
    help="Kinematically slide parcels after palm latch. Off by default so demos are physically replayable.",
)
parser.add_argument(
    "--sorting-expert",
    choices=("contact", "cartesian", "idle"),
    default="contact",
    help="Physics-only sorting expert. Cartesian uses Jacobian palm tracking; idle is a diagnostic zero-action baseline.",
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import numpy as np
import torch

from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.data.schema import TrajectoryEpisode, save_episode
from simfoundry.data.scripted import scripted_action
from simfoundry.data.prompts import VLA_SORTING_UNIFIED_PROMPT
from simfoundry.data.sorting_quality import (
    MAX_PARCEL_START_ABS_Y,
    MIN_PARCEL_START_X,
    capture_step,
    evaluate_episode,
    palm_xyz,
    parcel_xyz,
    resolve_hand_indices,
    sample_sorting_horizon,
    sample_wait_horizon,
    wrist_xyz,
)
from simfoundry.data.dataset_layout import SORTING_SCENE_ID, sorting_dataset_dirs
from simfoundry.data.sorting_push_assist import (
    ContactSweepState,
    PushAssistState,
    correct_palm_height,
    follow_active_arm_push,
    maybe_assist_push,
    palm_xyz,
    plan_palm_push,
    press_and_sweep_palm,
)
from simfoundry.data.sorting_cartesian_expert import CartesianSweepState, cartesian_sweep_palm
from simfoundry.data.unitree_json import export_episode_unitree_json
from simfoundry.calibration.sorting_station import _write_pose, reset_sorting_parcels
from simfoundry.embodiment import D435I_INTRINSICS
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.scene_bridge.labels import sync_shipping_labels
from simfoundry.robots.g1_assets import clip_sorting_action_offset, u1_sorting_default_qpos_np
from simfoundry.embodiment import G1_23DOF_JOINT_NAMES
from simfoundry.scene_package import filter_tasks, load_named_scene

_SORTING_SCENE = SORTING_SCENE_ID
_SORTING_SETTLE_STEPS = 30
_SORTING_CAMERA_WARMUP = 12
_SORTING_ACTION_NOISE = 0.0
_SORTING_DEFAULT_Q = u1_sorting_default_qpos_np()
_MIN_RGB_MEAN = 0.12
_TORSO_I = G1_23DOF_JOINT_NAMES.index("torso_joint")


def _to_uint8_nchw(frame: torch.Tensor) -> np.ndarray:
    """Convert one camera frame to uint8 CHW RGB 480x640."""
    x = frame.detach().cpu()
    if x.ndim == 3 and x.shape[0] in (3, 4):
        x = x[:3]
    elif x.ndim == 3 and x.shape[-1] in (3, 4):
        x = x[..., :3].permute(2, 0, 1)
    else:
        raise ValueError(f"unexpected rgb frame shape {tuple(x.shape)}")
    if x.dtype == torch.uint8:
        out = x.numpy()
    else:
        arr = x.float().numpy()
        if arr.max() <= 1.5:
            arr = arr * 255.0
        out = np.clip(arr, 0, 255).astype(np.uint8)
    if out.shape[1] != D435I_INTRINSICS.height or out.shape[2] != D435I_INTRINSICS.width:
        raise ValueError(f"rgb spatial size {out.shape[1:]} != 480x640")
    return out


def _wipe_sorting_datasets(out_dir: Path, unitree_dir: Path) -> None:
    """Delete only the explicit output dirs for this run (never sibling datasets)."""
    for path in (out_dir, unitree_dir):
        if path.exists():
            shutil.rmtree(path)
            print(f"wipe: removed {path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    unitree_dir.mkdir(parents=True, exist_ok=True)


def _run_sorting_rollout(
    env,
    *,
    task,
    spec,
    package,
    task_id: str,
    horizon: int,
    phase_bias: float,
    ep_rng: np.random.Generator,
    hand_idx: dict,
    robot,
    default_q: np.ndarray,
    dof: int,
    zero_action: torch.Tensor,
    instruction: str,
    use_assist: bool,
    sorting_expert: str,
) -> tuple[TrajectoryEpisode | None, str]:
    env.reset()
    box_xyz, mailer_xyz = reset_sorting_parcels(
        env, task_id=task_id, single_parcel=True, rng=ep_rng
    )
    for _ in range(_SORTING_SETTLE_STEPS):
        env.step(zero_action)
        sync_shipping_labels(env)
    # Re-establish the planned randomized start after solver warm-up.  Parcel
    # Z now begins in resting contact and the collision core is analytic, so
    # this no longer restarts the former 2 mm mesh-drop transient.
    active_name = "parcel_box" if task_id == "push_box_to_bin" else (
        "mailer" if task_id == "nudge_mailer_to_bin" else None
    )
    if active_name is not None:
        planned_xyz = box_xyz if active_name == "parcel_box" else mailer_xyz
        _write_pose(env, active_name, planned_xyz)
    # Keep the already-settled physical pose. Re-pinning here restarted the
    # package/table contact transient; twelve camera warm-up frames were not
    # enough for that second drop, so an untouched box could drift ~3 cm over
    # a long rollout and be mistaken for an expert-induced wrong-way push.
    obs = None
    terminated = truncated = None
    for _ in range(_SORTING_CAMERA_WARMUP):
        obs, _rew, terminated, truncated, _info = env.step(zero_action)
        sync_shipping_labels(env)
    # Do not teleport the parcel again after warm-up: doing so created a
    # visible frame-0 -> frame-1 settling jump.  The last warm-up observation
    # is already the state before the first recorded action, preserving the
    # causal (observation_t, action_t) alignment without another physics step.
    if obs is None or terminated is None or truncated is None:
        return None, "camera warm-up produced no observation"
    if bool(terminated[0] or truncated[0]):
        return None, "environment terminated during camera warm-up"
    # Persist the actual settled pose used by frame 0 so replay/evaluation do
    # not silently restore the pre-settle teleport pose from metadata.
    box_xyz = parcel_xyz(env, "parcel_box")
    mailer_xyz = parcel_xyz(env, "mailer")
    print(
        "    rest "
        f"palmR={palm_xyz(robot, hand_idx['right'])} "
        f"wristR={wrist_xyz(robot, hand_idx['right'])} "
        f"box={parcel_xyz(env, 'parcel_box')} "
        f"mailer={parcel_xyz(env, 'mailer')}",
        flush=True,
    )

    frozen_plan = None
    if task_id == "push_box_to_bin":
        px, py, _pz = parcel_xyz(env, "parcel_box")
        if px < MIN_PARCEL_START_X:
            return None, f"box starts too close to table front x={px:.3f} < {MIN_PARCEL_START_X:.2f}"
        if abs(py) > MAX_PARCEL_START_ABS_Y:
            return None, f"box unsettled/off-centre |y|={abs(py):.3f} > {MAX_PARCEL_START_ABS_Y:.2f}"
        frozen_plan = plan_palm_push("right", px, py)
    elif task_id == "nudge_mailer_to_bin":
        px, py, _pz = parcel_xyz(env, "mailer")
        if px < MIN_PARCEL_START_X:
            return None, f"mailer starts too close to table front x={px:.3f} < {MIN_PARCEL_START_X:.2f}"
        if abs(py) > MAX_PARCEL_START_ABS_Y:
            return None, f"mailer unsettled/off-centre |y|={abs(py):.3f} > {MAX_PARCEL_START_ABS_Y:.2f}"
        frozen_plan = plan_palm_push("left", px, py)

    rgbs: list[np.ndarray] = []
    qs: list[np.ndarray] = []
    acts: list[np.ndarray] = []
    trail = []
    assist = PushAssistState()
    expert = ContactSweepState(plan=frozen_plan)
    cartesian = None
    if sorting_expert == "cartesian" and task_id == "push_box_to_bin":
        # Use the opposite-side hand so it starts behind the package and never
        # has to cross over it during approach.
        cartesian = CartesianSweepState("right", float(box_xyz[0]), float(box_xyz[1]))
    elif sorting_expert == "cartesian" and task_id == "nudge_mailer_to_bin":
        cartesian = CartesianSweepState("left", float(mailer_xyz[0]), float(mailer_xyz[1]))

    for step in range(horizon):
        act_np = scripted_action(
            task_id,
            step,
            horizon,
            phase_bias=phase_bias,
            action_noise=_SORTING_ACTION_NOISE,
            rng=ep_rng,
        )
        spec_push = {"push_box_to_bin": "right", "nudge_mailer_to_bin": "left"}.get(task_id)
        is_wait = task_id == "wait_no_package"
        phase = min(1.0, max(0.0, step / max(horizon - 1, 1) + phase_bias))
        if use_assist and spec_push and not is_wait:
            correct_palm_height(robot, hand_idx, act_np, side=spec_push)
        elif use_assist and task_id == "sweep_parcels_apart":
            correct_palm_height(robot, hand_idx, act_np, side="right")
            correct_palm_height(robot, hand_idx, act_np, side="left")
        elif spec_push and not is_wait:
            # Physics collect: stay at rest hover, then servo press + Y sweep.
            # Scripted keyframes retract the stump and lose table contact.
            act_np = np.zeros(23, dtype=np.float32)
            if sorting_expert == "cartesian":
                assert cartesian is not None
                cartesian_sweep_palm(
                    robot,
                    hand_idx,
                    act_np,
                    state=cartesian,
                    step=step,
                    default_q=default_q,
                )
            elif sorting_expert == "contact":
                press_and_sweep_palm(
                    env,
                    robot,
                    hand_idx,
                    act_np,
                    task_id=task_id,
                    phase=phase,
                    plan=frozen_plan,
                    state=expert,
                )
        act_np = clip_sorting_action_offset(act_np)
        if use_assist and not is_wait:
            follow_active_arm_push(act_np, task_id=task_id, phase=phase, state=assist)
            act_np = clip_sorting_action_offset(act_np)
        # Waist yaw rotates D435i (mounted on torso). Keep it square; 23-DoF
        # lateral reach comes from shoulder yaw, not torso lean.
        act_np[_TORSO_I] = 0.0
        action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
        # Record causal (observation_t, action_t) before stepping physics.
        trail.append(
            capture_step(
                env,
                robot,
                hand_idx,
                step=step,
                horizon=horizon,
                phase_bias=phase_bias,
            )
        )
        rgb = _to_uint8_nchw(obs["rgb"][0])
        q = obs["policy"][0].detach().cpu().numpy().astype(np.float32)
        if q.shape[-1] != dof:
            raise RuntimeError(f"expected {dof}-DoF q, got {q.shape}")
        rgbs.append(rgb)
        qs.append(q)
        acts.append((default_q + act_np).astype(np.float32))
        next_obs, _rew, terminated, truncated, _info = env.step(action)
        sync_shipping_labels(env)
        if use_assist and not is_wait:
            assist = maybe_assist_push(
                env,
                robot,
                hand_idx,
                task_id=task_id,
                phase=phase,
                state=assist,
            )
            sync_shipping_labels(env)
        if bool(terminated[0] or truncated[0]):
            break
        obs = next_obs

    if not rgbs:
        return None, "empty rollout"

    rgb_stack = np.stack(rgbs, axis=0)
    if rgb_stack.mean() / 255.0 < _MIN_RGB_MEAN:
        return None, f"rgb too dark mean={rgb_stack.mean() / 255.0:.3f}"

    report = evaluate_episode(task_id, trail, horizon=horizon)
    if not report.passed:
        last = trail[-1]
        mid = trail[len(trail) // 2]
        wrong_peak = None
        if task_id == "push_box_to_bin":
            wrong_peak = max(trail, key=lambda s: s.box_y)
        elif task_id == "nudge_mailer_to_bin":
            wrong_peak = min(trail, key=lambda s: s.mailer_y)
        wrong_peak_text = ""
        if wrong_peak is not None:
            peak_palm = wrong_peak.palm_right if task_id == "push_box_to_bin" else wrong_peak.palm_left
            peak_y = wrong_peak.box_y if task_id == "push_box_to_bin" else wrong_peak.mailer_y
            wrong_peak_text = (
                f" wrong_peak_phase={wrong_peak.phase:.3f}"
                f" palm=({peak_palm[0]:.2f},{peak_palm[1]:.2f},{peak_palm[2]:.2f})"
                f" parcel_y={peak_y:.3f}"
            )
        extra = (
            f" palmR_mid=({mid.palm_right[0]:.2f},{mid.palm_right[1]:.2f},{mid.palm_right[2]:.2f})"
            f" palmL_mid=({mid.palm_left[0]:.2f},{mid.palm_left[1]:.2f},{mid.palm_left[2]:.2f})"
            f" palmR_end=({last.palm_right[0]:.2f},{last.palm_right[1]:.2f},{last.palm_right[2]:.2f})"
            f" palmL_end=({last.palm_left[0]:.2f},{last.palm_left[1]:.2f},{last.palm_left[2]:.2f})"
            f" box_end=({last.box_x:.2f},{last.box_y:.2f},{last.box_z:.2f})"
            f" mailer_end=({last.mailer_x:.2f},{last.mailer_y:.2f},{last.mailer_z:.2f})"
            f"{wrong_peak_text}"
            f" expert={(cartesian.mode + '/' + str(cartesian.mode_step)) if cartesian is not None else (expert.mode + '/' + str(expert.t_mode))}"
        )
        return None, "; ".join(report.reasons) + extra

    episode = TrajectoryEpisode(
        rgb=rgb_stack,
        q=np.stack(qs, axis=0),
        action=np.stack(acts, axis=0),
        instruction=instruction,
        scene_id=package.scene_id,
        task_id=task.task_id,
        embodiment_id=spec.embodiment_id,
        joint_names=spec.joint_names,
        collect_meta={
            "quality_gate": True,
            "push_assist": bool(use_assist),
            "assist_frames": int(assist.frames_assisted),
            "touch_frames": int(report.touch_frames),
            "push_delta_y": float(report.push_delta_y),
            "table_pen_frames": int(report.table_pen_frames),
            "stable_zone_frames": int(report.stable_zone_frames),
            "wrong_way_excursion_y": float(report.wrong_way_excursion_y),
            "horizon": int(report.length),
            "calibration_tag": f"sorting_station_vla_{sorting_expert}_lateral_zone_v2_2026-09-16",
            "expert": f"{sorting_expert}_sweep",
            "expert_end_mode": (
                expert.mode
                if sorting_expert == "contact"
                else (cartesian.mode if cartesian is not None else "idle")
            ),
            "box_xyz": [float(box_xyz[0]), float(box_xyz[1]), float(box_xyz[2])],
            "mailer_xyz": [float(mailer_xyz[0]), float(mailer_xyz[1]), float(mailer_xyz[2])],
        },
    )
    meta = (
        f"T={report.length} touch={report.touch_frames} "
        f"push_dy={report.push_delta_y:.3f} stable={report.stable_zone_frames} "
        f"wrong_way={report.wrong_way_excursion_y:.3f} "
        f"table_pen={report.table_pen_frames} "
        f"assist={assist.frames_assisted}"
    )
    return episode, meta


def _parse_task_mix(raw: str) -> list[tuple[str, int]]:
    jobs: list[tuple[str, int]] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise SystemExit(f"bad --task-mix item {part!r}; expected task_id:count")
        task_id, count = part.rsplit(":", 1)
        jobs.append((task_id.strip(), int(count)))
    return jobs


def _sorting_instruction() -> str:
    return VLA_SORTING_UNIFIED_PROMPT


def main() -> None:
    spec = resolve_scene_env(args_cli.scene_id)
    package = load_named_scene(spec.scene_id)
    allowed = {t.task_id: t for t in filter_tasks(package, args_cli.requires_ee)}
    mix = _parse_task_mix(args_cli.task_mix)
    if mix:
        jobs = mix
    else:
        jobs = [(args_cli.task_id, args_cli.num_episodes)]
    for task_id, _n in jobs:
        if task_id not in allowed:
            raise SystemExit(
                f"task {task_id!r} is not available for requires_ee={args_cli.requires_ee}. "
                f"stump tasks: {sorted(allowed)}"
            )

    env_cfg = spec.env_cfg_cls()
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.sim.device = args_cli.device
    env = ManagerBasedRLEnv(cfg=env_cfg)
    print(f"env.step_dt={env.step_dt:.6f}s ({1.0 / env.step_dt:.1f} Hz control)")

    is_sorting = args_cli.scene_id == _SORTING_SCENE
    out_dir = Path(args_cli.out_dir) if args_cli.out_dir else ROOT / spec.default_out_dir
    unitree_dir = Path(args_cli.unitree_out) if args_cli.unitree_out else out_dir.parent / f"{out_dir.name}_unitree"
    if is_sorting and not args_cli.out_dir and len(jobs) == 1:
        canonical = sorting_dataset_dirs(jobs[0][0], root=ROOT)
        if canonical is not None:
            out_dir, unitree_dir = canonical
            if not args_cli.unitree_out:
                print(f"sorting dataset dirs: npz={out_dir.name} unitree={unitree_dir.name}")

    if args_cli.wipe and is_sorting:
        _wipe_sorting_datasets(out_dir, unitree_dir)
    else:
        out_dir.mkdir(parents=True, exist_ok=True)

    dof = len(spec.joint_names)
    zero_action = torch.zeros(args_cli.num_envs, dof, device=env.device)
    default_q = _SORTING_DEFAULT_Q if is_sorting else None

    use_gate = is_sorting and args_cli.quality_gate
    if is_sorting and not use_gate:
        print("[warn] sorting collect without --quality-gate; use --quality-gate --wipe for gated re-collect.")
    if is_sorting:
        print(
            "sorting mode: fixed stance (legs hold rest pose); "
            "active teleop DoF = 11 (L5 + R5 + waist_yaw); "
            f"embodiment={spec.embodiment_id} push_assist={bool(args_cli.push_assist)}"
        )

    hand_idx = resolve_hand_indices(env.scene["robot"]) if is_sorting else None
    robot = env.scene["robot"] if is_sorting else None

    saved: list[Path] = []
    instruction = _sorting_instruction() if is_sorting else None
    # Resume into a non-empty new dataset tree without overwriting earlier
    # accepted episodes.  (Protected historical trees must still never use
    # --wipe.)
    existing_indices = []
    for path in out_dir.glob("*_ep*.npz"):
        match = re.search(r"_ep(\d+)\.npz$", path.name)
        if match:
            existing_indices.append(int(match.group(1)))
    global_ep = max(existing_indices, default=-1) + 1
    if global_ep:
        print(f"resume: {global_ep} existing npz episodes; next index={global_ep}")
    # A resumed collection must not replay the same horizon/phase/reset RNG
    # stream used by episode 0.  Offset the deterministic seed by the first
    # new global episode so appends add coverage instead of silent duplicates.
    master_rng = np.random.default_rng(20260910 + global_ep)

    for task_id, n_ep in jobs:
        task = allowed[task_id]
        goal = instruction if is_sorting else task.instruction
        for ep in range(n_ep):
            if use_gate:
                accepted = False
                attempts = args_cli.max_attempts if task_id != "wait_no_package" else min(args_cli.max_attempts, 12)
                for attempt in range(attempts):
                    if task_id == "wait_no_package":
                        horizon = sample_wait_horizon(master_rng)
                        phase_bias = 0.0
                    else:
                        horizon = sample_sorting_horizon(master_rng)
                        phase_bias = float(master_rng.uniform(-0.008, 0.008))
                    ep_rng = np.random.default_rng(master_rng.integers(0, 2**31 - 1))
                    episode, info = _run_sorting_rollout(
                        env,
                        task=task,
                        spec=spec,
                        package=package,
                        task_id=task_id,
                        horizon=horizon,
                        phase_bias=phase_bias,
                        ep_rng=ep_rng,
                        hand_idx=hand_idx,
                        robot=robot,
                        default_q=default_q,
                        dof=dof,
                        zero_action=zero_action,
                        instruction=goal,
                        use_assist=bool(args_cli.push_assist),
                        sorting_expert=args_cli.sorting_expert,
                    )
                    if episode is None:
                        print(
                            f"  {task_id} ep{global_ep:03d} attempt {attempt + 1}/{attempts} REJECT: {info}",
                            flush=True,
                        )
                        continue
                    path = out_dir / f"{task.task_id}_ep{global_ep:03d}.npz"
                    save_episode(episode, path)
                    saved.append(path)
                    print(f"  {task_id} ep{global_ep:03d} attempt {attempt + 1} ACCEPT {info} → {path.name}")
                    if args_cli.unitree:
                        ep_dir = export_episode_unitree_json(
                            episode,
                            unitree_dir,
                            episode_id=None,
                            fps=args_cli.unitree_fps,
                            goal=goal,
                            desc=goal,
                        )
                        print(f"    unitree → {ep_dir}")
                    accepted = True
                    break
                if not accepted:
                    raise RuntimeError(
                        f"failed to collect accepted episode {global_ep} ({task_id}) after {attempts} attempts"
                    )
                global_ep += 1
                continue

            # Legacy ungated path (kitchen / indoor / sorting without gate).
            horizon = args_cli.steps
            reset_result = env.reset()
            obs = reset_result[0] if isinstance(reset_result, tuple) else reset_result
            ep_rng = np.random.default_rng(42 + global_ep)
            if is_sorting:
                reset_sorting_parcels(env, task_id=task.task_id, single_parcel=True, rng=ep_rng)
                for _ in range(_SORTING_SETTLE_STEPS):
                    obs, _rew, _terminated, _truncated, _info = env.step(zero_action)
                    sync_shipping_labels(env)
                for _ in range(_SORTING_CAMERA_WARMUP):
                    obs, _rew, _terminated, _truncated, _info = env.step(zero_action)
                    sync_shipping_labels(env)
            phase_bias = ((global_ep % 5) - 2) * 0.012 if is_sorting else 0.0
            rgbs = []
            qs = []
            acts = []
            for step in range(horizon):
                act_np = scripted_action(
                    task.task_id,
                    step,
                    horizon,
                    phase_bias=phase_bias,
                    action_noise=_SORTING_ACTION_NOISE if is_sorting else 0.0,
                    rng=ep_rng,
                )
                if is_sorting:
                    act_np = clip_sorting_action_offset(act_np)
                action = torch.from_numpy(act_np).to(env.device).unsqueeze(0).repeat(env.num_envs, 1)
                rgb = _to_uint8_nchw(obs["rgb"][0])
                q = obs["policy"][0].detach().cpu().numpy().astype(np.float32)
                rgbs.append(rgb)
                qs.append(q)
                if is_sorting and default_q is not None:
                    acts.append((default_q + act_np).astype(np.float32))
                else:
                    acts.append(act_np)
                next_obs, _rew, terminated, truncated, _info = env.step(action)
                if is_sorting:
                    sync_shipping_labels(env)
                if bool(terminated[0] or truncated[0]):
                    break
                obs = next_obs
            episode = TrajectoryEpisode(
                rgb=np.stack(rgbs, axis=0),
                q=np.stack(qs, axis=0),
                action=np.stack(acts, axis=0),
                instruction=goal if goal is not None else task.instruction,
                scene_id=package.scene_id,
                task_id=task.task_id,
                embodiment_id=spec.embodiment_id,
                joint_names=spec.joint_names,
            )
            path = out_dir / f"{task.task_id}_ep{global_ep:03d}.npz"
            save_episode(episode, path)
            saved.append(path)
            print(f"saved {path} T={episode.rgb.shape[0]}")
            if args_cli.unitree:
                export_episode_unitree_json(
                    episode,
                    unitree_dir,
                    episode_id=global_ep,
                    fps=args_cli.unitree_fps,
                    goal=goal if goal is not None else task.instruction,
                    desc=goal if goal is not None else task.instruction,
                )
            global_ep += 1

    env.close()
    simulation_app.close()
    print(f"done. {len(saved)} accepted episodes → {out_dir}")


if __name__ == "__main__":
    main()
