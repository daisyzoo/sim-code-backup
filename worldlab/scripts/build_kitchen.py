#!/usr/bin/env python3
"""Build with .venv-tools/bin/python; never imports or starts Isaac Sim."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from worldlab.assets import build, load_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = build(load_config(args.config), args.force)
    print("Built", result["config"]["output"], "splats:", result["audit"]["count"])
