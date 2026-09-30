#!/usr/bin/env python3
"""Create plots and a concise report for the FastWAM sorting run."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path("/home/igs/Desktop/project/vla/unitree_lerobot_yth")
RUN = Path(
    "/skydata/syh/FastWAM/runs/"
    "pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/"
    "2026-08-31_17-41-07"
)
OUTPUT = WORKSPACE / "outputs/fastwam_sorting_offline_analysis/step_020000_live_snapshots"
ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x1b]*(?:\x1b\\|\x07))")


def parse_training_log() -> tuple[np.ndarray, np.ndarray]:
    log = RUN / "wandb/run-20260831_174542-dmfecuba/files/output.log"
    text = ANSI.sub("", log.read_text(encoding="utf-8", errors="replace"))
    text = " ".join(text.split())
    # Rich applies separate ANSI spans to the integer and fractional portions,
    # leaving whitespace such as ``loss=3 .8531`` after escape-code removal.
    text = re.sub(r"(?<=\d)\s+(?=\.)", "", text)
    train_pattern = re.compile(
        r"epoch=(\d+) step=(\d+)/20000.*?loss=([0-9.eE+-]+).*?"
        r"loss_action=([0-9.eE+-]+).*?loss_video=([0-9.eE+-]+).*?lr=([0-9.eE+-]+).*?speed="
    )
    val_pattern = re.compile(
        r"step=(\d+) val_loss=([0-9.eE+-]+).*?action_l2=([0-9.eE+-]+) "
        r"action_l1=([0-9.eE+-]+)"
    )
    train = np.asarray(
        [[int(m[1]), float(m[2]), float(m[3]), float(m[4]), float(m[5])] for m in train_pattern.findall(text)],
        dtype=np.float64,
    )
    val = np.asarray(
        [[int(m[0]), float(m[1]), float(m[2]), float(m[3])] for m in val_pattern.findall(text)],
        dtype=np.float64,
    )
    if train.size == 0 or val.size == 0:
        raise RuntimeError(f"Could not parse training log: train={train.shape}, val={val.shape}")
    return train, val


def moving_average(values: np.ndarray, width: int = 40) -> np.ndarray:
    if len(values) < width:
        return values
    kernel = np.ones(width) / width
    valid = np.convolve(values, kernel, mode="valid")
    return np.concatenate([np.full(width - 1, np.nan), valid])


def plot_training(train: np.ndarray, val: np.ndarray) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=False)
    axes[0].plot(train[:, 0], moving_average(train[:, 2]), label="action loss (40-log moving avg)")
    axes[0].plot(train[:, 0], moving_average(train[:, 3]), label="video loss (40-log moving avg)")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("training loss (log scale)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(val[:, 0], val[:, 1], marker="o", markersize=3, label="val loss")
    axes[1].plot(val[:, 0], val[:, 3], marker="o", markersize=3, label="action L1 (rad)")
    axes[1].set_xlabel("training step")
    axes[1].set_ylabel("single sampled eval per GPU")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    fig.suptitle("FastWAM sorting training history")
    fig.tight_layout()
    fig.savefig(OUTPUT / "training_curves.png", dpi=180)
    plt.close(fig)


def plot_counterfactuals(payload: dict) -> None:
    results = payload["results"]
    image_names = ["box_image", "bag_image"]
    state_names = [
        "box_live_state", "bag_live_state", "left_train_prototype",
        "right_train_prototype", "neutral_train_prototype",
    ]
    matrix = np.asarray([
        [results[f"{image}__{state}"]["right_minus_left_score"] for state in state_names]
        for image in image_names
    ])
    limit = float(np.max(np.abs(matrix)))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    image = ax.imshow(matrix, cmap="coolwarm", vmin=-limit, vmax=limit, aspect="auto")
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            ax.text(col, row, f"{matrix[row, col]:+.3f}\n{'R' if matrix[row, col] > 0 else 'L'}", ha="center", va="center")
    ax.set_xticks(range(len(state_names)), [name.replace("_", "\n") for name in state_names])
    ax.set_yticks(range(2), ["box image\n(expected R)", "black-bag image\n(expected L)"])
    ax.set_title("Fixed-noise image × robot-state counterfactuals")
    fig.colorbar(image, ax=ax, label="right motion − left motion (rad RMS)")
    fig.tight_layout()
    fig.savefig(OUTPUT / "image_state_counterfactual_matrix.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, val = parse_training_log()
    results_path = OUTPUT / "counterfactual_results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    plot_training(train, val)
    plot_counterfactuals(payload)

    segments = [(0, 1000), (1000, 5000), (5000, 10000), (10000, 15000), (15000, 20000)]
    segment_means = []
    for low, high in segments:
        selected = train[(train[:, 0] > low) & (train[:, 0] <= high)]
        segment_means.append({
            "steps": f"{low + 1}-{high}",
            "action_loss_mean": float(selected[:, 2].mean()),
            "video_loss_mean": float(selected[:, 3].mean()),
        })
    summary = json.loads((RUN / "wandb/run-20260831_174542-dmfecuba/files/wandb-summary.json").read_text())
    numeric = payload["results"]
    image_effect_at_box_state = (
        numeric["box_image__box_live_state"]["right_minus_left_score"]
        - numeric["bag_image__box_live_state"]["right_minus_left_score"]
    )
    image_effect_at_bag_state = (
        numeric["box_image__bag_live_state"]["right_minus_left_score"]
        - numeric["bag_image__bag_live_state"]["right_minus_left_score"]
    )
    state_effect_for_box_image = (
        numeric["box_image__bag_live_state"]["right_minus_left_score"]
        - numeric["box_image__box_live_state"]["right_minus_left_score"]
    )
    state_effect_for_bag_image = (
        numeric["bag_image__bag_live_state"]["right_minus_left_score"]
        - numeric["bag_image__box_live_state"]["right_minus_left_score"]
    )
    analysis = {
        "training_records": int(len(train)),
        "validation_records": int(len(val)),
        "training_segment_means": segment_means,
        "final_metrics": {
            "step": int(summary["_step"]),
            "train_action_loss": summary["train/loss_action"],
            "train_video_loss": summary["train/loss_video"],
            "val_loss": summary["eval/val_loss"],
            "action_l1_rad": summary["eval/action_l1"],
            "action_l2": summary["eval/action_l2"],
        },
        "causal_score_differences": {
            "image_box_minus_bag_at_box_live_state": image_effect_at_box_state,
            "image_box_minus_bag_at_bag_live_state": image_effect_at_bag_state,
            "state_bag_minus_box_for_box_image": state_effect_for_box_image,
            "state_bag_minus_box_for_bag_image": state_effect_for_bag_image,
        },
    }
    (OUTPUT / "analysis_summary.json").write_text(json.dumps(analysis, indent=2) + "\n")

    report = f"""# FastWAM sorting run and live-snapshot analysis

Date: 2026-09-01

## Training audit

- Run: `{RUN}`
- Evaluated checkpoint: `checkpoints/weights/step_020000.pt`
- Training reached the configured 20,000 steps (about epoch 6), with no interruption or NaN evidence.
- Data split: 0824 has 167 train / 19 validation episodes; all 3 episodes from 0828 are train-only. The validation set therefore does **not** test generalization to 0828.
- Train/validation window counts logged by the trainer: 47,961 / 3,795.
- Final logged action training loss: {summary['train/loss_action']:.6f}; final video loss: {summary['train/loss_video']:.6f}.
- Final sampled validation action L1: {summary['eval/action_l1']:.6f} rad; L2: {summary['eval/action_l2']:.6f}.
- The trainer evaluates one random window per GPU at each evaluation point (two windows total here), so the validation curve is high variance and is not a dataset-wide validation mean.

The action loss mean fell from {segment_means[0]['action_loss_mean']:.4f} in steps 1-1000 to {segment_means[-1]['action_loss_mean']:.4f} in steps 15001-20000. This is healthy in-distribution fitting, but it cannot by itself rule out a state shortcut.

## Snapshot provenance and metric

Both inputs are saved **real-robot snapshots**, not training samples:

- Box: PI0.5 live-run inference 1; correct arm is right.
- Black bag: the same live run at inference 9, after the robot had already moved its right arm; correct arm is left.

For each predicted 32-frame chunk, the score is mean right-arm target displacement minus mean left-arm target displacement from the supplied state. Positive means right, negative means left. The within-chunk-motion metric independently gives the same branch conclusions.

## Main result

- Box image + its live state: **right**, score {numeric['box_image__box_live_state']['right_minus_left_score']:+.3f} (correct).
- Black-bag image + box live state: **left**, score {numeric['bag_image__box_live_state']['right_minus_left_score']:+.3f} (correct).
- Box image with either left/right training prototype: always **right**.
- Black-bag image with either left/right training prototype: always **left**.
- Black-bag image + its later live state: **right**, score {numeric['bag_image__bag_live_state']['right_minus_left_score']:+.3f} (wrong), and all 3 noise seeds choose right.

Therefore FastWAM is **not simply ignoring the image**: around normal starting states, swapping only the image reliably swaps the selected arm. It is materially better than the previously tested PI0.5 behavior. However, the left/right problem is **not fully removed**. Once the state looks like an already active right-arm trajectory, it overrides the black-bag visual evidence and the model continues/selects right-arm motion.

This matches the data-collection shortcut: left-task trajectories keep the right arm fixed and right-task trajectories keep the left arm fixed. Because FastWAM trains on windows throughout each episode, current arm pose reveals which branch the demonstration belongs to. The model has learned both image semantics and that state correlation; the latter becomes dominant away from the normal initial-state region.

## Files

- `training_curves.png`: convergence and noisy sampled validation history.
- `image_state_counterfactual_matrix.png`: fixed-noise image/state causal matrix.
- `counterfactual_results.json`: all numeric outputs, seeds, latencies and snapshot paths.
- `box_live_snapshot.jpg`, `black_bag_live_snapshot.jpg`: exact tested images.
"""
    (OUTPUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
