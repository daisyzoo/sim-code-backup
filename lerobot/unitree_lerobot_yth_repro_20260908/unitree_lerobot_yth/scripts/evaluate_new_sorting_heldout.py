#!/usr/bin/env python3
"""Evaluate sorting hand selection on all 0824 episodes excluded by the split JSON."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow.parquet as pq

from analyze_pi05_sorting_snapshot_attribution import OfflinePolicy, action_metric
from evaluate_new_sorting_checkpoint import infer_seeds, load_dataset_item
from lerobot.datasets.lerobot_dataset import LeRobotDataset


POLICY = Path(
    "/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/pretrained_model"
)
DATASET = Path(
    "/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/pick_cup_sorting_0824"
)
STATS = Path(
    "/skydata/syh/FastWAM/configs/data/stats/"
    "pick_cup_sorting_0824_train_0828_all_11d_absolute.json"
)
TOKENIZER = Path(
    "/home/igs/Desktop/project/vla/data/.hf_hub_cache/"
    "models--google--paligemma-3b-pt-224/snapshots/"
    "35e4f46485b4d07967e7e9935bc3786aad50687c"
)
OUTPUT = Path("outputs/sorting_offline_analysis/new_checkpoint_020000/heldout_0824.json")
SEEDS = [20260828, 20260829, 20260830]


def main() -> None:
    split = json.loads(STATS.read_text(encoding="utf-8"))
    train_episodes = set(split["sources"][0]["episodes"])
    heldout = sorted(set(range(186)) - train_episodes)

    table = pq.read_table(
        sorted((DATASET / "data").glob("*/*.parquet")),
        columns=["episode_index", "frame_index", "observation.state", "action"],
    )
    episode_ids = np.asarray(table["episode_index"], dtype=np.int64)
    frame_ids = np.asarray(table["frame_index"], dtype=np.int64)
    states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
    actions = np.asarray(table["action"].to_pylist(), dtype=np.float32)

    policy_args = SimpleNamespace(
        dataset_root=DATASET,
        repo_id="xr/pick_cup_sorting_0824",
        policy_path=POLICY,
        tokenizer_path=TOKENIZER,
        device="cuda:0",
        num_inference_steps=10,
    )
    policy = OfflinePolicy(policy_args)
    dataset = LeRobotDataset(
        repo_id="xr/pick_cup_sorting_0824",
        root=DATASET,
        episodes=heldout,
        video_backend="pyav",
    )

    results = []
    correct = total = 0
    for episode in heldout:
        indices = np.flatnonzero(episode_ids == episode)
        indices = indices[np.argsort(frame_ids[indices])]
        candidates = []
        for offset in range(max(1, len(indices) - 49)):
            future = indices[offset : offset + 50]
            if len(future) < 50:
                continue
            metric = action_metric(actions[future], states[future[0]], 50)
            candidates.append((abs(metric["right_minus_left_score"]), int(future[0]), metric))
        _, index, truth = max(candidates, key=lambda value: value[0])
        image, state, task = load_dataset_item(dataset, index)
        predictions = infer_seeds(policy, image, state, task, SEEDS, 50)
        branches = [entry["branch"] for entry in predictions]
        correct += sum(branch == truth["branch"] for branch in branches)
        total += len(branches)
        result = {
            "episode": episode,
            "frame": int(frame_ids[index]),
            "ground_truth": truth,
            "predictions": predictions,
        }
        results.append(result)
        print(
            f"heldout ep={episode} frame={frame_ids[index]} truth={truth['branch']} "
            f"truth_score={truth['right_minus_left_score']:+.4f} pred={branches} "
            f"scores={[round(x['right_minus_left_score'], 4) for x in predictions]}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "policy": str(POLICY),
                "split_stats": str(STATS),
                "heldout_episodes": heldout,
                "accuracy": {"correct": correct, "total": total},
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"heldout accuracy={correct}/{total} ({correct / total:.1%})")


if __name__ == "__main__":
    main()
