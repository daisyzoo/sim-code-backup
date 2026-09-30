#!/usr/bin/env python3
"""Check PI0.5 sorting predictions on exact training-set inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import torch

from analyze_pi05_sorting_snapshot_attribution import OfflinePolicy, action_metric
from lerobot.datasets.lerobot_dataset import LeRobotDataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path(
            "/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/"
            "pick_cup_sorting_0824"
        ),
    )
    parser.add_argument("--repo-id", default="xr/pick_cup_sorting_0824")
    parser.add_argument(
        "--policy-path",
        type=Path,
        default=Path("/skydata/model/sorting_0828/pretrained_model"),
    )
    parser.add_argument(
        "--tokenizer-path",
        type=Path,
        default=Path(
            "/home/igs/Desktop/project/vla/data/.hf_hub_cache/"
            "models--google--paligemma-3b-pt-224/snapshots/"
            "35e4f46485b4d07967e7e9935bc3786aad50687c"
        ),
    )
    parser.add_argument("--episodes", default="0,1,2,4")
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/sorting_offline_analysis/training_sample_validation"
    ))
    return parser.parse_args()


def tensor_image_to_rgb(image: torch.Tensor) -> np.ndarray:
    array = image.detach().cpu().permute(1, 2, 0).numpy().clip(0.0, 1.0)
    return np.rint(array * 255.0).astype(np.uint8)


def main() -> None:
    args = parse_args()
    episodes = [int(value) for value in args.episodes.split(",")]
    seeds = [int(value) for value in args.seeds.split(",")]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    policy_args = SimpleNamespace(
        dataset_root=args.dataset_root,
        repo_id=args.repo_id,
        policy_path=args.policy_path,
        tokenizer_path=args.tokenizer_path,
        device=args.device,
        num_inference_steps=args.num_inference_steps,
    )
    policy = OfflinePolicy(policy_args)
    dataset = LeRobotDataset(
        repo_id=args.repo_id,
        root=args.dataset_root,
        episodes=episodes,
        video_backend="pyav",
    )

    results = []
    for episode in episodes:
        episode_meta = dataset.meta.episodes[episode]
        start = int(episode_meta["dataset_from_index"])
        end = int(episode_meta["dataset_to_index"])
        item = dataset[start]
        state = item["observation.state"].detach().cpu().numpy().astype(np.float32)
        image_rgb = tensor_image_to_rgb(item["observation.images.color_0"])
        task = str(item["task"])
        count = min(50, end - start)
        true_actions = torch.stack(
            [dataset.hf_dataset[index]["action"] for index in range(start, start + count)]
        ).cpu().numpy().astype(np.float32)
        true_20 = action_metric(true_actions, state, 20)
        true_50 = action_metric(true_actions, state, count)
        expected_branch = true_50["branch"]

        predictions = []
        for seed in seeds:
            predicted = policy.infer(image_rgb, state, task, policy.make_noise(seed))
            compare_count = min(count, len(predicted))
            predictions.append(
                {
                    "seed": seed,
                    "metric_20": action_metric(predicted, state, 20),
                    "metric_50": action_metric(predicted, state, compare_count),
                    "action_mse_50": float(
                        np.mean((predicted[:compare_count] - true_actions[:compare_count]) ** 2)
                    ),
                }
            )

        cv2.imwrite(
            str(args.output_dir / f"episode_{episode:03d}_{expected_branch}.jpg"),
            cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR),
        )
        result = {
            "episode": episode,
            "task": task,
            "expected_branch_from_ground_truth_50": expected_branch,
            "ground_truth_metric_20": true_20,
            "ground_truth_metric_50": true_50,
            "predictions": predictions,
        }
        results.append(result)
        branches = [entry["metric_50"]["branch"] for entry in predictions]
        scores = [entry["metric_50"]["right_minus_left_score"] for entry in predictions]
        print(
            f"episode={episode} truth={expected_branch} pred50={branches} "
            f"scores={[round(value, 5) for value in scores]}"
        )

    summary = {
        "dimension_layout": {
            "left_arm": [0, 1, 2, 3, 4],
            "right_arm": [5, 6, 7, 8, 9],
            "waist_yaw": [10],
        },
        "policy_path": str(args.policy_path),
        "dataset_root": str(args.dataset_root),
        "results": results,
    }
    (args.output_dir / "training_sample_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
