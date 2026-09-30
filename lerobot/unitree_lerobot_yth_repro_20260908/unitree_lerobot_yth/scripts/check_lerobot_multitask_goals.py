#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from lerobot.datasets.lerobot_dataset import LeRobotDataset


@dataclass(frozen=True)
class Rule:
    episode_start: int
    episode_end: int
    expected_task: str


DEFAULT_RULES = [
    Rule(episode_start=0, episode_end=67, expected_task="Dock the cup with the left hand."),
    Rule(episode_start=68, episode_end=9999, expected_task="Dock the bottle with the right hand."),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether multitask goals are correct in a LeRobot dataset.")
    parser.add_argument(
        "--repo-id",
        required=True,
        help="LeRobot dataset repo id, for example local/g1_23_dual_hand_dock_multitask_11d",
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="LeRobot dataset root directory.",
    )
    return parser.parse_args()


def match_rule(episode_index: int) -> Rule | None:
    for rule in DEFAULT_RULES:
        if rule.episode_start <= episode_index <= rule.episode_end:
            return rule
    return None


def main() -> None:
    args = parse_args()
    dataset = LeRobotDataset(repo_id=args.repo_id, root=args.root)

    mismatches: list[str] = []
    task_counts: dict[str, int] = {}

    for episode_index in range(dataset.num_episodes):
        from_idx = int(dataset.meta.episodes["dataset_from_index"][episode_index])
        step = dataset[from_idx]
        actual_task = str(step["task"])
        task_counts[actual_task] = task_counts.get(actual_task, 0) + 1

        rule = match_rule(episode_index)
        if rule is None:
            continue

        if actual_task != rule.expected_task:
            mismatches.append(
                f"episode {episode_index}: expected '{rule.expected_task}' but got '{actual_task}'"
            )

    print(f"dataset episodes: {dataset.num_episodes}")
    print("task counts:")
    for task, count in sorted(task_counts.items()):
        print(f"  {count:4d}  {task}")

    if mismatches:
        print("mismatches:")
        for line in mismatches[:20]:
            print(f"  {line}")
        raise SystemExit(1)

    print("goal check passed")


if __name__ == "__main__":
    main()
