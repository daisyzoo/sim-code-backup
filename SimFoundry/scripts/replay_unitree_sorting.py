#!/usr/bin/env python3
"""Open-loop replay of recorded Unitree 11-D absolute joints in Isaac.

Confirms a collected demo still moves the parcel via physics (no kinematic assist).

    conda activate env_isaaclab
    export OMNI_KIT_ACCEPT_EULA=yes DISPLAY=:1
    cd /home/user/Documents/zoo/sim/IsaacLab
    ./isaaclab.sh -p ../SimFoundry/scripts/replay_unitree_sorting.py \\
      --dataset ../SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0910 \\
      --viz none --save-preview
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Replay Unitree sorting JSON in Isaac.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument(
    "--dataset",
    default=str(ROOT / "datasets" / "sorting_station_g1_23_unitree_vla_0910"),
)
parser.add_argument("--episodes", default="", help="Comma episode ids, or empty = one per task_id.")
parser.add_argument("--record-dir", default="")
parser.add_argument("--save-preview", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = app_launcher.app

import torch
from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.calibration.sorting_station import (
    SORTING_BOX_REST_SINGLE,
    SORTING_MAILER_REST_SINGLE,
    TABLE_TOP_Z,
    reset_sorting_parcels,
)
from simfoundry.data.sorting_quality import PARCEL_DROP_Z, parcel_xyz
from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg
from simfoundry.robots.g1_assets import clip_sorting_action_offset, u1_sorting_default_qpos_np
from simfoundry.scene_bridge.labels import sync_shipping_labels

_LEFT_ARM = slice(13, 18)
_RIGHT_ARM = slice(18, 23)
_WAIST = 12


def _abs11_to_offset23(act11: np.ndarray, default_q: np.ndarray) -> np.ndarray:
    q = default_q.astype(np.float32).copy()
    a = np.asarray(act11, dtype=np.float32).reshape(-1)
    q[13:18] = a[0:5]
    q[18:23] = a[5:10]
    q[12] = a[10]
    return clip_sorting_action_offset(q - default_q)


def _frame_abs11(frame: dict) -> np.ndarray:
    la = frame["actions"]["left_arm"]["qpos"]
    ra = frame["actions"]["right_arm"]["qpos"]
    wy = frame["actions"]["body"]["qpos"][0]
    return np.asarray(list(la) + list(ra) + [wy], dtype=np.float32)


def _episode_dirs(dataset: Path, spec: str) -> list[Path]:
    if spec.strip():
        ids = [int(x) for x in spec.split(",") if x.strip()]
        return [dataset / f"episode_{i:04d}" for i in ids]
    by_task: dict[str, Path] = {}
    for path in sorted(dataset.glob("episode_*")):
        payload = json.loads((path / "data.json").read_text())
        task_id = payload["info"]["simfoundry"]["task_id"]
        by_task.setdefault(task_id, path)
    return [by_task[k] for k in sorted(by_task)]


def main() -> None:
    dataset = Path(args_cli.dataset)
    record_dir = Path(args_cli.record_dir) if args_cli.record_dir else ROOT / "demo" / "replay_vla_0910"
    record_dir.mkdir(parents=True, exist_ok=True)
    env = ManagerBasedRLEnv(cfg=SortingStationEnvCfg())
    default_q = u1_sorting_default_qpos_np()
    zero = torch.zeros(1, 23, device=env.device)
    results = []
    for ep_dir in _episode_dirs(dataset, args_cli.episodes):
        payload = json.loads((ep_dir / "data.json").read_text())
        task_id = payload["info"]["simfoundry"]["task_id"]
        frames = payload["data"]
        env.reset()
        collect = payload.get("info", {}).get("simfoundry", {}).get("collect", {})
        box_xyz = tuple(collect["box_xyz"]) if collect.get("box_xyz") else SORTING_BOX_REST_SINGLE
        mailer_xyz = tuple(collect["mailer_xyz"]) if collect.get("mailer_xyz") else SORTING_MAILER_REST_SINGLE
        if task_id == "push_box_to_bin":
            mailer_xyz = None
        elif task_id == "nudge_mailer_to_bin":
            box_xyz = None
        reset_sorting_parcels(
            env, task_id=task_id, single_parcel=True, box_xyz=box_xyz, mailer_xyz=mailer_xyz
        )
        zero_t = torch.zeros(1, 23, device=env.device)
        for _ in range(30):
            env.step(zero_t)
            sync_shipping_labels(env)
        reset_sorting_parcels(
            env, task_id=task_id, single_parcel=True, box_xyz=box_xyz, mailer_xyz=mailer_xyz
        )
        for _ in range(12):
            env.step(zero_t)
            sync_shipping_labels(env)
        reset_sorting_parcels(
            env, task_id=task_id, single_parcel=True, box_xyz=box_xyz, mailer_xyz=mailer_xyz
        )
        start_box = parcel_xyz(env, "parcel_box")
        start_mailer = parcel_xyz(env, "mailer")
        peak_dy = 0.0
        min_z = TABLE_TOP_Z
        if task_id == "push_box_to_bin":
            min_z = start_box[2]
        elif task_id == "nudge_mailer_to_bin":
            min_z = start_mailer[2]
        for frame in frames:
            off = _abs11_to_offset23(_frame_abs11(frame), default_q)
            action = torch.from_numpy(off).to(env.device).unsqueeze(0)
            env.step(action)
            sync_shipping_labels(env)
            if task_id == "push_box_to_bin":
                _, y, z = parcel_xyz(env, "parcel_box")
                peak_dy = max(peak_dy, start_box[1] - y)
                min_z = min(min_z, z)
            elif task_id == "nudge_mailer_to_bin":
                _, y, z = parcel_xyz(env, "mailer")
                peak_dy = max(peak_dy, y - start_mailer[1])
                min_z = min(min_z, z)
        end_box = parcel_xyz(env, "parcel_box")
        end_mailer = parcel_xyz(env, "mailer")
        if task_id == "push_box_to_bin":
            dy = peak_dy
            z = min_z
            # Off-table after a push is success; only a no-move replay fails.
            ok = dy >= 0.08 or z < PARCEL_DROP_Z
        elif task_id == "nudge_mailer_to_bin":
            dy = peak_dy
            z = min_z
            ok = dy >= 0.08 or z < PARCEL_DROP_Z
        else:
            dy = 0.0
            z = TABLE_TOP_Z
            ok = abs(end_box[1]) > 2.0 and abs(end_mailer[1]) > 2.0
        rec = {
            "episode": ep_dir.name,
            "task_id": task_id,
            "frames": len(frames),
            "start_box": start_box,
            "end_box": end_box,
            "start_mailer": start_mailer,
            "end_mailer": end_mailer,
            "push_dy": dy,
            "end_z": z,
            "ok": ok,
        }
        results.append(rec)
        print(json.dumps(rec, indent=2))
    (record_dir / "replay_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    env.close()
    simulation_app.close()
    if failed:
        raise SystemExit(f"replay failed: {[r['episode'] for r in failed]}")
    print(f"replay ok  n={len(results)}  → {record_dir / 'replay_summary.json'}")


if __name__ == "__main__":
    main()
