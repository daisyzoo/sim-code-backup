#!/usr/bin/env python3
"""Probe reachable U1 palm poses before changing the sorting rest calibration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--num_envs", type=int, default=1)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
launcher = AppLauncher(args_cli, enable_cameras=True)
simulation_app = launcher.app

import numpy as np
import torch
from isaaclab.envs import ManagerBasedRLEnv

from simfoundry.calibration.sorting_station import reset_sorting_parcels
from simfoundry.data.sorting_quality import palm_xyz, resolve_hand_indices, wrist_xyz
from simfoundry.isaac_envs.sorting_env_cfg import SortingStationEnvCfg


def main() -> None:
    cfg = SortingStationEnvCfg()
    cfg.scene.num_envs = 1
    env = ManagerBasedRLEnv(cfg=cfg)
    robot = env.scene["robot"]
    hands = resolve_hand_indices(robot)
    # Offsets relative to calibrated q0. Negative pitch reaches toward +X;
    # elbow offsets explore height/reach compensation.
    pitch_offsets = (0.0, -0.12, -0.24, -0.36, -0.48)
    elbow_offsets = (-0.24, -0.12, 0.0, 0.12, 0.24)
    print("pitch_off elbow_off palm_x palm_y palm_z wrist_x wrist_y wrist_z")
    for pitch in pitch_offsets:
        for elbow in elbow_offsets:
            env.reset()
            reset_sorting_parcels(env, task_id="wait_no_package", single_parcel=True)
            off = np.zeros(23, dtype=np.float32)
            off[18] = pitch
            off[21] = elbow
            action = torch.from_numpy(off).to(env.device).unsqueeze(0)
            for _ in range(35):
                env.step(action)
            p = palm_xyz(robot, hands["right"])
            w = wrist_xyz(robot, hands["right"])
            print(
                f"{pitch:+.2f} {elbow:+.2f} "
                f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} "
                f"{w[0]:.4f} {w[1]:.4f} {w[2]:.4f}",
                flush=True,
            )
    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
