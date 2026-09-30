#!/usr/bin/env python3
"""Convert SimFoundry npz trajectories to HuggingFace LeRobotDataset v2.1.

Example:

    conda activate env_isaaclab
    cd /home/user/Documents/zoo/sim/SimFoundry
    python scripts/npz_to_lerobot.py \\
      --npz-dir datasets/kitchen_counter_placeholder \\
      --out datasets/kitchen_counter_placeholder_lerobot \\
      --overwrite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.data.lerobot_v21 import DEFAULT_FPS, IMAGE_KEY, export_npz_dir_to_lerobot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npz-dir",
        default=str(ROOT / "datasets" / "kitchen_counter_placeholder"),
        help="Directory of SimFoundry *.npz episodes",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "datasets" / "kitchen_counter_placeholder_lerobot"),
        help="LeRobot v2.1 dataset root",
    )
    parser.add_argument("--pattern", default="*.npz")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    result = export_npz_dir_to_lerobot(
        args.npz_dir,
        args.out,
        pattern=args.pattern,
        fps=args.fps,
        overwrite=args.overwrite,
    )
    print(f"wrote LeRobot v2.1 dataset → {result.root}")
    print(f"  episodes={result.num_episodes} frames={result.num_frames} tasks={result.num_tasks}")
    print(f"  image key={IMAGE_KEY}")
    print(f"  load with: LeRobotDataset('{result.root}')  # after pip/uv install lerobot")


if __name__ == "__main__":
    main()
