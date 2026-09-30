#!/usr/bin/env python3
"""Audit whether initial robot state predicts the active arm in sorting data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq


JOINT_NAMES = [
    "left_arm_0",
    "left_arm_1",
    "left_arm_2",
    "left_arm_3",
    "left_arm_4",
    "right_arm_0",
    "right_arm_1",
    "right_arm_2",
    "right_arm_3",
    "right_arm_4",
    "waist_yaw",
]


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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/sorting_offline_analysis/state_shortcut"),
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260828)
    return parser.parse_args()


def load_frames(dataset_root: Path) -> tuple[np.ndarray, ...]:
    paths = sorted((dataset_root / "data").glob("*/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No data parquet files under {dataset_root}")
    table = pq.read_table(
        paths,
        columns=["episode_index", "frame_index", "observation.state", "action"],
    )
    return (
        np.asarray(table["episode_index"], dtype=np.int64),
        np.asarray(table["frame_index"], dtype=np.int64),
        np.asarray(table["observation.state"].to_pylist(), dtype=np.float64),
        np.asarray(table["action"].to_pylist(), dtype=np.float64),
    )


def episode_features(
    episode_index: np.ndarray,
    frame_index: np.ndarray,
    states: np.ndarray,
    actions: np.ndarray,
) -> dict[str, np.ndarray]:
    episode_ids = np.unique(episode_index)
    initial_states = []
    labels = []
    lengths = []
    left_max = []
    right_max = []
    for episode_id in episode_ids:
        indices = np.flatnonzero(episode_index == episode_id)
        indices = indices[np.argsort(frame_index[indices])]
        episode_states = states[indices]
        episode_actions = actions[indices]
        initial = episode_states[0]
        left_motion = np.sqrt(np.mean((episode_actions[:, :5] - initial[:5]) ** 2, axis=1))
        right_motion = np.sqrt(np.mean((episode_actions[:, 5:10] - initial[5:10]) ** 2, axis=1))
        initial_states.append(initial)
        labels.append(int(np.max(right_motion) > np.max(left_motion)))
        lengths.append(len(indices))
        left_max.append(float(np.max(left_motion)))
        right_max.append(float(np.max(right_motion)))
    return {
        "episode_ids": episode_ids,
        "initial_states": np.asarray(initial_states),
        "labels": np.asarray(labels, dtype=np.int64),
        "lengths": np.asarray(lengths),
        "left_max_motion": np.asarray(left_max),
        "right_max_motion": np.asarray(right_max),
    }


def quantize_like_pi05(initial_states: np.ndarray, dataset_root: Path) -> np.ndarray:
    stats = json.loads((dataset_root / "meta" / "stats.json").read_text(encoding="utf-8"))
    state_stats = stats["observation.state"]
    q01 = np.asarray(state_stats["q01"], dtype=np.float64)
    q99 = np.asarray(state_stats["q99"], dtype=np.float64)
    normalized = 2.0 * (initial_states - q01) / np.maximum(q99 - q01, 1e-8) - 1.0
    # This exactly follows Pi05PrepareStateTokenizerProcessorStep. Values are
    # deliberately not clipped before digitization in the current implementation.
    return np.digitize(normalized, bins=np.linspace(-1.0, 1.0, 257)[:-1]) - 1


def stratified_folds(labels: np.ndarray, count: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    folds: list[list[int]] = [[] for _ in range(count)]
    for label in (0, 1):
        indices = np.flatnonzero(labels == label)
        rng.shuffle(indices)
        for offset, index in enumerate(indices):
            folds[offset % count].append(int(index))
    return [np.asarray(sorted(fold), dtype=np.int64) for fold in folds]


def fit_ridge_logistic(features: np.ndarray, labels: np.ndarray, l2: float = 1.0) -> np.ndarray:
    design = np.column_stack([np.ones(len(features)), features])
    weights = np.zeros(design.shape[1], dtype=np.float64)
    penalty = np.eye(design.shape[1], dtype=np.float64) * l2
    penalty[0, 0] = 0.0
    for _ in range(80):
        logits = np.clip(design @ weights, -30.0, 30.0)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        curvature = np.maximum(probabilities * (1.0 - probabilities), 1e-7)
        gradient = design.T @ (probabilities - labels) + penalty @ weights
        hessian = (design.T * curvature) @ design + penalty
        step = np.linalg.solve(hessian, gradient)
        weights -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    return weights


def cross_validated_predictions(
    features: np.ndarray,
    labels: np.ndarray,
    fold_count: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    predictions = np.zeros_like(labels)
    scores = np.zeros(len(labels), dtype=np.float64)
    all_indices = np.arange(len(labels))
    for test_indices in stratified_folds(labels, fold_count, seed):
        train_indices = np.setdiff1d(all_indices, test_indices)
        mean = features[train_indices].mean(axis=0)
        std = features[train_indices].std(axis=0)
        std[std < 1e-8] = 1.0
        train = (features[train_indices] - mean) / std
        test = (features[test_indices] - mean) / std
        weights = fit_ridge_logistic(train, labels[train_indices])
        test_scores = np.column_stack([np.ones(len(test)), test]) @ weights
        scores[test_indices] = test_scores
        predictions[test_indices] = (test_scores >= 0.0).astype(np.int64)
    return predictions, scores


def permutation_test(
    features: np.ndarray,
    labels: np.ndarray,
    fold_count: int,
    seed: int,
    repeats: int = 300,
) -> np.ndarray:
    rng = np.random.default_rng(seed + 1)
    accuracies = []
    for repeat in range(repeats):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        predictions, _ = cross_validated_predictions(
            features,
            shuffled,
            fold_count,
            seed + repeat + 17,
        )
        accuracies.append(float(np.mean(predictions == shuffled)))
    return np.asarray(accuracies)


def make_plot(
    output_path: Path,
    initial_states: np.ndarray,
    quantized_states: np.ndarray,
    labels: np.ndarray,
) -> None:
    left = labels == 0
    right = labels == 1
    raw_scale = np.maximum(initial_states.std(axis=0), 1e-8)
    standardized_difference = (
        initial_states[right].mean(axis=0) - initial_states[left].mean(axis=0)
    ) / raw_scale
    quantized_difference = quantized_states[right].mean(axis=0) - quantized_states[left].mean(axis=0)

    figure, axes = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    colors = ["#d95f02" if value < 0 else "#1b9e77" for value in standardized_difference]
    axes[0].bar(JOINT_NAMES, standardized_difference, color=colors)
    axes[0].axhline(0.0, color="black", linewidth=0.8)
    axes[0].set_ylabel("(right mean - left mean) / initial-state std")
    axes[0].set_title("Initial-state branch separation before any policy action")
    axes[0].tick_params(axis="x", rotation=35)

    colors = ["#d95f02" if value < 0 else "#1b9e77" for value in quantized_difference]
    axes[1].bar(JOINT_NAMES, quantized_difference, color=colors)
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_ylabel("PI0.5 state-token bin difference")
    axes[1].set_title("The separation survives quantile normalization and 256-bin tokenization")
    axes[1].tick_params(axis="x", rotation=35)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    episode_index, frame_index, states, actions = load_frames(args.dataset_root)
    features = episode_features(episode_index, frame_index, states, actions)
    initial_states = features["initial_states"]
    labels = features["labels"]
    quantized = quantize_like_pi05(initial_states, args.dataset_root)

    raw_predictions, _ = cross_validated_predictions(initial_states, labels, args.folds, args.seed)
    token_predictions, _ = cross_validated_predictions(quantized, labels, args.folds, args.seed)
    null_accuracies = permutation_test(quantized, labels, args.folds, args.seed)
    token_accuracy = float(np.mean(token_predictions == labels))
    raw_accuracy = float(np.mean(raw_predictions == labels))
    permutation_p = float((1 + np.sum(null_accuracies >= token_accuracy)) / (1 + len(null_accuracies)))

    left = labels == 0
    right = labels == 1
    summary = {
        "dataset_root": str(args.dataset_root),
        "total_episodes": int(len(labels)),
        "left_arm_episodes": int(np.sum(left)),
        "right_arm_episodes": int(np.sum(right)),
        "episode_length_min": int(features["lengths"].min()),
        "episode_length_median": float(np.median(features["lengths"])),
        "episode_length_max": int(features["lengths"].max()),
        "initial_state_cv_accuracy_raw": raw_accuracy,
        "initial_state_cv_accuracy_pi05_token_bins": token_accuracy,
        "chance_accuracy": float(max(np.mean(left), np.mean(right))),
        "permutation_null_mean": float(null_accuracies.mean()),
        "permutation_null_p95": float(np.quantile(null_accuracies, 0.95)),
        "permutation_p_value": permutation_p,
        "misclassified_episode_ids": features["episode_ids"][token_predictions != labels].tolist(),
        "joint_names": JOINT_NAMES,
        "left_initial_state_mean": initial_states[left].mean(axis=0).tolist(),
        "right_initial_state_mean": initial_states[right].mean(axis=0).tolist(),
        "left_initial_token_bin_mean": quantized[left].mean(axis=0).tolist(),
        "right_initial_token_bin_mean": quantized[right].mean(axis=0).tolist(),
    }
    (args.output_dir / "state_shortcut_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    make_plot(args.output_dir / "initial_state_branch_separation.png", initial_states, quantized, labels)

    report = f"""# Sorting dataset initial-state shortcut audit

- Episodes: {len(labels)} ({np.sum(left)} left-arm, {np.sum(right)} right-arm)
- Majority-class chance accuracy: {summary['chance_accuracy']:.1%}
- 10-fold accuracy from raw frame-0 state only: {raw_accuracy:.1%}
- 10-fold accuracy from the exact PI0.5 256-bin state tokens: {token_accuracy:.1%}
- Permutation null: mean {null_accuracies.mean():.1%}, 95th percentile {np.quantile(null_accuracies, 0.95):.1%}
- Permutation p-value: {permutation_p:.4f}

The label is derived only from which arm has the larger maximum action displacement over
the full episode. The classifier receives only the 11-dimensional observation.state at
frame 0. It receives no image and no future action. Accuracy substantially above the
permutation null means the initial pose contains information about the future arm branch.
"""
    (args.output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"Artifacts: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
