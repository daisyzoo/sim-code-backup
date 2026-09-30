#!/usr/bin/env python3
"""Infer FastWAM action chunks for selected sorting snapshots and save plot inputs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image


DEFAULT_RUN = Path(
    "/skydata/syh/FastWAM/runs/"
    "pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/"
    "2026-08-31_17-41-07"
)
DEFAULT_PROMPT = (
    "Sort the package on the table by type. If it is a black bag, press and hold the bag "
    "down with the left hand, then push it to the left sorting area. If it is a box, "
    "press and hold the box down with the right hand, then push it to the right sorting area."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fastwam-root", type=Path, default=Path("/skydata/syh/FastWAM"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument(
        "--checkpoint", type=Path, default=DEFAULT_RUN / "checkpoints/weights/step_020000.pt"
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
    parser.add_argument("--snapshot-json", type=Path, action="append", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "outputs/fastwam_sorting_offline_analysis/step_020000_hand_trajectories"
        ),
    )
    parser.add_argument("--task", default=DEFAULT_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--action-horizon", type=int, default=32)
    return parser.parse_args()


def load_snapshot(path: Path) -> tuple[dict, np.ndarray, Image.Image]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    state = np.asarray(metadata["observation_state"], dtype=np.float32)
    if state.shape != (11,) or not np.isfinite(state).all():
        raise ValueError(f"{path}: expected finite 11-D observation_state, got {state.shape}")
    image_name = metadata["images"]["observation.images.cam_high"]
    image_path = path.parent / image_name
    return metadata, state, Image.open(image_path).convert("RGB")


def action_metric(actions: np.ndarray, state: np.ndarray) -> dict[str, float | str]:
    delta = actions - state[None]
    left = float(np.sqrt(np.mean(delta[:, :5] ** 2, axis=1)).mean())
    right = float(np.sqrt(np.mean(delta[:, 5:10] ** 2, axis=1)).mean())
    return {
        "left_target_displacement_rms": left,
        "right_target_displacement_rms": right,
        "right_minus_left_score": right - left,
        "branch": "right" if right > left else "left",
    }


def main() -> None:
    args = parse_args()
    args.fastwam_root = args.fastwam_root.expanduser().resolve()
    args.run_dir = args.run_dir.expanduser().resolve()
    args.checkpoint = args.checkpoint.expanduser().resolve()
    args.text_embedding_cache = args.text_embedding_cache.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    snapshot_paths = [path.expanduser().resolve() for path in args.snapshot_json]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_output_dir = args.output_dir / "selected_snapshots"
    snapshot_output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.fastwam_root / "scripts"))
    from eval_fastwam_g1_23_real import FastWAMRealPolicy  # noqa: PLC0415

    # Wan base assets are resolved relative to the FastWAM checkout.
    os.chdir(args.fastwam_root)
    policy_args = SimpleNamespace(
        config=args.run_dir / "config.yaml",
        checkpoint=args.checkpoint,
        dataset_stats=args.run_dir / "dataset_stats.json",
        text_embedding_cache=args.text_embedding_cache,
        asset_root=args.fastwam_root,
        task=args.task,
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

    summary = []
    for snapshot_path in snapshot_paths:
        metadata, state, image = load_snapshot(snapshot_path)
        policy.seed = args.seed
        image_tensor = torch.from_numpy(np.asarray(image, dtype=np.uint8).copy())
        _, actions, latency_s = policy.infer_chunk(image_tensor, state)
        actions = np.asarray(actions, dtype=np.float32)
        if actions.shape != (args.action_horizon, 11):
            raise ValueError(
                f"{snapshot_path}: expected [{args.action_horizon}, 11] actions, got {actions.shape}"
            )

        prediction_path = args.output_dir / f"{snapshot_path.stem}_predicted_chunk.npy"
        np.save(prediction_path, actions)
        shutil.copy2(snapshot_path, snapshot_output_dir / snapshot_path.name)
        image_name = metadata["images"]["observation.images.cam_high"]
        shutil.copy2(snapshot_path.parent / image_name, snapshot_output_dir / image_name)

        result = {
            "snapshot": str(snapshot_path),
            "prediction": str(prediction_path),
            "seed": args.seed,
            "task": args.task,
            "num_actions": int(len(actions)),
            "latency_s": float(latency_s),
            "decision_metric": action_metric(actions, state),
        }
        summary.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)

    summary_path = args.output_dir / "fastwam_prediction_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved predictions: {args.output_dir}")
    print(f"Snapshot subset: {snapshot_output_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
