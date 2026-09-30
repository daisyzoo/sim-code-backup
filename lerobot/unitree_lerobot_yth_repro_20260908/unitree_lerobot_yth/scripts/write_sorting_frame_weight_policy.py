#!/usr/bin/env python3
"""Write meta/sorting_frame_weight_policy.json for a sorting LeRobot dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEROBOT_SRC = REPO_ROOT / "unitree_lerobot/lerobot/src"
sys.path.insert(0, str(LEROBOT_SRC))

from lerobot.utils.sorting_frame_weights import DEFAULT_POLICY, POLICY_FILENAME  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lerobot-root", type=Path, required=True)
    parser.add_argument("--unitree-root", type=Path, required=True)
    args = parser.parse_args()

    episode_tasks: dict[str, str] = {}
    for ep_dir in sorted(args.unitree_root.glob("episode_*")):
        ep = int(ep_dir.name.split("_")[1])
        payload = json.loads((ep_dir / "data.json").read_text(encoding="utf-8"))
        task_id = payload["info"]["simfoundry"]["task_id"]
        episode_tasks[str(ep)] = task_id

    policy = dict(DEFAULT_POLICY)
    policy["episode_tasks"] = episode_tasks
    policy["source_unitree"] = str(args.unitree_root.resolve())
    policy["lerobot_root"] = str(args.lerobot_root.resolve())

    out = args.lerobot_root / "meta" / POLICY_FILENAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(policy, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(episode_tasks)} episodes)")


if __name__ == "__main__":
    main()
