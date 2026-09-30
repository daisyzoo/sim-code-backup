# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Approve or drop stage-5 detections before upsample.

Auto mode keeps objects that s5 marked is_valid_removed_obj=true. Pass --interactive
to open the 5b GUI first, then rewrite the keep list from the (possibly edited) JSONs.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from omegaconf import OmegaConf

from simfoundry import CFG_DIR, REPO_DIR
from simfoundry.pipeline.object_filter import (
    list_s5_objects,
    resolve_keep_indices,
    sync_object_filter_from_s5,
    write_object_filter,
)

logger = logging.getLogger(__name__)


def _scene_s5_dir(overrides: list[str]) -> Path:
    cfg = OmegaConf.load(Path(CFG_DIR) / "real2sim_cfg.yaml")
    dotlist = [item for item in overrides if "=" in item]
    if dotlist:
        cfg = OmegaConf.merge(cfg, OmegaConf.from_dotlist(dotlist))
    return Path(str(cfg.s5_scene.out_dir))


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true", help="Open 5b_visualize_decomposition.py first")
    parser.add_argument("--include-invalid", action="store_true", help="Keep every detection, including invalid ones")
    parser.add_argument("overrides", nargs="*", help="Hydra overrides, e.g. scene_name=fruits_demo")
    args = parser.parse_args()

    s5_dir = _scene_s5_dir(args.overrides)
    if args.interactive:
        script = Path(REPO_DIR) / "scripts/pipeline/A_reconstruction/stages/5b_visualize_decomposition.py"
        cmd = [sys.executable, str(script), *args.overrides]
        logger.info("Launching interactive reviewer: %s", " ".join(cmd))
        subprocess.run(cmd, check=True, cwd=str(REPO_DIR))

    records = list_s5_objects(s5_dir)
    if not records:
        raise SystemExit(f"No stage-5 objects found in {s5_dir}/obj_cat_list")

    if args.include_invalid:
        keep = [row["idx"] for row in records]
        invalid = [row["idx"] for row in records if not row["is_valid"]]
        payload = write_object_filter(
            s5_dir,
            keep_indices=keep,
            invalid_indices=invalid,
            source="5c_include_invalid",
            approved=True,
        )
    else:
        payload = sync_object_filter_from_s5(s5_dir, source="5c_auto", approved=True)

    logger.info("Wrote %s", s5_dir / "object_filter.json")
    logger.info(
        "keep=%s invalid=%s",
        payload["keep_indices"],
        payload["invalid_indices"],
    )
    for row in records:
        flag = "keep" if row["idx"] in payload["keep_indices"] else "drop"
        validity = "valid" if row["is_valid"] else "invalid"
        logger.info("  iter_%s  %s  %s  %s", row["idx"], flag, validity, row["phrase"])
    # Touch the helper so require_review can see an approved list.
    resolve_keep_indices(s5_dir, include_invalid=args.include_invalid, require_review=True)


if __name__ == "__main__":
    main()
