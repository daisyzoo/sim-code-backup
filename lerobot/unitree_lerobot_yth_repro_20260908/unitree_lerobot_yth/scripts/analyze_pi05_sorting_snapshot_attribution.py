#!/usr/bin/env python3
"""Offline causal attribution for one PI0.5 sorting inference snapshot."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
import torch

from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.processor.rename_processor import rename_stats
from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS


JOINT_NAMES = [
    "left_arm_0", "left_arm_1", "left_arm_2", "left_arm_3", "left_arm_4",
    "right_arm_0", "right_arm_1", "right_arm_2", "right_arm_3", "right_arm_4",
    "waist_yaw",
]
CORRECT_TASK = "Sort packages: place black bags on the left and boxes on the right."


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
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("outputs/rtc_inference_snapshots/pi05_sorting_11d_15hz"),
    )
    parser.add_argument("--snapshot-json", type=Path)
    parser.add_argument("--execution-log", type=Path)
    parser.add_argument(
        "--image-description",
        default="box in front of the robot (manual inspection)",
        help="Human-readable description written to REPORT.md.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/sorting_offline_analysis/snapshot_attribution"),
    )
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--noise-trials", type=int, default=5)
    parser.add_argument("--num-inference-steps", type=int, default=10)
    parser.add_argument("--decision-horizon", type=int, default=20)
    parser.add_argument("--grid-rows", type=int, default=6)
    parser.add_argument("--grid-cols", type=int, default=8)
    return parser.parse_args()


def select_snapshot(args: argparse.Namespace) -> Path:
    if args.snapshot_json is not None:
        return args.snapshot_json
    candidates = sorted(
        args.snapshot_dir.glob("inference_0001_*.json"),
        key=lambda path: path.stat().st_mtime_ns,
    )
    if not candidates:
        raise FileNotFoundError(f"No inference_0001 snapshot JSON under {args.snapshot_dir}")
    return candidates[-1]


def load_snapshot(path: Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    state = np.asarray(metadata["observation_state"], dtype=np.float32)
    if state.shape != (11,):
        raise ValueError(f"Snapshot state must be shape (11,), got {state.shape}")
    image_name = metadata.get("images", {}).get("observation.images.cam_high")
    if not image_name:
        raise KeyError("Snapshot has no observation.images.cam_high image")
    image_bgr = cv2.imread(str(path.parent / image_name), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise FileNotFoundError(path.parent / image_name)
    return metadata, state, cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def find_execution_log(snapshot: dict[str, Any], explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    snapshot_ns = int(snapshot["inference_start_wall_time_ns"])
    candidates = []
    for path in Path("outputs/rtc_execution_logs").glob("**/*.jsonl"):
        try:
            with path.open(encoding="utf-8") as handle:
                first = json.loads(handle.readline())
            config = first.get("config", {})
            if "pick_cup_sorting_0824" not in str(config.get("root", "")):
                continue
            candidates.append((abs(path.stat().st_mtime_ns - snapshot_ns), path))
        except Exception:
            continue
    return min(candidates)[1] if candidates else None


def action_metric(actions: np.ndarray, state: np.ndarray, horizon: int) -> dict[str, Any]:
    count = min(len(actions), max(1, horizon))
    selected = actions[:count]
    left_frames = np.sqrt(np.mean((selected[:, :5] - state[:5]) ** 2, axis=1))
    right_frames = np.sqrt(np.mean((selected[:, 5:10] - state[5:10]) ** 2, axis=1))
    left_motion = float(np.mean(left_frames))
    right_motion = float(np.mean(right_frames))
    score = right_motion - left_motion
    return {
        "frames": count,
        "left_motion_rms": left_motion,
        "right_motion_rms": right_motion,
        "right_minus_left_score": score,
        "branch": "right" if score > 0.0 else "left",
    }


def read_live_context(
    log_path: Path | None,
    inference_index: int,
    snapshot_state: np.ndarray,
    horizon: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {"task_text": CORRECT_TASK, "executed_policy_metric": None}
    if log_path is None or not log_path.is_file():
        return result
    actions = []
    with log_path.open(encoding="utf-8") as handle:
        first = json.loads(handle.readline())
        result["task_text"] = str(first.get("config", {}).get("task_override", CORRECT_TASK))
        for line in handle:
            record = json.loads(line)
            source = record.get("rtc_source") or {}
            if (
                record.get("record_type") == "rtc_executed_action"
                and int(source.get("inference_index", -1)) == inference_index
            ):
                actions.append(record["policy_action"])
    if actions:
        result["executed_policy_metric"] = action_metric(
            np.asarray(actions, dtype=np.float32), snapshot_state, horizon
        )
    result["execution_log"] = str(log_path)
    return result


def load_branch_prototypes(dataset_root: Path) -> dict[str, np.ndarray]:
    paths = sorted((dataset_root / "data").glob("*/*.parquet"))
    table = pq.read_table(
        paths,
        columns=["episode_index", "frame_index", "observation.state", "action"],
    )
    episode_index = np.asarray(table["episode_index"], dtype=np.int64)
    frame_index = np.asarray(table["frame_index"], dtype=np.int64)
    states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
    actions = np.asarray(table["action"].to_pylist(), dtype=np.float32)
    initial_states = []
    labels = []
    for episode_id in np.unique(episode_index):
        indices = np.flatnonzero(episode_index == episode_id)
        indices = indices[np.argsort(frame_index[indices])]
        initial = states[indices[0]]
        episode_actions = actions[indices]
        left = np.sqrt(np.mean((episode_actions[:, :5] - initial[:5]) ** 2, axis=1)).max()
        right = np.sqrt(np.mean((episode_actions[:, 5:10] - initial[5:10]) ** 2, axis=1)).max()
        initial_states.append(initial)
        labels.append(int(right > left))
    initial_states = np.asarray(initial_states)
    labels = np.asarray(labels)
    return {
        "left": initial_states[labels == 0].mean(axis=0),
        "right": initial_states[labels == 1].mean(axis=0),
        "neutral": initial_states.mean(axis=0),
        "episode_0": initial_states[0],
        "initial_std": np.maximum(initial_states.std(axis=0), 1e-8),
    }


class OfflinePolicy:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        config = PreTrainedConfig.from_pretrained(args.policy_path)
        config.pretrained_path = args.policy_path
        config.device = args.device
        config.num_inference_steps = args.num_inference_steps
        self.dataset = LeRobotDataset(
            repo_id=args.repo_id,
            root=args.dataset_root,
            episodes=[0],
        )
        self.policy = make_policy(config, ds_meta=self.dataset.meta)
        self.policy.eval()
        if hasattr(self.policy.model, "gradient_checkpointing_disable"):
            self.policy.model.gradient_checkpointing_disable()
        rename_map = {"observation.images.cam_high": "observation.images.color_0"}
        overrides = {
            "device_processor": {"device": args.device},
            "rename_observations_processor": {"rename_map": rename_map},
            "tokenizer_processor": {
                "tokenizer_name": str(args.tokenizer_path),
                "local_files_only": True,
            },
        }
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            policy_cfg=config,
            pretrained_path=config.pretrained_path,
            dataset_stats=rename_stats(self.dataset.meta.stats, rename_map),
            preprocessor_overrides=overrides,
        )
        self.action_dim = int(config.output_features["action"].shape[0])
        self.noise_shape = (1, config.chunk_size, config.max_action_dim)

    def make_noise(self, seed: int) -> torch.Tensor:
        generator = torch.Generator(device=self.args.device)
        generator.manual_seed(seed)
        return torch.randn(
            self.noise_shape,
            generator=generator,
            device=self.args.device,
            dtype=torch.float32,
        )

    def preprocess(self, image_rgb: np.ndarray, state: np.ndarray, task: str) -> dict[str, Any]:
        observation: dict[str, Any] = {
            "observation.images.cam_high": torch.from_numpy(image_rgb.copy())
            .to(torch.float32)
            .div(255.0)
            .permute(2, 0, 1)
            .contiguous()
            .unsqueeze(0),
            "observation.state": torch.from_numpy(state.copy()).to(torch.float32).unsqueeze(0),
            "task": task,
            "robot_type": "",
        }
        self.preprocessor.reset()
        return self.preprocessor(observation)

    def infer(
        self,
        image_rgb: np.ndarray,
        state: np.ndarray,
        task: str,
        noise: torch.Tensor,
    ) -> np.ndarray:
        batch = self.preprocess(image_rgb, state, task)
        images, image_masks = self.policy._preprocess_images(batch)
        tokens = batch[OBS_LANGUAGE_TOKENS]
        masks = batch[OBS_LANGUAGE_ATTENTION_MASK]
        with torch.inference_mode():
            actions = self.policy.model.sample_actions(
                images,
                image_masks,
                tokens,
                masks,
                noise=noise.clone(),
                num_steps=self.args.num_inference_steps,
            )[:, :, : self.action_dim]
            self.postprocessor.reset()
            actions = self.postprocessor(actions)
        return actions.squeeze(0).detach().cpu().numpy()


def plot_condition_scores(path: Path, metrics: dict[str, dict[str, Any]]) -> None:
    names = list(metrics)
    values = [metrics[name]["right_minus_left_score"] for name in names]
    colors = ["#377eb8" if value > 0 else "#e41a1c" for value in values]
    figure, axis = plt.subplots(figsize=(11, max(4, len(names) * 0.42)))
    axis.barh(names, values, color=colors)
    axis.axvline(0.0, color="black", linewidth=1.0)
    axis.set_xlabel("right-arm motion RMS - left-arm motion RMS (rad)")
    axis.set_title("Fixed-noise causal interventions (blue=right, red=left)")
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def plot_state_importance(path: Path, values: np.ndarray) -> None:
    colors = ["#377eb8" if value > 0 else "#e41a1c" for value in values]
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.bar(JOINT_NAMES, values, color=colors)
    axis.axhline(0.0, color="black", linewidth=1.0)
    axis.set_ylabel("score(right prototype) - score(left prototype)")
    axis.set_title("Single-joint state counterfactual effect; fixed image and noise")
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def plot_image_heatmap(path: Path, image_rgb: np.ndarray, support: np.ndarray) -> None:
    height, width = image_rgb.shape[:2]
    resized = cv2.resize(support.astype(np.float32), (width, height), interpolation=cv2.INTER_NEAREST)
    limit = max(float(np.max(np.abs(resized))), 1e-8)
    figure, axis = plt.subplots(figsize=(12, 9))
    axis.imshow(image_rgb)
    overlay = axis.imshow(resized, cmap="coolwarm", vmin=-limit, vmax=limit, alpha=0.52)
    axis.set_title(
        "Causal image occlusion: red supports RIGHT, blue supports LEFT\n"
        "value = baseline score - score after local blur"
    )
    axis.axis("off")
    figure.colorbar(overlay, ax=axis, fraction=0.035, pad=0.02)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = select_snapshot(args)
    snapshot, state, image_rgb = load_snapshot(snapshot_path)
    execution_log = find_execution_log(snapshot, args.execution_log)
    live_context = read_live_context(
        execution_log,
        int(snapshot["inference_index"]),
        state,
        args.decision_horizon,
    )
    live_task = live_context["task_text"]
    prototypes = load_branch_prototypes(args.dataset_root)
    delta_episode_0 = state - prototypes["episode_0"]

    logging.info("Loading PI0.5 once for offline interventions")
    policy = OfflinePolicy(args)
    fixed_noise = policy.make_noise(args.seed)
    condition_metrics: dict[str, dict[str, Any]] = {}

    def evaluate(name: str, image: np.ndarray, robot_state: np.ndarray, task: str) -> dict[str, Any]:
        actions = policy.infer(image, robot_state, task, fixed_noise)
        metric = action_metric(actions, robot_state, args.decision_horizon)
        condition_metrics[name] = metric
        print(
            f"{name}: branch={metric['branch']} "
            f"score={metric['right_minus_left_score']:+.5f} "
            f"left={metric['left_motion_rms']:.5f} right={metric['right_motion_rms']:.5f}"
        )
        return metric

    baseline = evaluate("baseline_logged_task", image_rgb, state, live_task)
    evaluate("corrected_task_text", image_rgb, state, CORRECT_TASK)
    evaluate("left_initial_state_prototype", image_rgb, prototypes["left"], live_task)
    evaluate("right_initial_state_prototype", image_rgb, prototypes["right"], live_task)
    evaluate("neutral_initial_state_prototype", image_rgb, prototypes["neutral"], live_task)
    blurred = cv2.GaussianBlur(image_rgb, (51, 51), 0)
    grayscale = cv2.cvtColor(cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    evaluate("fully_blurred_image", blurred, state, live_task)
    evaluate("grayscale_image", grayscale, state, live_task)

    state_contrast = np.zeros(11, dtype=np.float64)
    state_joint_metrics: dict[str, Any] = {}
    for index, name in enumerate(JOINT_NAMES):
        left_state = state.copy()
        right_state = state.copy()
        left_state[index] = prototypes["left"][index]
        right_state[index] = prototypes["right"][index]
        left_actions = policy.infer(image_rgb, left_state, live_task, fixed_noise)
        right_actions = policy.infer(image_rgb, right_state, live_task, fixed_noise)
        left_metric = action_metric(left_actions, left_state, args.decision_horizon)
        right_metric = action_metric(right_actions, right_state, args.decision_horizon)
        contrast = right_metric["right_minus_left_score"] - left_metric["right_minus_left_score"]
        state_contrast[index] = contrast
        state_joint_metrics[name] = {
            "left_prototype_value": float(prototypes["left"][index]),
            "right_prototype_value": float(prototypes["right"][index]),
            "left_value_metric": left_metric,
            "right_value_metric": right_metric,
            "right_minus_left_prototype_effect": float(contrast),
        }
        print(f"state {name}: contrast={contrast:+.5f}")

    rows, cols = args.grid_rows, args.grid_cols
    support = np.zeros((rows, cols), dtype=np.float64)
    height, width = image_rgb.shape[:2]
    blur_source = cv2.GaussianBlur(image_rgb, (81, 81), 0)
    for row in range(rows):
        y0, y1 = round(row * height / rows), round((row + 1) * height / rows)
        for col in range(cols):
            x0, x1 = round(col * width / cols), round((col + 1) * width / cols)
            occluded = image_rgb.copy()
            occluded[y0:y1, x0:x1] = blur_source[y0:y1, x0:x1]
            actions = policy.infer(occluded, state, live_task, fixed_noise)
            metric = action_metric(actions, state, args.decision_horizon)
            support[row, col] = (
                baseline["right_minus_left_score"] - metric["right_minus_left_score"]
            )
            print(
                f"image cell {row + 1}/{rows},{col + 1}/{cols}: "
                f"support={support[row, col]:+.5f}"
            )

    noise_trials = []
    for offset in range(max(1, args.noise_trials)):
        noise = policy.make_noise(args.seed + offset)
        actions = policy.infer(image_rgb, state, live_task, noise)
        noise_trials.append(action_metric(actions, state, args.decision_horizon))

    plot_condition_scores(args.output_dir / "condition_scores.png", condition_metrics)
    plot_state_importance(args.output_dir / "state_joint_counterfactual.png", state_contrast)
    plot_image_heatmap(args.output_dir / "image_occlusion_heatmap.png", image_rgb, support)
    cv2.imwrite(
        str(args.output_dir / "snapshot_input.jpg"),
        cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR),
    )

    summary = {
        "snapshot_json": str(snapshot_path),
        "execution_log": str(execution_log) if execution_log else None,
        "policy_path": str(args.policy_path),
        "dataset_root": str(args.dataset_root),
        "fixed_noise_seed": args.seed,
        "decision_horizon": args.decision_horizon,
        "logged_task_text": live_task,
        "correct_task_text": CORRECT_TASK,
        "image_description": args.image_description,
        "snapshot_state": state.tolist(),
        "dataset_episode_0_initial_state": prototypes["episode_0"].tolist(),
        "snapshot_minus_episode_0": delta_episode_0.tolist(),
        "snapshot_episode_0_max_abs_delta": float(np.max(np.abs(delta_episode_0))),
        "snapshot_episode_0_std_normalized_rms": float(
            np.sqrt(np.mean((delta_episode_0 / prototypes["initial_std"]) ** 2))
        ),
        "actual_executed_policy_metric": live_context.get("executed_policy_metric"),
        "condition_metrics": condition_metrics,
        "state_joint_counterfactual": state_joint_metrics,
        "image_occlusion_support_grid": support.tolist(),
        "noise_trials": noise_trials,
    }
    (args.output_dir / "attribution_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    right_count = sum(metric["branch"] == "right" for metric in noise_trials)
    actual_metric = live_context.get("executed_policy_metric")
    actual_branch = actual_metric["branch"] if actual_metric else "unavailable"
    report = f"""# PI0.5 sorting snapshot offline attribution

- Snapshot: {snapshot_path}
- Image content: {args.image_description}
- Actual logged task text: {live_task}
- Correct task text: {CORRECT_TASK}
- Snapshot vs dataset episode-0 initial state max absolute difference: {np.max(np.abs(delta_episode_0)):.6f} rad
- Actual executed first-chunk branch: {actual_branch}
- Fixed-noise offline baseline branch: {baseline['branch']} (score {baseline['right_minus_left_score']:+.6f})
- Noise trials choosing right: {right_count}/{len(noise_trials)}

Decision score is mean right-arm target displacement minus mean left-arm target displacement
over the first {args.decision_horizon} action frames. Positive means right-arm preference.

image_occlusion_heatmap.png is causal patch occlusion, not a raw attention map.
state_joint_counterfactual.png changes one state joint at a time between the left-branch
and right-branch training prototypes while holding the image and diffusion noise fixed.
"""
    (args.output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"Artifacts: {args.output_dir.resolve()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
