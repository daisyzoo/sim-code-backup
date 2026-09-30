#!/usr/bin/env python3
"""Infer PI0.5 action chunks for selected sorting snapshots and save plot inputs."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from analyze_pi05_sorting_snapshot_attribution import OfflinePolicy, action_metric, load_snapshot


DEFAULT_PROMPT = (
    "Sort the package on the table by type. If it is a black bag, press and hold the bag "
    "down with the left hand, then push it to the left sorting area. If it is a box, "
    "press and hold the box down with the right hand, then push it to the right sorting area."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-path",
        type=Path,
        default=Path(
            "/skydata/model/sorting_11d_merged_20260828_103515/checkpoints/020000/"
            "pretrained_model"
        ),
    )
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
        "--tokenizer-path",
        type=Path,
        default=Path(
            "/home/igs/Desktop/project/vla/data/.hf_hub_cache/"
            "models--google--paligemma-3b-pt-224/snapshots/"
            "35e4f46485b4d07967e7e9935bc3786aad50687c"
        ),
    )
    parser.add_argument("--snapshot-json", type=Path, action="append", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "outputs/sorting_offline_analysis/pi05_checkpoint_020000_hand_trajectories"
        ),
    )
    parser.add_argument("--task", default=DEFAULT_PROMPT)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--decision-horizon", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_output_dir = args.output_dir / "selected_snapshots"
    snapshot_output_dir.mkdir(parents=True, exist_ok=True)

    policy_args = SimpleNamespace(
        dataset_root=args.dataset_root,
        repo_id=args.repo_id,
        policy_path=args.policy_path,
        tokenizer_path=args.tokenizer_path,
        device=args.device,
        num_inference_steps=args.num_inference_steps,
    )
    policy = OfflinePolicy(policy_args)
    fixed_noise = policy.make_noise(args.seed)

    summary = []
    for snapshot_path in args.snapshot_json:
        snapshot_path = snapshot_path.expanduser().resolve()
        metadata, state, image_rgb = load_snapshot(snapshot_path)
        actions = policy.infer(image_rgb, state, args.task, fixed_noise)
        if actions.ndim != 2 or actions.shape[1] != 11:
            raise ValueError(f"{snapshot_path}: expected [T, 11] actions, got {actions.shape}")

        prediction_path = args.output_dir / f"{snapshot_path.stem}_predicted_chunk.npy"
        np.save(prediction_path, actions)

        copied_json = snapshot_output_dir / snapshot_path.name
        shutil.copy2(snapshot_path, copied_json)
        image_name = metadata["images"]["observation.images.cam_high"]
        source_image = snapshot_path.parent / image_name
        shutil.copy2(source_image, snapshot_output_dir / image_name)

        metric = action_metric(actions, state, args.decision_horizon)
        result = {
            "snapshot": str(snapshot_path),
            "prediction": str(prediction_path.resolve()),
            "seed": args.seed,
            "task": args.task,
            "num_actions": int(len(actions)),
            "decision_metric": metric,
        }
        summary.append(result)
        print(json.dumps(result, ensure_ascii=False))

    summary_path = args.output_dir / "pi05_prediction_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved predictions: {args.output_dir.resolve()}")
    print(f"Snapshot subset: {snapshot_output_dir.resolve()}")


if __name__ == "__main__":
    main()
