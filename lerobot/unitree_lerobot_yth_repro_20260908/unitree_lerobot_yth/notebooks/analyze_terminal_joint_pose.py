"""Build a terminal joint-pose detector config from a LeRobot parquet dataset.

The analysis uses measured ``observation.state`` values, not commanded actions.
For each episode it summarizes the final short window, rejects endpoints that
are still moving, and derives robust per-joint terminal bounds and stability
tolerances. The generated JSON is consumed by the real-robot MCP RTC runtime.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def _as_floats(values: np.ndarray) -> list[float]:
    return [round(float(value), 8) for value in values]


def _first_detection(
    states: np.ndarray,
    *,
    fps: float,
    lower: np.ndarray,
    upper: np.ndarray,
    max_p90_deviation: np.ndarray,
    hold_s: float,
    min_elapsed_s: float,
    minimum_terminal_inlier_fraction: float,
) -> int | None:
    hold_frames = max(2, int(math.ceil(hold_s * fps)))
    first_frame = max(hold_frames - 1, int(math.ceil(min_elapsed_s * fps)))
    for frame in range(first_frame, len(states)):
        window = states[frame - hold_frames + 1 : frame + 1]
        inlier_frames = np.all((window >= lower) & (window <= upper), axis=1)
        median_state = np.median(window, axis=0)
        p90_deviation = np.quantile(np.abs(window - median_state), 0.9, axis=0)
        if (
            np.mean(inlier_frames) >= minimum_terminal_inlier_fraction
            and np.all(median_state >= lower)
            and np.all(median_state <= upper)
            and np.all(p90_deviation <= max_p90_deviation)
        ):
            return frame
    return None


def analyze(
    dataset_root: Path,
    *,
    terminal_window_s: float,
    endpoint_quantile: float,
    hold_s: float,
    min_elapsed_s: float,
) -> dict:
    info = json.loads((dataset_root / "meta/info.json").read_text(encoding="utf-8"))
    fps = float(info["fps"])
    feature = info["features"]["observation.state"]
    state_dim = int(feature["shape"][0])
    names_value = feature.get("names")
    joint_names = names_value[0] if names_value and isinstance(names_value[0], list) else names_value
    if not joint_names:
        joint_names = [f"joint_{index}" for index in range(state_dim)]

    parquet_files = sorted(dataset_root.glob("data/chunk-*/file-*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No LeRobot parquet files found under {dataset_root}")
    frame_table = pd.concat(
        [pd.read_parquet(path, columns=["episode_index", "frame_index", "observation.state"]) for path in parquet_files],
        ignore_index=True,
    )

    terminal_frames = max(2, int(round(terminal_window_s * fps)))
    episodes: list[tuple[int, np.ndarray]] = []
    endpoint_centers: list[np.ndarray] = []
    endpoint_ranges: list[np.ndarray] = []
    endpoint_p90_deviations: list[np.ndarray] = []
    lengths: list[int] = []
    for episode_index, group in frame_table.groupby("episode_index", sort=True):
        group = group.sort_values("frame_index")
        states = np.stack(group["observation.state"].to_numpy()).astype(np.float64)
        if states.ndim != 2 or states.shape[1] != state_dim:
            raise ValueError(
                f"episode {episode_index} state shape {states.shape} does not match expected (*, {state_dim})"
            )
        tail = states[-min(terminal_frames, len(states)) :]
        episodes.append((int(episode_index), states))
        endpoint_center = np.median(tail, axis=0)
        endpoint_centers.append(endpoint_center)
        endpoint_ranges.append(np.ptp(tail, axis=0))
        endpoint_p90_deviations.append(
            np.quantile(np.abs(tail - endpoint_center), 0.9, axis=0)
        )
        lengths.append(len(states))

    centers = np.stack(endpoint_centers)
    ranges = np.stack(endpoint_ranges)
    p90_deviations = np.stack(endpoint_p90_deviations)
    moving_limit = np.quantile(ranges, 0.95, axis=0)
    stable_endpoint_mask = np.all(ranges <= moving_limit, axis=1)
    stable_centers = centers[stable_endpoint_mask]
    stable_p90_deviations = p90_deviations[stable_endpoint_mask]
    if len(stable_centers) < max(10, int(0.25 * len(centers))):
        raise RuntimeError("Too few stable episode endpoints to derive a terminal-pose detector")

    lower = np.quantile(stable_centers, endpoint_quantile, axis=0)
    upper = np.quantile(stable_centers, 1.0 - endpoint_quantile, axis=0)
    center = np.median(stable_centers, axis=0)
    # Robust p90 deviations tolerate occasional action-model twitches. These
    # floors intentionally exceed quiet demonstration noise to accommodate the
    # observed real-robot endpoint oscillation.
    default_floors = np.array([0.04, 0.02, 0.04, 0.05, 0.03, 0.04], dtype=np.float64)
    if state_dim != len(default_floors):
        default_floors = np.full(state_dim, 0.03, dtype=np.float64)
    max_p90_deviation = np.maximum(
        np.quantile(stable_p90_deviations, 0.95, axis=0),
        default_floors,
    )
    minimum_terminal_inlier_fraction = 0.9

    detections: list[dict] = []
    for episode_index, states in episodes:
        frame = _first_detection(
            states,
            fps=fps,
            lower=lower,
            upper=upper,
            max_p90_deviation=max_p90_deviation,
            hold_s=hold_s,
            min_elapsed_s=min_elapsed_s,
            minimum_terminal_inlier_fraction=minimum_terminal_inlier_fraction,
        )
        if frame is not None:
            detections.append(
                {
                    "episode_index": episode_index,
                    "frame_index": int(frame),
                    "seconds_before_episode_end": round(float((len(states) - 1 - frame) / fps), 4),
                }
            )

    return {
        "schema_version": 1,
        "detector_type": "terminal_joint_pose_hold",
        "source": {
            "dataset_root": str(dataset_root),
            "episodes": len(episodes),
            "frames": int(sum(lengths)),
            "fps": fps,
            "terminal_window_s": terminal_window_s,
            "terminal_window_frames": terminal_frames,
            "stable_endpoint_episodes": int(stable_endpoint_mask.sum()),
            "endpoint_quantile": endpoint_quantile,
        },
        "joint_names": list(joint_names),
        "reference_center": _as_floats(center),
        "lower_bounds": _as_floats(lower),
        "upper_bounds": _as_floats(upper),
        "max_p90_abs_deviation": _as_floats(max_p90_deviation),
        "hold_duration_s": hold_s,
        "min_episode_elapsed_s": min_elapsed_s,
        "minimum_sample_fraction": 0.8,
        "minimum_terminal_inlier_fraction": minimum_terminal_inlier_fraction,
        "analysis": {
            "episode_length_frames": {
                "min": int(np.min(lengths)),
                "median": float(np.median(lengths)),
                "max": int(np.max(lengths)),
            },
            "training_replay_detections": len(detections),
            "training_replay_detection_fraction": round(len(detections) / len(episodes), 6),
            "detections": detections,
            "note": (
                "This is a joint-pose heuristic, not visual proof that the cup is in the hand. "
                "Stable failure poses outside the learned terminal bounds do not trigger it."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--terminal-window-s", type=float, default=0.5)
    parser.add_argument("--endpoint-quantile", type=float, default=0.05)
    parser.add_argument("--hold-s", type=float, default=2.0)
    parser.add_argument("--min-elapsed-s", type=float, default=3.0)
    args = parser.parse_args()
    if not 0.0 < args.endpoint_quantile < 0.5:
        parser.error("--endpoint-quantile must be between 0 and 0.5")
    if args.terminal_window_s <= 0 or args.hold_s <= 0 or args.min_elapsed_s < 0:
        parser.error("window/hold must be positive and min elapsed must be non-negative")

    result = analyze(
        args.dataset_root.resolve(),
        terminal_window_s=args.terminal_window_s,
        endpoint_quantile=args.endpoint_quantile,
        hold_s=args.hold_s,
        min_elapsed_s=args.min_elapsed_s,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_keys = (
        "source",
        "joint_names",
        "reference_center",
        "lower_bounds",
        "upper_bounds",
        "max_p90_abs_deviation",
        "hold_duration_s",
        "min_episode_elapsed_s",
        "minimum_terminal_inlier_fraction",
    )
    print(
        json.dumps(
            {key: result[key] for key in summary_keys},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"Wrote detector config: {args.output}")


if __name__ == "__main__":
    main()
