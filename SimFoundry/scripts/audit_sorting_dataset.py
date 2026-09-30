#!/usr/bin/env python3
"""Audit sorting-station npz or Unitree episode exports (no Isaac required).

Checks RGB heuristics (hand-like dark pixels in lower FOV), frame count, brightness.
Use while a long collect runs to spot bad episodes without opening Kit.

Examples::

    python scripts/audit_sorting_dataset.py \\
        --unitree-dir datasets/sorting_station_g1_23_unitree_0831

    python scripts/audit_sorting_dataset.py \\
        --npz-dir datasets/sorting_station_g1_23_0831 --sample-every 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

# Keep this audit usable without Isaac Lab imports.
SORTING_MIN_FRAMES = 105
WAIT_MIN_FRAMES = 14
MAX_ADJACENT_FRAME_MAD = 6.0
MIN_PARCEL_START_X = 0.35

try:
    import cv2
except ImportError:
    cv2 = None


def _hand_score_bgr(img: np.ndarray) -> float:
    """Heuristic: fraction of dark pixels in bottom 45% (where teleop hands appear)."""
    h, w = img.shape[:2]
    band = img[int(h * 0.55) :, :, :]
    gray = band.mean(axis=2)
    # Rubber hands + shadow: darker than table blue in lower band.
    dark = (gray < 85).mean()
    return float(dark)


def _brightness(img: np.ndarray) -> float:
    return float(img.mean(axis=(0, 1)).mean() / 255.0)


def audit_unitree_episode(ep_dir: Path, *, sample_every: int = 15) -> dict:
    colors = sorted((ep_dir / "colors").glob("*_color_0.jpg"))
    if not colors:
        return {"episode": ep_dir.name, "error": "no colors"}
    scores = []
    brights = []
    for i, p in enumerate(colors):
        if i % sample_every != 0 and i != len(colors) - 1:
            continue
        if cv2 is None:
            raise RuntimeError("opencv-python required: pip install opencv-python")
        img = cv2.imread(str(p))
        if img is None:
            continue
        scores.append(_hand_score_bgr(img))
        brights.append(_brightness(img))
    n_frames = len(colors)
    data_path = ep_dir / "data.json"
    n_json = 0
    task_id = ""
    max_action_jump = 0.0
    max_state_jump = 0.0
    if data_path.is_file():
        with data_path.open() as f:
            payload = json.load(f)
        frames = payload.get("data", [])
        n_json = len(frames)
        task_id = payload.get("info", {}).get("simfoundry", {}).get("task_id", "")
        action_rows = []
        state_rows = []
        for frame in frames:
            controls = frame.get("actions", {})
            states = frame.get("states", {})
            row = []
            state_row = []
            for group in ("left_arm", "right_arm", "body"):
                row.extend(controls.get(group, {}).get("qpos", []))
                state_row.extend(states.get(group, {}).get("qpos", []))
            if row:
                action_rows.append(row)
            if state_row:
                state_rows.append(state_row)
        if len(action_rows) > 1:
            max_action_jump = float(np.max(np.abs(np.diff(np.asarray(action_rows), axis=0))))
        if len(state_rows) > 1:
            max_state_jump = float(np.max(np.abs(np.diff(np.asarray(state_rows), axis=0))))
    avg_hand = float(np.mean(scores)) if scores else 0.0
    avg_bright = float(np.mean(brights)) if brights else 0.0
    # Empirical: sim episodes with visible rubber hands often score > 0.08 in lower band.
    min_frames = WAIT_MIN_FRAMES if task_id == "wait_no_package" else SORTING_MIN_FRAMES
    no_reset_jump = max_state_jump < 0.25
    flag = (
        "ok"
        if avg_hand >= 0.06 and n_frames >= min_frames and n_frames == n_json and no_reset_jump
        else "review"
    )
    return {
        "episode": ep_dir.name,
        "frames_jpg": n_frames,
        "frames_json": n_json,
        "hand_score_avg": round(avg_hand, 4),
        "brightness_avg": round(avg_bright, 4),
        "task_id": task_id,
        "max_action_jump": round(max_action_jump, 5),
        "max_state_jump": round(max_state_jump, 5),
        "terminal_reset_suspected": not no_reset_jump,
        "flag": flag,
    }


def audit_npz(path: Path) -> dict:
    z = np.load(path, allow_pickle=True)
    rgb = z["rgb"]
    t = rgb.shape[0]
    scores = []
    for i in range(0, t, max(1, t // 12)):
        img = np.transpose(rgb[i], (1, 2, 0))  # CHW → HWC RGB
        if cv2 is not None:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        scores.append(_hand_score_bgr(img))
    avg_hand = float(np.mean(scores)) if scores else 0.0
    task_id = str(z["task_id"].item()) if "task_id" in z.files else path.name.split("_ep", 1)[0]
    min_frames = WAIT_MIN_FRAMES if task_id == "wait_no_package" else SORTING_MIN_FRAMES
    action = z["action"] if "action" in z.files else np.empty((0,))
    max_action_jump = (
        float(np.max(np.abs(np.diff(action, axis=0)))) if action.ndim == 2 and len(action) > 1 else 0.0
    )
    q = z["q"] if "q" in z.files else np.empty((0,))
    max_state_jump = float(np.max(np.abs(np.diff(q, axis=0)))) if q.ndim == 2 and len(q) > 1 else 0.0
    if t > 1:
        # Mean absolute RGB delta in 8-bit pixel units.  This catches reset,
        # teleport and first-frame settling discontinuities that joint-state
        # checks cannot see (for example a parcel moving under idle arms).
        frame_mad = np.abs(np.diff(rgb.astype(np.int16), axis=0)).mean(axis=(1, 2, 3))
        max_frame_mad = float(frame_mad.max())
        first_frame_mad = float(frame_mad[0])
    else:
        max_frame_mad = first_frame_mad = 0.0
    continuous = max_frame_mad < MAX_ADJACENT_FRAME_MAD
    start_x = None
    safe_start = True
    if "collect_meta" in z.files and task_id != "wait_no_package":
        try:
            collect_meta = json.loads(str(z["collect_meta"].item()))
            xyz_key = "box_xyz" if task_id == "push_box_to_bin" else "mailer_xyz"
            start_x = float(collect_meta[xyz_key][0])
            safe_start = start_x >= MIN_PARCEL_START_X
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            safe_start = False
    return {
        "file": path.name,
        "frames": t,
        "hand_score_avg": round(avg_hand, 4),
        "task_id": task_id,
        "max_action_jump": round(max_action_jump, 5),
        "max_state_jump": round(max_state_jump, 5),
        "first_frame_mad": round(first_frame_mad, 4),
        "max_frame_mad": round(max_frame_mad, 4),
        "frame_discontinuity_suspected": not continuous,
        "parcel_start_x": None if start_x is None else round(start_x, 4),
        "unsafe_parcel_start": not safe_start,
        "terminal_reset_suspected": max_state_jump >= 0.25,
        "flag": (
            "ok"
            if avg_hand >= 0.06 and t >= min_frames and max_state_jump < 0.25 and continuous and safe_start
            else "review"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unitree-dir", type=Path, default=None)
    parser.add_argument("--npz-dir", type=Path, default=None)
    parser.add_argument("--sample-every", type=int, default=15)
    args = parser.parse_args()
    if not args.unitree_dir and not args.npz_dir:
        parser.error("pass --unitree-dir and/or --npz-dir")

    rows: list[dict] = []
    if args.unitree_dir:
        for ep in sorted(args.unitree_dir.glob("episode_*")):
            if ep.is_dir():
                rows.append(audit_unitree_episode(ep, sample_every=args.sample_every))
    if args.npz_dir:
        for npz in sorted(args.npz_dir.glob("*.npz")):
            rows.append(audit_npz(npz))

    ok = sum(1 for r in rows if r.get("flag") == "ok")
    review = [r for r in rows if r.get("flag") == "review"]
    print(f"audited {len(rows)} items: {ok} ok, {len(review)} review")
    for r in rows:
        tag = r.get("flag", "?")
        name = r.get("episode") or r.get("file")
        hs = r.get("hand_score_avg", 0)
        fr = r.get("frames_jpg") or r.get("frames")
        jump = r.get("max_action_jump", 0)
        state_jump = r.get("max_state_jump", 0)
        frame_mad = r.get("max_frame_mad")
        task = r.get("task_id", "?")
        print(
            f"  [{tag:6s}] {name} task={task} frames={fr} hand_score={hs:.3f} "
            f"action_jump={jump:.4f} state_jump={state_jump:.4f}"
            + (f" frame_mad={frame_mad:.3f}" if frame_mad is not None else "")
        )
    if review:
        print("\nreview episodes (low hand_score or short horizon):")
        for r in review:
            print(f"  {r.get('episode') or r.get('file')}: {r}")


if __name__ == "__main__":
    main()
