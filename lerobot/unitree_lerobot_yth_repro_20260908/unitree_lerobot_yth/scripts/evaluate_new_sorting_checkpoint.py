#!/usr/bin/env python3
"""Evaluate a merged PI0.5 sorting checkpoint on train and real-robot inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import cv2
import numpy as np
import pyarrow.parquet as pq
import torch
from safetensors import safe_open

from analyze_pi05_sorting_snapshot_attribution import OfflinePolicy, action_metric, load_snapshot
from lerobot.datasets.lerobot_dataset import LeRobotDataset


SHORT_TASK = "Sort packages: place black bags on the left and boxes on the right."
DETAILED_TASK = (
    "Sort the package on the table by type. If it is a black bag, press and hold the bag "
    "down with the left hand, then push it to the left sorting area. If it is a box, "
    "press and hold the box down with the right hand, then push it to the right sorting area."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy-path",
        type=Path,
        default=Path(
            "/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/"
            "pretrained_model"
        ),
    )
    parser.add_argument(
        "--stats-json",
        type=Path,
        default=Path(
            "/skydata/syh/FastWAM/configs/data/stats/"
            "pick_cup_sorting_0824_train_0828_all_11d_absolute.json"
        ),
    )
    parser.add_argument(
        "--dataset-0824",
        type=Path,
        default=Path(
            "/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/"
            "pick_cup_sorting_0824"
        ),
    )
    parser.add_argument(
        "--dataset-0828",
        type=Path,
        default=Path(
            "/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/"
            "pick_cup_sorting_0828"
        ),
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
    parser.add_argument(
        "--box-snapshot",
        type=Path,
        default=Path(
            "outputs/rtc_inference_snapshots/pi05_sorting_11d_15hz/"
            "inference_0001_20260828_114229_054476.json"
        ),
    )
    parser.add_argument(
        "--bag-snapshot",
        type=Path,
        default=Path(
            "outputs/rtc_inference_snapshots/pi05_sorting_11d_15hz/"
            "inference_0009_20260828_114252_677166.json"
        ),
    )
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/sorting_offline_analysis/new_checkpoint_020000"),
    )
    return parser.parse_args()


def tensor_image_to_rgb(image: torch.Tensor) -> np.ndarray:
    array = image.detach().cpu().permute(1, 2, 0).numpy().clip(0.0, 1.0)
    return np.rint(array * 255.0).astype(np.uint8)


def checkpoint_stats(policy_path: Path) -> dict[str, np.ndarray]:
    path = policy_path / "policy_preprocessor_step_2_normalizer_processor.safetensors"
    result: dict[str, np.ndarray] = {}
    with safe_open(path, framework="np") as handle:
        for key in (
            "observation.state.mean",
            "observation.state.std",
            "observation.state.count",
            "action.mean",
            "action.std",
            "action.count",
        ):
            result[key] = np.asarray(handle.get_tensor(key))
    return result


def compare_stats(stats_json: Path, policy_path: Path) -> dict[str, Any]:
    external = json.loads(stats_json.read_text(encoding="utf-8"))
    saved = checkpoint_stats(policy_path)
    comparisons: dict[str, Any] = {
        "external_num_episodes": int(external["num_episodes"]),
        "external_num_transition": int(external["num_transition"]),
        "external_sources": external["sources"],
        "checkpoint_state_count": float(saved["observation.state.count"].item()),
        "checkpoint_action_count": float(saved["action.count"].item()),
    }
    for external_name, checkpoint_prefix in (("state", "observation.state"), ("action", "action")):
        mean = np.asarray(external[external_name]["default"]["global_mean"], dtype=np.float64)
        std = np.asarray(external[external_name]["default"]["global_std"], dtype=np.float64)
        saved_mean = saved[f"{checkpoint_prefix}.mean"].astype(np.float64)
        saved_std = saved[f"{checkpoint_prefix}.std"].astype(np.float64)
        comparisons[external_name] = {
            "max_abs_mean_delta": float(np.max(np.abs(mean - saved_mean))),
            "max_abs_std_delta": float(np.max(np.abs(std - saved_std))),
            "mean_delta_in_external_std_max": float(np.max(np.abs(mean - saved_mean) / std)),
        }
    return comparisons


def infer_seeds(
    policy: OfflinePolicy,
    image_rgb: np.ndarray,
    state: np.ndarray,
    task: str,
    seeds: list[int],
    horizon: int = 50,
) -> list[dict[str, Any]]:
    results = []
    for seed in seeds:
        actions = policy.infer(image_rgb, state, task, policy.make_noise(seed))
        results.append({"seed": seed, **action_metric(actions, state, horizon)})
    return results


def load_dataset_item(dataset: LeRobotDataset, index: int) -> tuple[np.ndarray, np.ndarray, str]:
    item = dataset[index]
    return (
        tensor_image_to_rgb(item["observation.images.color_0"]),
        item["observation.state"].detach().cpu().numpy().astype(np.float32),
        str(item["task"]),
    )


def dataset_episode_case(
    policy: OfflinePolicy,
    dataset: LeRobotDataset,
    episode: int,
    seeds: list[int],
    output_dir: Path,
) -> dict[str, Any]:
    meta = dataset.meta.episodes[episode]
    start, end = int(meta["dataset_from_index"]), int(meta["dataset_to_index"])
    image, state, task = load_dataset_item(dataset, start)
    count = min(50, end - start)
    truth_actions = torch.stack(
        [dataset.hf_dataset[index]["action"] for index in range(start, start + count)]
    ).cpu().numpy().astype(np.float32)
    truth = action_metric(truth_actions, state, count)
    predictions = infer_seeds(policy, image, state, task, seeds, count)
    cv2.imwrite(
        str(output_dir / f"0824_episode_{episode:03d}_{truth['branch']}.jpg"),
        cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
    )
    return {
        "dataset": "0824",
        "episode": episode,
        "frame": 0,
        "task": task,
        "ground_truth": truth,
        "predictions": predictions,
    }


def select_0828_cases(root: Path, per_branch: int = 4) -> list[dict[str, Any]]:
    paths = sorted((root / "data").glob("*/*.parquet"))
    table = pq.read_table(
        paths, columns=["episode_index", "frame_index", "observation.state", "action"]
    )
    episodes = np.asarray(table["episode_index"], dtype=np.int64)
    frames = np.asarray(table["frame_index"], dtype=np.int64)
    states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
    actions = np.asarray(table["action"].to_pylist(), dtype=np.float32)
    candidates: dict[str, list[dict[str, Any]]] = {"left": [], "right": []}
    for episode in np.unique(episodes):
        indices = np.flatnonzero(episodes == episode)
        indices = indices[np.argsort(frames[indices])]
        for offset in range(0, max(0, len(indices) - 50), 15):
            index = int(indices[offset])
            future = indices[offset : offset + 50]
            metric = action_metric(actions[future], states[index], 50)
            if abs(metric["right_minus_left_score"]) < 0.12:
                continue
            candidates[metric["branch"]].append(
                {
                    "index": index,
                    "episode": int(episode),
                    "frame": int(frames[index]),
                    "ground_truth": metric,
                    "strength": abs(metric["right_minus_left_score"]),
                }
            )

    selected: list[dict[str, Any]] = []
    for branch in ("left", "right"):
        chosen: list[dict[str, Any]] = []
        for item in sorted(candidates[branch], key=lambda value: value["strength"], reverse=True):
            if any(
                item["episode"] == prior["episode"]
                and abs(item["frame"] - prior["frame"]) < 450
                for prior in chosen
            ):
                continue
            chosen.append(item)
            if len(chosen) == per_branch:
                break
        selected.extend(chosen)
    return sorted(selected, key=lambda item: (item["episode"], item["frame"]))


def main() -> None:
    args = parse_args()
    seeds = [int(value) for value in args.seeds.split(",")]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stats_comparison = compare_stats(args.stats_json, args.policy_path)
    print("Stats comparison:", json.dumps(stats_comparison, ensure_ascii=False))

    policy_args = SimpleNamespace(
        dataset_root=args.dataset_0824,
        repo_id="xr/pick_cup_sorting_0824",
        policy_path=args.policy_path,
        tokenizer_path=args.tokenizer_path,
        device=args.device,
        num_inference_steps=args.num_inference_steps,
    )
    policy = OfflinePolicy(policy_args)

    dataset_0824 = policy.dataset
    train_cases = [
        dataset_episode_case(policy, dataset_0824, episode, seeds, args.output_dir)
        for episode in (0, 1, 2, 4)
    ]

    dataset_0828 = LeRobotDataset(
        repo_id="xr/pick_cup_sorting_0828",
        root=args.dataset_0828,
        episodes=[0, 1, 2],
        video_backend="pyav",
    )
    for case in select_0828_cases(args.dataset_0828):
        image, state, task = load_dataset_item(dataset_0828, case["index"])
        predictions = infer_seeds(policy, image, state, task, seeds, 50)
        cv2.imwrite(
            str(
                args.output_dir
                / f"0828_episode_{case['episode']:03d}_frame_{case['frame']:05d}_"
                f"{case['ground_truth']['branch']}.jpg"
            ),
            cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
        )
        train_cases.append(
            {
                "dataset": "0828",
                "episode": case["episode"],
                "frame": case["frame"],
                "task": task,
                "ground_truth": case["ground_truth"],
                "predictions": predictions,
            }
        )

    snapshots = {}
    loaded_snapshots = {}
    for name, path, expected in (
        ("box", args.box_snapshot, "right"),
        ("black_bag", args.bag_snapshot, "left"),
    ):
        metadata, state, image = load_snapshot(path)
        loaded_snapshots[name] = (state, image)
        snapshots[name] = {
            "snapshot": str(path),
            "expected_branch": expected,
            "short_task": infer_seeds(policy, image, state, SHORT_TASK, seeds),
            "detailed_task": infer_seeds(policy, image, state, DETAILED_TASK, seeds),
        }

    box_state, box_image = loaded_snapshots["box"]
    bag_state, bag_image = loaded_snapshots["black_bag"]
    snapshots["cross_state"] = {
        "box_image_with_bag_time_state": infer_seeds(
            policy, box_image, bag_state, DETAILED_TASK, seeds
        ),
        "bag_image_with_box_time_state": infer_seeds(
            policy, bag_image, box_state, DETAILED_TASK, seeds
        ),
    }

    correct = 0
    total = 0
    for case in train_cases:
        truth = case["ground_truth"]["branch"]
        branches = [prediction["branch"] for prediction in case["predictions"]]
        correct += sum(branch == truth for branch in branches)
        total += len(branches)
        print(
            f"train {case['dataset']} ep={case['episode']} frame={case['frame']} "
            f"truth={truth} pred={branches}"
        )
    for name in ("box", "black_bag"):
        print(
            f"snapshot {name} expected={snapshots[name]['expected_branch']} "
            f"short={[x['branch'] for x in snapshots[name]['short_task']]} "
            f"detailed={[x['branch'] for x in snapshots[name]['detailed_task']]}"
        )

    summary = {
        "policy_path": str(args.policy_path),
        "stats_json": str(args.stats_json),
        "stats_comparison": stats_comparison,
        "training_cases": train_cases,
        "training_branch_accuracy": {"correct": correct, "total": total},
        "real_robot_snapshots": snapshots,
    }
    (args.output_dir / "evaluation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
