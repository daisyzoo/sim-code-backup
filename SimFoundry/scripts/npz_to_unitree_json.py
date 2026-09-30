#!/usr/bin/env python3
"""Convert SimFoundry npz seed episodes → Unitree episode_*/data.json layout.

Matches /home/user/Desktop/project/data/pick_cup_soring_0824 so the same
unitree_lerobot converters (G1_23 11-D) can ingest sim data.

    python scripts/npz_to_unitree_json.py \\
      --npz-dir datasets/sorting_station_g1_23 \\
      --out datasets/sorting_station_g1_23_unitree \\
      --fps 15 --overwrite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.data.unitree_json import export_npz_dir_to_unitree_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--npz-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fps", type=float, default=15.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    written = export_npz_dir_to_unitree_json(
        args.npz_dir, args.out, fps=args.fps, overwrite=args.overwrite
    )
    print(f"wrote {len(written)} episodes → {args.out}")
    for p in written[:5]:
        print(f"  {p}")
    if len(written) > 5:
        print(f"  ... +{len(written) - 5} more")


if __name__ == "__main__":
    main()
