#!/usr/bin/env python3
"""Run fixed-noise FastWAM counterfactuals on two logged sorting snapshots.

The snapshots are from one PI0.5 real-robot run, but this script only reuses
their camera frame and measured 11-D robot state as offline FastWAM inputs.
No robot command is created or published.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image, ImageFilter


JOINT_NAMES = [
    "left_arm_0", "left_arm_1", "left_arm_2", "left_arm_3", "left_arm_4",
    "right_arm_0", "right_arm_1", "right_arm_2", "right_arm_3", "right_arm_4",
    "waist_yaw",
]
TASK = (
    "Sort the package on the table by type. If it is a black bag, press and hold "
    "the bag down with the left hand, then push it to the left sorting area. If it "
    "is a box, press and hold the box down with the right hand, then push it to the "
    "right sorting area."
)


def parse_args() -> argparse.Namespace:
    workspace = Path("/home/igs/Desktop/project/vla/unitree_lerobot_yth")
    run = Path(
        "/skydata/syh/FastWAM/runs/"
        "pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/"
        "2026-08-31_17-41-07"
    )
    snapshots = workspace / "outputs/rtc_inference_snapshots/pi05_sorting_11d_15hz"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastwam-root", type=Path, default=Path("/skydata/syh/FastWAM"))
    parser.add_argument("--run-dir", type=Path, default=run)
    parser.add_argument("--checkpoint", type=Path, default=run / "checkpoints/weights/step_020000.pt")
    parser.add_argument("--box-snapshot", type=Path, default=snapshots / "inference_0001_20260828_114229_054476.json")
    parser.add_argument("--bag-snapshot", type=Path, default=snapshots / "inference_0009_20260828_114252_677166.json")
    parser.add_argument(
        "--state-summary",
        type=Path,
        default=workspace / "outputs/sorting_offline_analysis/state_shortcut/state_shortcut_summary.json",
    )
    parser.add_argument(
        "--text-embedding-cache",
        type=Path,
        default=Path(
            "/skydata/syh/FastWAM/datasets/data/text_embeds_cache/"
            "pick_cup_sorting_first_frame/"
            "740fc050e848971fd5c4ab04d00ecac9b269caa053eeb6d5b52b2a8209cf0a53."
            "t5_len128.wan22ti2v5b.pt"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=workspace / "outputs/fastwam_sorting_offline_analysis/step_020000_live_snapshots",
    )
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--noise-trials", type=int, default=3)
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--action-horizon", type=int, default=32)
    return parser.parse_args()


def load_snapshot(path: Path) -> tuple[dict, np.ndarray, Image.Image]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    state = np.asarray(metadata["observation_state"], dtype=np.float32)
    if state.shape != (11,):
        raise ValueError(f"{path}: expected 11-D state, got {state.shape}")
    image_name = metadata["images"]["observation.images.cam_high"]
    image = Image.open(path.parent / image_name).convert("RGB")
    return metadata, state, image


def action_metric(actions: np.ndarray, state: np.ndarray) -> dict:
    """Measure which arm is commanded away from the supplied current state."""
    left_per_frame = np.sqrt(np.mean((actions[:, :5] - state[:5]) ** 2, axis=1))
    right_per_frame = np.sqrt(np.mean((actions[:, 5:10] - state[5:10]) ** 2, axis=1))
    left = float(left_per_frame.mean())
    right = float(right_per_frame.mean())
    score = right - left
    # Also report within-chunk motion, which does not algebraically depend on
    # the counterfactual state used to condition the model.
    relative = actions - actions[:1]
    left_shape = float(np.sqrt(np.mean(relative[:, :5] ** 2, axis=1)).mean())
    right_shape = float(np.sqrt(np.mean(relative[:, 5:10] ** 2, axis=1)).mean())
    return {
        "left_target_displacement_rms": left,
        "right_target_displacement_rms": right,
        "right_minus_left_score": score,
        "branch": "right" if score > 0 else "left",
        "left_within_chunk_motion_rms": left_shape,
        "right_within_chunk_motion_rms": right_shape,
        "within_chunk_right_minus_left": right_shape - left_shape,
    }


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.fastwam_root / "scripts"))
    from eval_fastwam_g1_23_real import FastWAMRealPolicy  # noqa: PLC0415

    box_meta, box_state, box_image = load_snapshot(args.box_snapshot)
    bag_meta, bag_state, bag_image = load_snapshot(args.bag_snapshot)
    state_summary = json.loads(args.state_summary.read_text(encoding="utf-8"))
    left_prototype = np.asarray(state_summary["left_initial_state_mean"], dtype=np.float32)
    right_prototype = np.asarray(state_summary["right_initial_state_mean"], dtype=np.float32)
    neutral_prototype = (left_prototype + right_prototype) / 2

    policy_args = SimpleNamespace(
        config=args.run_dir / "config.yaml",
        checkpoint=args.checkpoint,
        dataset_stats=args.run_dir / "dataset_stats.json",
        text_embedding_cache=args.text_embedding_cache,
        asset_root=args.fastwam_root,
        task=TASK,
        device=args.device,
        mixed_precision="bf16",
        num_inference_steps=args.num_inference_steps,
        action_horizon=args.action_horizon,
        action_dim=11,
        compile_action_infer=False,
        seed=args.seed,
    )
    logging.info("Loading FastWAM checkpoint %s", args.checkpoint)
    policy = FastWAMRealPolicy(policy_args)

    images = {"box_image": box_image, "bag_image": bag_image}
    states = {
        "box_live_state": box_state,
        "bag_live_state": bag_state,
        "left_train_prototype": left_prototype,
        "right_train_prototype": right_prototype,
        "neutral_train_prototype": neutral_prototype,
    }
    results: dict[str, dict] = {}

    def infer(name: str, image: Image.Image, state: np.ndarray, seed: int) -> dict:
        policy.seed = seed
        image_tensor = torch.from_numpy(np.asarray(image, dtype=np.uint8).copy())
        _, actions, latency_s = policy.infer_chunk(image_tensor, state)
        metric = action_metric(actions, state)
        metric["latency_s"] = latency_s
        metric["seed"] = seed
        results[name] = metric
        print(
            f"{name}: {metric['branch']} score={metric['right_minus_left_score']:+.5f} "
            f"left={metric['left_target_displacement_rms']:.5f} "
            f"right={metric['right_target_displacement_rms']:.5f} latency={latency_s:.2f}s",
            flush=True,
        )
        return metric

    # Full 2 x 5 image/state factorial design. With fixed noise, changing only
    # image or only state is a direct causal intervention on that input.
    for image_name, image in images.items():
        for state_name, state in states.items():
            infer(f"{image_name}__{state_name}", image, state, args.seed)

    # Remove object-level visual information while preserving global layout.
    infer("box_blurred__box_live_state", box_image.filter(ImageFilter.GaussianBlur(25)), box_state, args.seed)
    infer("bag_blurred__bag_live_state", bag_image.filter(ImageFilter.GaussianBlur(25)), bag_state, args.seed)

    # Diffusion noise robustness for the two natural pairs.
    noise_trials: dict[str, list[dict]] = {"box": [], "bag": []}
    for offset in range(args.noise_trials):
        seed = args.seed + offset
        noise_trials["box"].append(infer(f"box_noise_seed_{seed}", box_image, box_state, seed))
        noise_trials["bag"].append(infer(f"bag_noise_seed_{seed}", bag_image, bag_state, seed))

    summary = {
        "checkpoint": str(args.checkpoint),
        "config": str(policy_args.config),
        "dataset_stats": str(policy_args.dataset_stats),
        "task": TASK,
        "action_order": JOINT_NAMES,
        "metric_definition": (
            "mean RMS target displacement from supplied state over all 32 frames; "
            "positive right_minus_left_score means right-arm preference"
        ),
        "snapshots": {
            "box": {"json": str(args.box_snapshot), "inference_index": box_meta["inference_index"], "expected_branch": "right", "state": box_state.tolist()},
            "black_bag": {"json": str(args.bag_snapshot), "inference_index": bag_meta["inference_index"], "expected_branch": "left", "state": bag_state.tolist()},
        },
        "training_state_prototypes_source": str(args.state_summary),
        "results": results,
        "noise_trials": noise_trials,
    }
    (args.output_dir / "counterfactual_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    box_image.save(args.output_dir / "box_live_snapshot.jpg")
    bag_image.save(args.output_dir / "black_bag_live_snapshot.jpg")
    print(f"Saved {args.output_dir / 'counterfactual_results.json'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
