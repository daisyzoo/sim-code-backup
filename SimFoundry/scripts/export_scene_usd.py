#!/usr/bin/env python3
"""Export layout.json to twin/scene.usda (no Isaac required)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simfoundry.scene_bridge.usda import export_usda
from simfoundry.scene_package import load_named_scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-id", default="kitchen_counter_placeholder")
    parser.add_argument("--out", default=None, help="USDA path. Default: scenes/<id>/twin/scene.usda")
    args = parser.parse_args()
    package = load_named_scene(args.scene_id)
    dest = export_usda(package, args.out)
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
