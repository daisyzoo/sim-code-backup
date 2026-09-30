#!/usr/bin/env python3
"""Analyze real teleop vs sim images; print / write sorting-station calibration report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from simfoundry.calibration.sorting_station import (
    SORTING_D435I_POS,
    SORTING_D435I_ROT_XYZW,
    SORTING_ROBOT_POS,
    SORTING_ROBOT_STANDOFF_M,
    TABLE_FRONT_X,
    TABLE_TOP_Z,
)


def _metrics(path: Path) -> dict:
    bgr = cv2.imread(str(path))
    if bgr is None:
        return {"path": str(path), "error": "unreadable"}
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    # Upper-band brightness (vent / ceiling region in real teleop).
    upper = gray[: int(h * 0.28), :].mean()
    lower = gray[int(h * 0.55) :, :].mean()
    return {
        "path": path.name,
        "brightness": float(gray.mean()),
        "upper_band": float(upper),
        "lower_band": float(lower),
        "size": [w, h],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sorting station calibration report.")
    parser.add_argument(
        "--real-image",
        default="/home/user/Desktop/project/data/pick_cup_soring_0824/episode_0004/colors/000000_color_0.jpg",
    )
    parser.add_argument(
        "--sim-image",
        default=str(ROOT / "datasets/sorting_station_g1_23_unitree/episode_0000/colors/000010_color_0.jpg"),
    )
    parser.add_argument("--out", default=str(ROOT / "demo/calibration/sorting_station_report.json"))
    args = parser.parse_args()

    real = _metrics(Path(args.real_image))
    sim = _metrics(Path(args.sim_image))

    report = {
        "table": {"front_edge_x_m": TABLE_FRONT_X, "top_z_m": TABLE_TOP_Z},
        "robot": {
            "pos_m": list(SORTING_ROBOT_POS),
            "rot_xyzw": [0.0, 0.0, 0.0, 1.0],
            "standoff_to_table_front_m": SORTING_ROBOT_STANDOFF_M,
            "faces": "+X toward table",
        },
        "d435i": {
            "parent": "torso_link",
            "offset_pos_m": list(SORTING_D435I_POS),
            "offset_rot_xyzw": list(SORTING_D435I_ROT_XYZW),
        },
        "image_metrics": {"real_teleop": real, "sim": sim},
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Sorting station calibration ===")
    print(f"table front x = {TABLE_FRONT_X:.3f} m, top z = {TABLE_TOP_Z:.3f} m")
    print(f"robot pos   = {SORTING_ROBOT_POS}  (standoff {SORTING_ROBOT_STANDOFF_M:.2f} m)")
    print(f"d435i offset pos = {SORTING_D435I_POS}")
    print(f"d435i offset rot = {SORTING_D435I_ROT_XYZW}")
    print(f"real image: {real}")
    print(f"sim image:  {sim}")
    print(f"report → {out}")


if __name__ == "__main__":
    main()
