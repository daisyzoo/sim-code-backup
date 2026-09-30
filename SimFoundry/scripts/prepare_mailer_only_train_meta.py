#!/usr/bin/env python3
"""Build mailer-only split + stats for PI0.5 routing ablation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATASET_ROOT = Path(
    "/home/user/Documents/zoo/sim/lerobot/lerobot_sim_sorting_vla_officialhand_inactivepark_300_r2_20260921"
)


def main() -> None:
    split = json.loads((DATASET_ROOT / "meta/train_validation_split.json").read_text(encoding="utf-8"))
    policy = json.loads((DATASET_ROOT / "meta/sorting_frame_weight_policy.json").read_text(encoding="utf-8"))
    ep_task = policy["episode_tasks"]
    mailer_train = [ep for ep in split["train"] if ep_task[str(ep)] == "nudge_mailer_to_bin"]
    mailer_val = [ep for ep in split["validation"] if ep_task[str(ep)] == "nudge_mailer_to_bin"]

    mailer_split = {
        "schema_version": 1,
        "grouping": "mailer_only_ablation",
        "train": mailer_train,
        "validation": mailer_val,
        "source": str(DATASET_ROOT),
    }
    out_split = DATASET_ROOT / "meta/mailer_only_train_episodes.json"
    out_split.write_text(json.dumps(mailer_split, indent=2) + "\n", encoding="utf-8")

    df = pd.read_parquet(DATASET_ROOT / "data/chunk-000/file-000.parquet")
    sub = df[df.episode_index.isin(mailer_train)]
    stats = {}
    for key in ("observation.state", "action"):
        arr = np.stack(sub[key].to_numpy())
        stats[key] = {
            "min": arr.min(axis=0).tolist(),
            "max": arr.max(axis=0).tolist(),
            "mean": arr.mean(axis=0).tolist(),
            "std": arr.std(axis=0).tolist(),
            "count": [int(len(arr))],
            "q01": np.quantile(arr, 0.01, axis=0).tolist(),
            "q99": np.quantile(arr, 0.99, axis=0).tolist(),
        }
    payload = {"episode_indices": mailer_train, **stats}
    out_stats = DATASET_ROOT / "meta/mailer_only_train_stats.json"
    out_stats.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"mailer train eps={len(mailer_train)} frames={len(sub)} val mailer eps={len(mailer_val)}")
    print(f"wrote {out_split}")
    print(f"wrote {out_stats}")


if __name__ == "__main__":
    main()
