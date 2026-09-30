#!/usr/bin/env python3
"""Regenerate the A-period kitchen scene package from adapter stubs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.adapter.pipeline import build_placeholder_kitchen
from simfoundry.scene_package import filter_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes-root", default=str(ROOT / "scenes"))
    parser.add_argument("--scene-id", default="kitchen_counter_placeholder")
    args = parser.parse_args()
    package = build_placeholder_kitchen(args.scenes_root, scene_id=args.scene_id)
    stump = filter_tasks(package, "stump")
    print(f"wrote {package.root}")
    print(f"objects: {[o.name for o in package.objects]}")
    print(f"stump tasks: {[t.task_id for t in stump]}")
    print(f"filtered out: {[t.task_id for t in package.tasks if t.requires_ee != 'stump']}")


if __name__ == "__main__":
    main()
