#!/usr/bin/env python3
"""Regenerate demo/preview assets from an existing npz episode (no Isaac)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.data.schema import load_episode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npz",
        default=str(ROOT / "datasets" / "kitchen_counter_placeholder" / "push_cup_to_bowl_ep000.npz"),
    )
    parser.add_argument("--out", default=str(ROOT / "demo" / "preview"))
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ep = load_episode(args.npz)
    idxs = sorted({0, ep.rgb.shape[0] // 2, ep.rgb.shape[0] - 1})
    tiles = []
    for i in idxs:
        frame = ep.rgb[i].transpose(1, 2, 0)
        path = out / f"frame_{i:03d}.png"
        cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        tiles.append(frame)
    sheet = np.concatenate(tiles, axis=1)
    cv2.imwrite(str(out / "contact_sheet.png"), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    np.savetxt(
        out / "q_right_arm.csv",
        ep.q[:, 18:],
        delimiter=",",
        header="r_shoulder_pitch,r_shoulder_roll,r_shoulder_yaw,r_elbow_pitch,r_elbow_roll",
        comments="",
    )
    summary = {
        "npz": str(Path(args.npz).resolve()),
        "task": ep.task_id,
        "instruction": ep.instruction,
        "embodiment_id": ep.embodiment_id,
        "T": int(ep.rgb.shape[0]),
        "rgb_shape": list(ep.rgb.shape),
        "rgb_mean": float(ep.rgb.mean()),
        "frame_indices": idxs,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote preview under {out}")


if __name__ == "__main__":
    main()
