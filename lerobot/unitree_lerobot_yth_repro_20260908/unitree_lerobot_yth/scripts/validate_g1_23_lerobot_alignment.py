#!/usr/bin/env python3

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pyarrow.parquet as pq


DEFAULT_PATHS = ["left_arm.qpos", "right_arm.qpos", "body.qpos[0]"]


@dataclass
class EpisodeMismatch:
    episode_index: int
    frame_index: int
    kind: str
    raw_values: list[float]
    converted_values: list[float]
    max_abs_diff: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate raw Unitree JSON episodes against converted LeRobot parquet rows."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("/home/igs/Desktop/project/vla/xr_teleoperate/teleop/utils/data/g1_23_right_hand_rag_reach"),
        help="Directory containing episode_XXXX folders with data.json.",
    )
    parser.add_argument(
        "--lerobot-dir",
        type=Path,
        default=Path("/home/igs/Desktop/project/vla/data/local/g1_23_right_hand_rag_reach_11d"),
        help="Converted LeRobot dataset root.",
    )
    parser.add_argument(
        "--state-paths",
        nargs="+",
        default=DEFAULT_PATHS,
        help="Dot/index paths to extract from raw frame['states'].",
    )
    parser.add_argument(
        "--action-paths",
        nargs="+",
        default=DEFAULT_PATHS,
        help="Dot/index paths to extract from raw frame['actions'].",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-6,
        help="Absolute tolerance for equality checks.",
    )
    parser.add_argument(
        "--max-report",
        type=int,
        default=20,
        help="Maximum number of mismatches to print.",
    )
    return parser.parse_args()


def resolve_path(data: dict, path: str):
    current = data
    for token in path.split("."):
        match = re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?", token)
        if match is None:
            raise ValueError(f"Invalid path token: {token}")
        key, index_str = match.groups()
        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Missing key '{key}' in path '{path}'")
        current = current[key]
        if index_str is not None:
            if not isinstance(current, list):
                raise TypeError(f"Expected list at '{key}' in path '{path}'")
            current = current[int(index_str)]
    return current


def extract_vector(frame: dict, key: str, paths: list[str]) -> np.ndarray:
    values: list[float] = []
    for path in paths:
        resolved = resolve_path(frame[key], path)
        if isinstance(resolved, list):
            values.extend(float(v) for v in resolved)
        else:
            values.append(float(resolved))
    return np.asarray(values, dtype=np.float32)


def load_raw_episodes(raw_dir: Path, state_paths: list[str], action_paths: list[str]) -> list[dict]:
    episode_dirs = sorted(p for p in raw_dir.iterdir() if p.is_dir() and p.name.startswith("episode_"))
    episodes = []
    for episode_dir in episode_dirs:
        data = json.loads((episode_dir / "data.json").read_text(encoding="utf-8"))
        states = []
        actions = []
        for frame in data["data"]:
            states.append(extract_vector(frame, "states", state_paths))
            actions.append(extract_vector(frame, "actions", action_paths))
        episodes.append(
            {
                "name": episode_dir.name,
                "states": np.stack(states) if states else np.empty((0, 0), dtype=np.float32),
                "actions": np.stack(actions) if actions else np.empty((0, 0), dtype=np.float32),
            }
        )
    return episodes


def load_converted_rows(lerobot_dir: Path) -> dict[int, dict[str, np.ndarray]]:
    parquet_path = lerobot_dir / "data" / "chunk-000" / "file-000.parquet"
    table = pq.read_table(parquet_path, columns=["episode_index", "frame_index", "observation.state", "action"])
    rows = table.to_pylist()
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        grouped.setdefault(int(row["episode_index"]), []).append(row)

    converted: dict[int, dict[str, np.ndarray]] = {}
    for episode_index, episode_rows in grouped.items():
        episode_rows.sort(key=lambda row: int(row["frame_index"]))
        converted[episode_index] = {
            "frame_index": np.asarray([int(row["frame_index"]) for row in episode_rows], dtype=np.int64),
            "states": np.asarray([row["observation.state"] for row in episode_rows], dtype=np.float32),
            "actions": np.asarray([row["action"] for row in episode_rows], dtype=np.float32),
        }
    return converted


def compare_episodes(
    raw_episodes: list[dict],
    converted_rows: dict[int, dict[str, np.ndarray]],
    atol: float,
    max_report: int,
) -> int:
    mismatches: list[EpisodeMismatch] = []
    checked_frames = 0

    if len(raw_episodes) != len(converted_rows):
        print(f"Episode count mismatch: raw={len(raw_episodes)} converted={len(converted_rows)}")

    for episode_index, raw_episode in enumerate(raw_episodes):
        if episode_index not in converted_rows:
            mismatches.append(
                EpisodeMismatch(
                    episode_index=episode_index,
                    frame_index=-1,
                    kind="missing_episode",
                    raw_values=[],
                    converted_values=[],
                    max_abs_diff=float("inf"),
                )
            )
            continue

        converted = converted_rows[episode_index]
        raw_states = raw_episode["states"]
        raw_actions = raw_episode["actions"]
        conv_states = converted["states"]
        conv_actions = converted["actions"]

        if raw_states.shape != conv_states.shape:
            mismatches.append(
                EpisodeMismatch(
                    episode_index=episode_index,
                    frame_index=-1,
                    kind="state_shape",
                    raw_values=list(raw_states.shape),
                    converted_values=list(conv_states.shape),
                    max_abs_diff=float("inf"),
                )
            )
            continue

        if raw_actions.shape != conv_actions.shape:
            mismatches.append(
                EpisodeMismatch(
                    episode_index=episode_index,
                    frame_index=-1,
                    kind="action_shape",
                    raw_values=list(raw_actions.shape),
                    converted_values=list(conv_actions.shape),
                    max_abs_diff=float("inf"),
                )
            )
            continue

        for frame_index in range(raw_states.shape[0]):
            checked_frames += 1

            state_diff = np.abs(raw_states[frame_index] - conv_states[frame_index])
            if not np.allclose(raw_states[frame_index], conv_states[frame_index], atol=atol, rtol=0.0):
                mismatches.append(
                    EpisodeMismatch(
                        episode_index=episode_index,
                        frame_index=frame_index,
                        kind="state",
                        raw_values=raw_states[frame_index].tolist(),
                        converted_values=conv_states[frame_index].tolist(),
                        max_abs_diff=float(state_diff.max()),
                    )
                )

            action_diff = np.abs(raw_actions[frame_index] - conv_actions[frame_index])
            if not np.allclose(raw_actions[frame_index], conv_actions[frame_index], atol=atol, rtol=0.0):
                mismatches.append(
                    EpisodeMismatch(
                        episode_index=episode_index,
                        frame_index=frame_index,
                        kind="action",
                        raw_values=raw_actions[frame_index].tolist(),
                        converted_values=conv_actions[frame_index].tolist(),
                        max_abs_diff=float(action_diff.max()),
                    )
                )

            if len(mismatches) >= max_report:
                break

        if len(mismatches) >= max_report:
            break

    print(f"Checked episodes: {len(raw_episodes)}")
    print(f"Checked frames:   {checked_frames}")
    print(f"Reported issues:  {len(mismatches)}")

    if not mismatches:
        print("Validation passed: raw JSON and converted LeRobot rows are aligned.")
        return 0

    for mismatch in mismatches:
        print(
            f"[episode={mismatch.episode_index:04d} frame={mismatch.frame_index:04d} kind={mismatch.kind}] "
            f"max_abs_diff={mismatch.max_abs_diff}"
        )
        if mismatch.raw_values or mismatch.converted_values:
            print(f"  raw:       {mismatch.raw_values}")
            print(f"  converted: {mismatch.converted_values}")

    return 1


def main() -> int:
    args = parse_args()
    raw_episodes = load_raw_episodes(args.raw_dir, args.state_paths, args.action_paths)
    converted_rows = load_converted_rows(args.lerobot_dir)
    return compare_episodes(raw_episodes, converted_rows, args.atol, args.max_report)


if __name__ == "__main__":
    raise SystemExit(main())
