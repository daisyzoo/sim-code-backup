#!/usr/bin/env python3
"""One-rollout diagnostic for sorting quality gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
parser.add_argument("--task-id", default="push_box_to_bin")
parser.add_argument("--horizon", type=int, default=195)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app = AppLauncher(args, enable_cameras=True).app

import numpy as np
import torch
from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.calibration.sorting_station import reset_sorting_parcels
from simfoundry.data.sorting_push_assist import PushAssistState, correct_palm_height, maybe_assist_push
from simfoundry.data.scripted import scripted_action
from simfoundry.data.sorting_quality import (
    TABLE_TOP_Z,
    _TASK_SPEC,
    capture_step,
    evaluate_episode,
    palm_xyz,
    resolve_hand_indices,
)
from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg
from simfoundry.robots.g1_assets import clip_sorting_action_offset
from simfoundry.scene_bridge.labels import sync_shipping_labels

env = ManagerBasedRLEnv(cfg=SortingStationEnvCfg())
robot = env.scene["robot"]
hand_idx = resolve_hand_indices(robot)
zero = torch.zeros(1, 23, device=env.device)
task_id = args.task_id
horizon = args.horizon
spec = _TASK_SPEC[task_id]
hand = spec["hand"]
parcel = spec["parcel"]

env.reset()
reset_sorting_parcels(env, task_id=task_id, single_parcel=True)
from simfoundry.data.sorting_quality import parcel_xyz
print("after reset box", parcel_xyz(env, "parcel_box"), "mailer", parcel_xyz(env, "mailer"))
for name in ("parcel_box_b", "mailer_b", "mailer_c", "mailer_d"):
    try:
        print(" ", name, parcel_xyz(env, name))
    except Exception as e:
        print(" ", name, "ERR", e)
for _ in range(42):
    env.step(zero)
    sync_shipping_labels(env)
print("after settle box", parcel_xyz(env, "parcel_box"), "mailer", parcel_xyz(env, "mailer"))
idle_l = palm_xyz(robot, hand_idx["left"])
idle_r = palm_xyz(robot, hand_idx["right"])
print(f"idle palms L={idle_l} R={idle_r}")
print(
    f"idle palms Lz={idle_l[2]:.3f} Rz={idle_r[2]:.3f} TABLE_TOP={TABLE_TOP_Z:.3f} "
    f"dL={idle_l[2]-TABLE_TOP_Z:+.3f} dR={idle_r[2]-TABLE_TOP_Z:+.3f}"
)

trail = []
assist = PushAssistState()
min_h = 999.0
best = None
min_palm_z = 999.0
for step in range(horizon):
    act = clip_sorting_action_offset(scripted_action(task_id, step, horizon))
    act_np = act if hasattr(act, "copy") else act
    import numpy as np

    act_np = np.asarray(act, dtype=np.float32).copy()
    correct_palm_height(robot, hand_idx, act_np, side="right")
    correct_palm_height(robot, hand_idx, act_np, side="left")
    env.step(torch.from_numpy(act_np).to(env.device).unsqueeze(0))
    sync_shipping_labels(env)
    phase = step / max(horizon - 1, 1)
    assist = maybe_assist_push(env, robot, hand_idx, task_id=task_id, phase=phase, state=assist)
    sync_shipping_labels(env)
    snap = capture_step(env, robot, hand_idx, step=step, horizon=horizon)
    trail.append(snap)
    palm = snap.palm_right if hand == "right" else snap.palm_left
    min_palm_z = min(min_palm_z, snap.palm_left[2], snap.palm_right[2])
    if parcel == "parcel_box":
        ox, oy, oz = snap.box_x, snap.box_y, snap.box_z
    else:
        ox, oy, oz = snap.mailer_x, snap.mailer_y, snap.mailer_z
    h = ((palm[0] - ox) ** 2 + (palm[1] - oy) ** 2) ** 0.5
    if h < min_h:
        min_h = h
        best = (step, snap.phase, palm, (ox, oy, oz))

report = evaluate_episode(task_id, trail, horizon=horizon)
print(f"task={task_id} T={len(trail)} passed={report.passed}")
print(f"reasons: {report.reasons}")
print(f"assist frames={assist.frames_assisted} latched={assist.latched}")
if best:
    step, phase, palm, obj = best
    print(
        f"closest step={step} phase={phase:.2f} palm={palm} obj={obj} "
        f"horiz={min_h:.3f} palm_z_delta={palm[2]-TABLE_TOP_Z:+.3f}"
    )
ys = [s.box_y if parcel == "parcel_box" else s.mailer_y for s in trail]
xs = [s.box_x if parcel == "parcel_box" else s.mailer_x for s in trail]
push_phases = [s for s in trail if s.phase >= 0.55]
if push_phases:
    pr = [s.palm_right if hand == "right" else s.palm_left for s in push_phases]
    print(
        f"push phase palm x [{min(p[0] for p in pr):.2f},{max(p[0] for p in pr):.2f}] "
        f"y [{min(p[1] for p in pr):.2f},{max(p[1] for p in pr):.2f}] "
        f"z [{min(p[2] for p in pr):.2f},{max(p[2] for p in pr):.2f}]"
    )
print(f"parcel y range [{min(ys):.3f},{max(ys):.3f}]  x range [{min(xs):.3f},{max(xs):.3f}]")
y0 = trail[0].box_y if parcel == "parcel_box" else trail[0].mailer_y
y1 = trail[-1].box_y if parcel == "parcel_box" else trail[-1].mailer_y
print(f"parcel y: {y0:.3f} -> {y1:.3f}  dy={y1-y0:+.3f}")
print(f"min either-palm z={min_palm_z:.3f} delta={min_palm_z-TABLE_TOP_Z:+.3f}")
env.close()
app.close()
