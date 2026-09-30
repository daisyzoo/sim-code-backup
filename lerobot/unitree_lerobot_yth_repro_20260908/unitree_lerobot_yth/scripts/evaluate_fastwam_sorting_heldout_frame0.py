#!/usr/bin/env python3
"""Infer FastWAM from frame 0 of selected held-out sorting episodes.

Run ``--phase infer`` in the FastWAM environment, then ``--phase plot`` in an
environment containing matplotlib.  No robot interface is imported or used.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace


WORKSPACE = Path("/home/igs/Desktop/project/vla/unitree_lerobot_yth")
FASTWAM_ROOT = Path("/skydata/syh/FastWAM")
RUN = FASTWAM_ROOT / (
    "runs/pick_cup_sorting_first_frame_0824_0828_1cam224x288_1e-4/"
    "2026-08-31_17-41-07"
)
DATASET = Path(
    "/skydata/syh/InternVLA-A-series/.cache/huggingface/lerobot/xr/"
    "pick_cup_sorting_0824"
)
SPLIT_STATS = FASTWAM_ROOT / (
    "configs/data/stats/pick_cup_sorting_0824_train_0828_all_11d_absolute.json"
)
TEXT_EMBEDDING = FASTWAM_ROOT / (
    "datasets/data/text_embeds_cache/pick_cup_sorting_first_frame/"
    "740fc050e848971fd5c4ab04d00ecac9b269caa053eeb6d5b52b2a8209cf0a53."
    "t5_len128.wan22ti2v5b.pt"
)
OUTPUT = WORKSPACE / "outputs/fastwam_sorting_offline_analysis/step_020000_heldout_frame0"
TASK = (
    "Sort the package on the table by type. If it is a black bag, press and hold "
    "the bag down with the left hand, then push it to the left sorting area. If it "
    "is a box, press and hold the box down with the right hand, then push it to the "
    "right sorting area."
)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("infer", "plot"), required=True)
    parser.add_argument("--fastwam-root", type=Path, default=FASTWAM_ROOT)
    parser.add_argument("--run-dir", type=Path, default=RUN)
    parser.add_argument("--checkpoint", type=Path, default=RUN / "checkpoints/weights/step_020000.pt")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--split-stats", type=Path, default=SPLIT_STATS)
    parser.add_argument("--text-embedding-cache", type=Path, default=TEXT_EMBEDDING)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument(
        "--episodes",
        default="14,36,41,64",
        help="Held-out episode IDs. Defaults contain two left-arm and two right-arm examples.",
    )
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--action-horizon", type=int, default=32)
    parser.add_argument("--fps", type=float, default=15.0)
    return parser.parse_args()


def episode_ids(value: str) -> list[int]:
    result = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not result:
        raise ValueError("--episodes is empty")
    return result


def motion_metric(actions, state) -> dict[str, float | str]:
    import numpy as np

    delta = actions - state[None]
    left = float(np.sqrt(np.mean(delta[:, :5] ** 2, axis=1)).mean())
    right = float(np.sqrt(np.mean(delta[:, 5:10] ** 2, axis=1)).mean())
    return {
        "left_target_displacement_rms": left,
        "right_target_displacement_rms": right,
        "right_minus_left_score": right - left,
        "branch": "right" if right > left else "left",
    }


def load_cases(args: argparse.Namespace, episodes: list[int]):
    import av
    import numpy as np
    import pyarrow.parquet as pq

    paths = sorted((args.dataset / "data").glob("*/*.parquet"))
    table = pq.read_table(
        paths,
        columns=["episode_index", "frame_index", "index", "observation.state", "action"],
    )
    episode_col = np.asarray(table["episode_index"], dtype=np.int64)
    frame_col = np.asarray(table["frame_index"], dtype=np.int64)
    global_col = np.asarray(table["index"], dtype=np.int64)
    states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
    actions = np.asarray(table["action"].to_pylist(), dtype=np.float32)

    split = json.loads(args.split_stats.read_text(encoding="utf-8"))
    training = set(int(value) for value in split["sources"][0]["episodes"])
    invalid = sorted(set(episodes) & training)
    if invalid:
        raise ValueError(f"episodes are in the training split, not held out: {invalid}")

    cases = {}
    target_global_indices = {}
    for episode in episodes:
        rows = np.flatnonzero(episode_col == episode)
        rows = rows[np.argsort(frame_col[rows])]
        if len(rows) < args.action_horizon or int(frame_col[rows[0]]) != 0:
            raise ValueError(f"episode {episode} cannot provide frame 0 plus {args.action_horizon} actions")
        first = int(rows[0])
        cases[episode] = {
            "state": states[first],
            "ground_truth": actions[rows[: args.action_horizon]],
            "global_index": int(global_col[first]),
            "episode_length": int(len(rows)),
        }
        target_global_indices[int(global_col[first])] = episode

    video_paths = sorted(
        (args.dataset / "videos/observation.images.color_0").glob("*/*.mp4")
    )
    if len(video_paths) != 1:
        raise ValueError(f"expected one dataset video, found {len(video_paths)}")
    remaining = dict(target_global_indices)
    with av.open(str(video_paths[0])) as container:
        for frame_number, frame in enumerate(container.decode(video=0)):
            episode = remaining.pop(frame_number, None)
            if episode is not None:
                cases[episode]["image"] = frame.to_ndarray(format="rgb24")
            if not remaining:
                break
    if remaining:
        raise RuntimeError(f"could not decode global video frames {sorted(remaining)}")
    return cases


def run_inference(args: argparse.Namespace) -> None:
    import numpy as np
    import torch
    from PIL import Image

    episodes = episode_ids(args.episodes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases(args, episodes)
    sys.path.insert(0, str(args.fastwam_root / "scripts"))
    from eval_fastwam_g1_23_real import FastWAMRealPolicy  # noqa: PLC0415

    # FastWAM's Wan component loader resolves its local ``checkpoints`` root
    # from cwd.  Use the checkout that already owns the base weights so running
    # this script from another repository never triggers a duplicate download.
    os.chdir(args.fastwam_root)

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
    policy = FastWAMRealPolicy(policy_args)
    results = []
    for episode in episodes:
        case = cases[episode]
        image_tensor = torch.from_numpy(case["image"].copy())
        _, prediction, latency_s = policy.infer_chunk(image_tensor, case["state"])
        truth_metric = motion_metric(case["ground_truth"], case["state"])
        prediction_metric = motion_metric(prediction, case["state"])
        Image.fromarray(case["image"]).save(args.output_dir / f"episode_{episode:03d}_frame_000.jpg")
        result = {
            "episode": episode,
            "frame": 0,
            "global_index": case["global_index"],
            "episode_length": case["episode_length"],
            "state": case["state"].tolist(),
            "ground_truth_actions": case["ground_truth"].tolist(),
            "predicted_actions": prediction.tolist(),
            "ground_truth_metric": truth_metric,
            "prediction_metric": prediction_metric,
            "inference_latency_s": latency_s,
        }
        results.append(result)
        print(
            f"episode={episode} frame=0 truth={truth_metric['branch']} "
            f"prediction={prediction_metric['branch']} "
            f"score={prediction_metric['right_minus_left_score']:+.4f} "
            f"latency={latency_s:.3f}s",
            flush=True,
        )
    payload = {
        "checkpoint": str(args.checkpoint),
        "dataset": str(args.dataset),
        "split_stats": str(args.split_stats),
        "task": TASK,
        "seed": args.seed,
        "fps": args.fps,
        "action_horizon": args.action_horizon,
        "joint_order": JOINT_NAMES,
        "results": results,
    }
    (args.output_dir / "results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved raw results to {args.output_dir / 'results.json'}")


def run_plot(args: argparse.Namespace) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    path = args.output_dir / "results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    report_rows = []
    for result in payload["results"]:
        episode = int(result["episode"])
        state = np.asarray(result["state"], dtype=np.float32)
        truth = np.asarray(result["ground_truth_actions"], dtype=np.float32)
        prediction = np.asarray(result["predicted_actions"], dtype=np.float32)
        time_s = np.arange(len(prediction)) / float(payload["fps"])
        fig, axes = plt.subplots(4, 3, figsize=(15, 13), sharex=True)
        for joint, (name, axis) in enumerate(zip(payload["joint_order"], axes.flat)):
            axis.plot(time_s, truth[:, joint], "--", linewidth=1.8, label="ground truth")
            axis.plot(time_s, prediction[:, joint], linewidth=1.8, label="prediction")
            axis.axhline(state[joint], color="black", linestyle=":", linewidth=1.0, label="frame-0 state")
            axis.set_title(name)
            axis.set_ylabel("rad")
            axis.grid(alpha=0.25)
        axes.flat[-1].axis("off")
        for axis in axes[-1, :2]:
            axis.set_xlabel("chunk time (s)")
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.96, 0.075))
        truth_branch = result["ground_truth_metric"]["branch"]
        prediction_branch = result["prediction_metric"]["branch"]
        fig.suptitle(
            f"FastWAM held-out episode {episode}, frame 0 | "
            f"truth={truth_branch}, prediction={prediction_branch}"
        )
        fig.tight_layout(rect=(0, 0.03, 1, 0.97))
        figure_name = f"episode_{episode:03d}_frame0_joint_trajectories.png"
        fig.savefig(args.output_dir / figure_name, dpi=180)
        plt.close(fig)
        report_rows.append(
            f"| {episode} | {truth_branch} | {prediction_branch} | "
            f"{result['prediction_metric']['right_minus_left_score']:+.4f} | "
            f"{result['inference_latency_s']:.3f} | [{figure_name}]({figure_name}) |"
        )

    report = "\n".join(
        [
            "# FastWAM held-out frame-0 chunk trajectories",
            "",
            f"- Checkpoint: `{payload['checkpoint']}`",
            f"- Dataset: `{payload['dataset']}`",
            f"- Input frame: episode frame 0",
            f"- Chunk: {payload['action_horizon']} actions at {payload['fps']} Hz",
            f"- Diffusion seed: {payload['seed']}",
            "",
            "The branch score is mean right-arm target displacement minus mean left-arm target displacement from the frame-0 state. Positive means right arm.",
            "",
            "| Episode | Ground truth | Prediction | Branch score | Latency (s) | Trajectories |",
            "|---:|:---:|:---:|---:|---:|:---|",
            *report_rows,
            "",
            "Each trajectory figure shows the absolute joint target in radians. The dotted line is the observed frame-0 joint state, the dashed line is the demonstration, and the solid line is FastWAM's predicted 32-action chunk.",
            "",
        ]
    )
    (args.output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


def main() -> None:
    args = parse_args()
    if args.phase == "infer":
        run_inference(args)
    else:
        run_plot(args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
