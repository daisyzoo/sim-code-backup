#!/usr/bin/env python3
"""Offline routing diagnostics: open-loop, per-task val loss, frame0 classifier."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Subset

SIM_ROOT = Path(__file__).resolve().parents[1]
LEROBOT_SRC = (
    SIM_ROOT.parent
    / "lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src"
)
if str(LEROBOT_SRC) not in sys.path:
    sys.path.insert(0, str(LEROBOT_SRC))

from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata
from lerobot.datasets.factory import make_dataset
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.utils.constants import OBS_LANGUAGE_ATTENTION_MASK, OBS_LANGUAGE_TOKENS

DEFAULT_PROMPT = (
    "Sort the package on the table by type. If there is no package on the table, keep both "
    "arms still and wait. If it is a black bag, press and hold the bag down with the left "
    "hand, then push it to the left sorting area. If it is a box, press and hold the box "
    "down with the right hand, then push it to the right sorting area."
)
SHORT_BOX_PROMPT = "Push the box to the right with the right hand."
SHORT_MAILER_PROMPT = "Push the black bag to the left with the left hand."
SHORT_WAIT_PROMPT = "Keep both arms still and wait."


def _l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)))


def _shoulder_rolls(action: np.ndarray) -> tuple[float, float]:
    a = np.asarray(action, dtype=np.float64).reshape(-1)
    return float(a[1]), float(a[6])


def load_inferencer(policy_path: Path, dataset_root: Path, tokenizer_path: Path, device: str, seed: int):
    torch.manual_seed(seed)
    np.random.seed(seed)
    config = PreTrainedConfig.from_pretrained(str(policy_path))
    config.pretrained_path = str(policy_path)
    config.device = device
    ds_meta = LeRobotDatasetMetadata(repo_id="local/diag", root=str(dataset_root))
    policy = make_policy(config, ds_meta=ds_meta)
    policy.eval()
    if hasattr(policy.model, "gradient_checkpointing_disable"):
        policy.model.gradient_checkpointing_disable()
    overrides = {
        "device_processor": {"device": device},
        "tokenizer_processor": {
            "tokenizer_name": str(tokenizer_path),
            "local_files_only": True,
        },
    }
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=str(policy_path),
        dataset_stats=ds_meta.stats,
        preprocessor_overrides=overrides,
    )
    action_dim = int(config.output_features["action"].shape[0])
    chunk_size = int(config.chunk_size)
    noise_shape = (1, chunk_size, config.max_action_dim)
    dev = torch.device(device)

    def infer(image_chw: torch.Tensor, state: np.ndarray, task: str, noise_seed: int) -> np.ndarray:
        torch.manual_seed(noise_seed)
        observation: dict[str, Any] = {
            "observation.images.color_0": image_chw.unsqueeze(0).float(),
            "observation.state": torch.from_numpy(np.asarray(state, dtype=np.float32)).unsqueeze(0),
            "task": task,
            "robot_type": "",
        }
        preprocessor.reset()
        batch = preprocessor(observation)
        images, image_masks = policy._preprocess_images(batch)
        tokens = batch[OBS_LANGUAGE_TOKENS]
        masks = batch[OBS_LANGUAGE_ATTENTION_MASK]
        noise = torch.randn(noise_shape, device=dev, dtype=torch.float32)
        with torch.inference_mode():
            actions = policy.model.sample_actions(
                images,
                image_masks,
                tokens,
                masks,
                noise=noise,
                num_steps=10,
            )[:, :, :action_dim]
            postprocessor.reset()
            actions = postprocessor(actions)
        return np.asarray(actions.squeeze(0).detach().cpu().numpy(), dtype=np.float32)

    return infer, policy, preprocessor


def find_global_index(dataset: LeRobotDataset, episode_index: int, frame_index: int) -> int:
    for idx in range(len(dataset)):
        row = dataset.hf_dataset[idx]
        if int(row["episode_index"].item()) == episode_index and int(row["frame_index"].item()) == frame_index:
            return idx
    raise KeyError(f"episode {episode_index} frame {frame_index} not found")


def run_open_loop(
    dataset: LeRobotDataset,
    policy_path: Path,
    dataset_root: Path,
    tokenizer_path: Path,
    out_dir: Path,
    device: str,
) -> dict[str, Any]:
    infer, _, _ = load_inferencer(policy_path, dataset_root, tokenizer_path, device, seed=42)
    cases = [
        ("box_f0", 0, 0),
        ("box_f50", 0, 50),
        ("mailer_f0", 120, 0),
        ("mailer_f50", 120, 50),
        ("wait_f0", 240, 0),
    ]
    samples: dict[str, dict[str, Any]] = {}
    for name, ep, fi in cases:
        gidx = find_global_index(dataset, ep, fi)
        item = dataset[gidx]
        img = item["observation.images.color_0"]
        state = np.asarray(item["observation.state"], dtype=np.float32)
        gt_action = np.asarray(item["action"], dtype=np.float32)
        pred = infer(img, state, DEFAULT_PROMPT, noise_seed=1000 + gidx)
        pred_a0 = pred[0]
        samples[name] = {
            "episode_index": ep,
            "frame_index": fi,
            "global_index": gidx,
            "gt_action0": gt_action.tolist(),
            "pred_action0": pred_a0.tolist(),
            "l2_pred_vs_gt": _l2(pred_a0, gt_action),
            "pred_shoulder_roll": {"L": _shoulder_rolls(pred_a0)[0], "R": _shoulder_rolls(pred_a0)[1]},
            "gt_shoulder_roll": {"L": _shoulder_rolls(gt_action)[0], "R": _shoulder_rolls(gt_action)[1]},
        }

    mailer_f0 = samples["mailer_f0"]["pred_action0"]
    box_f0 = samples["box_f0"]["pred_action0"]
    mailer_gt = samples["mailer_f0"]["gt_action0"]
    box_gt = samples["box_f0"]["gt_action0"]
    collapse = {
        "mailer_f0_pred_vs_box_gt_l2": _l2(mailer_f0, box_gt),
        "mailer_f0_pred_vs_mailer_gt_l2": _l2(mailer_f0, mailer_gt),
        "mailer_f0_pred_vs_box_f0_pred_l2": _l2(mailer_f0, box_f0),
        "mailer_f0_pred_closer_to_box_than_mailer_gt": _l2(mailer_f0, box_gt)
        < _l2(mailer_f0, mailer_gt),
        "interpretation": "",
    }
    if collapse["mailer_f0_pred_closer_to_box_than_mailer_gt"]:
        collapse["interpretation"] = (
            "Open-loop: mailer frame0 prediction is closer to box GT than mailer GT → routing collapse."
        )
    else:
        collapse["interpretation"] = (
            "Open-loop: mailer frame0 prediction is closer to mailer GT than box GT."
        )

    # Prompt sensitivity at open-loop (same image, different prompts)
    gidx = find_global_index(dataset, 120, 0)
    item = dataset[gidx]
    img = item["observation.images.color_0"]
    state = np.asarray(item["observation.state"], dtype=np.float32)
    prompt_rows = {}
    for pname, prompt in [
        ("default", DEFAULT_PROMPT),
        ("oracle_mailer", SHORT_MAILER_PROMPT),
        ("wrong_box", SHORT_BOX_PROMPT),
    ]:
        pred = infer(img, state, prompt, noise_seed=4242)
        prompt_rows[pname] = {
            "pred_action0": pred[0].tolist(),
            "shoulder_roll": {"L": _shoulder_rolls(pred[0])[0], "R": _shoulder_rolls(pred[0])[1]},
        }
    prompt_rows["oracle_vs_wrong_l2"] = _l2(
        np.array(prompt_rows["oracle_mailer"]["pred_action0"]),
        np.array(prompt_rows["wrong_box"]["pred_action0"]),
    )
    prompt_rows["language_sensitive"] = prompt_rows["oracle_vs_wrong_l2"] > 0.05

    result = {"samples": samples, "collapse_metrics": collapse, "mailer_f0_prompt_ablation": prompt_rows}
    (out_dir / "01_open_loop.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_per_task_val_loss(
    policy_path: Path,
    dataset_root: Path,
    tokenizer_path: Path,
    split_file: Path,
    policy_file: Path,
    train_stats_file: Path,
    out_dir: Path,
    device: str,
) -> dict[str, Any]:
    from lerobot.datasets.factory import resolve_delta_timestamps
    from lerobot.utils.pi05_training import read_split

    split = read_split(str(split_file))
    policy_json = json.loads(policy_file.read_text(encoding="utf-8"))
    ep_task = policy_json["episode_tasks"]

    config = PreTrainedConfig.from_pretrained(str(policy_path))
    config.pretrained_path = str(policy_path)
    config.device = device

    ds_meta = LeRobotDatasetMetadata(repo_id="local/diag", root=str(dataset_root))
    if train_stats_file.is_file():
        stats_payload = json.loads(train_stats_file.read_text(encoding="utf-8"))
        for key in ("observation.state", "action"):
            ds_meta.stats[key] = {name: np.asarray(val) for name, val in stats_payload[key].items()}

    policy = make_policy(config, ds_meta=ds_meta)
    policy.eval()
    overrides = {
        "device_processor": {"device": device},
        "tokenizer_processor": {"tokenizer_name": str(tokenizer_path), "local_files_only": True},
    }
    preprocessor, _ = make_pre_post_processors(
        policy_cfg=config,
        pretrained_path=str(policy_path),
        dataset_stats=ds_meta.stats,
        preprocessor_overrides=overrides,
    )

    delta_timestamps = resolve_delta_timestamps(config, ds_meta)
    dataset = LeRobotDataset(
        repo_id="local/diag",
        root=str(dataset_root),
        episodes=split["validation"],
        delta_timestamps=delta_timestamps,
        image_transforms=None,
    )

    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)
    totals: dict[str, list[float]] = defaultdict(list)
    with torch.inference_mode():
        for batch_idx, batch in enumerate(loader):
            ep = int(batch["episode_index"][0].item())
            task = ep_task[str(ep)]
            proc = preprocessor(batch)
            loss, _ = policy(proc)
            totals[task].append(float(loss.item()))

    summary = {
        task: {
            "frames": len(vals),
            "mean_loss": float(np.mean(vals)),
            "std_loss": float(np.std(vals)),
        }
        for task, vals in sorted(totals.items())
    }
    push_tasks = [summary[k]["mean_loss"] for k in ("push_box_to_bin", "nudge_mailer_to_bin") if k in summary]
    if len(push_tasks) == 2:
        summary["_delta_mailer_minus_box"] = (
            summary["nudge_mailer_to_bin"]["mean_loss"] - summary["push_box_to_bin"]["mean_loss"]
        )
    (out_dir / "03_per_task_val_loss.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_frame0_classifier(dataset_root: Path, policy_file: Path, out_dir: Path) -> dict[str, Any]:
    import cv2
    import pandas as pd

    policy_json = json.loads(policy_file.read_text(encoding="utf-8"))
    ep_task = policy_json["episode_tasks"]
    label_map = {"push_box_to_bin": 0, "nudge_mailer_to_bin": 1}
    dataset = LeRobotDataset(repo_id="local/diag", root=str(dataset_root))

    xs, ys = [], []
    for ep_str, task in ep_task.items():
        if task not in label_map:
            continue
        ep = int(ep_str)
        gidx = find_global_index(dataset, ep, 0)
        img = dataset[gidx]["observation.images.color_0"]
        if isinstance(img, torch.Tensor):
            if img.ndim == 3 and img.shape[0] == 3:
                rgb = img.permute(1, 2, 0).detach().cpu().numpy()
            else:
                rgb = img.detach().cpu().numpy()
        else:
            rgb = np.asarray(img)
        if rgb.max() <= 1.0:
            rgb = (rgb * 255.0).clip(0, 255).astype(np.uint8)
        small = cv2.resize(rgb, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        xs.append(small.reshape(-1))
        ys.append(label_map[task])

    x = np.stack(xs)
    y = np.array(ys)
    rng = np.random.default_rng(42)
    idx = np.arange(len(y))
    rng.shuffle(idx)
    split = int(len(y) * 0.8)
    train_idx, test_idx = idx[:split], idx[split:]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]

    mu = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train_n = (x_train - mu) / std
    x_test_n = (x_test - mu) / std
    x_train_b = np.concatenate([x_train_n, np.ones((len(x_train_n), 1), dtype=np.float32)], axis=1)

    weights = np.zeros((2, x_train_b.shape[1]), dtype=np.float64)
    for cls in (0, 1):
        mask = y_train == cls
        if mask.any():
            w, _, _, _ = np.linalg.lstsq(x_train_b[mask], np.ones(mask.sum()), rcond=None)
            weights[cls] = w

    logits = x_test_n @ weights[:, :-1].T + weights[:, -1]
    pred = logits.argmax(axis=1)
    acc = float((pred == y_test).mean())
    tp = {0: 0, 1: 0}
    fp = {0: 0, 1: 0}
    fn = {0: 0, 1: 0}
    for gt, pr in zip(y_test, pred, strict=True):
        if gt == pr:
            tp[gt] += 1
        else:
            fn[gt] += 1
            fp[pr] += 1
    per_class = {}
    for cls, name in ((0, "box"), (1, "mailer")):
        prec = tp[cls] / max(tp[cls] + fp[cls], 1)
        rec = tp[cls] / max(tp[cls] + fn[cls], 1)
        per_class[name] = {"precision": prec, "recall": rec, "support": int((y_test == cls).sum())}

    result = {
        "method": "Least-squares linear classifier on 64x64 RGB frame0 pixels (no sklearn)",
        "n_episodes_used": int(len(y)),
        "box_count": int((y == 0).sum()),
        "mailer_count": int((y == 1).sum()),
        "test_accuracy": acc,
        "per_class": per_class,
        "interpretation": (
            "High accuracy means vision can distinguish box vs mailer; low VLA routing implies binding failure."
            if acc > 0.85
            else "Low accuracy means frame0 vision may be ambiguous even for simple classifier."
        ),
    }
    (out_dir / "05_frame0_classifier.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--policy-path",
        type=Path,
        default=Path(
            "/home/user/Documents/zoo/sim/lerobot/outputs/"
            "package_sorting_pi05_1gpu_20260922_140103/checkpoints/last/pretrained_model"
        ),
    )
    p.add_argument(
        "--dataset-root",
        type=Path,
        default=Path(
            "/home/user/Documents/zoo/sim/lerobot/"
            "lerobot_sim_sorting_vla_officialhand_inactivepark_300_r2_20260921"
        ),
    )
    p.add_argument(
        "--tokenizer-path",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224"),
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=SIM_ROOT / "demo/diagnostic_routing_verification",
    )
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--skip-open-loop", action="store_true")
    p.add_argument("--skip-val-loss", action="store_true")
    p.add_argument("--skip-classifier", action="store_true")
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", "/home/user/Documents/zoo/sim/lerobot/hf_home/pi05")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("LEROBOT_TOKENIZER_NAME_OVERRIDE", str(args.tokenizer_path))
    os.environ.setdefault("LEROBOT_TOKENIZER_LOCAL_FILES_ONLY_OVERRIDE", "true")

    policy_file = args.dataset_root / "meta/sorting_frame_weight_policy.json"
    split_file = args.dataset_root / "meta/train_validation_split.json"
    train_stats = args.dataset_root / "meta/train_only_stats.json"

    summary: dict[str, Any] = {"policy_path": str(args.policy_path), "dataset_root": str(args.dataset_root)}

    dataset = LeRobotDataset(repo_id="local/diag", root=str(args.dataset_root))

    if not args.skip_open_loop:
        print("=== ① Open-loop ===", flush=True)
        summary["open_loop"] = run_open_loop(
            dataset, args.policy_path, args.dataset_root, args.tokenizer_path, args.out_dir, args.device
        )

    if not args.skip_val_loss:
        print("=== ③ Per-task val loss ===", flush=True)
        summary["per_task_val_loss"] = run_per_task_val_loss(
            args.policy_path,
            args.dataset_root,
            args.tokenizer_path,
            split_file,
            policy_file,
            train_stats,
            args.out_dir,
            args.device,
        )

    if not args.skip_classifier:
        print("=== ⑤ Frame0 classifier ===", flush=True)
        summary["frame0_classifier"] = run_frame0_classifier(args.dataset_root, policy_file, args.out_dir)

    (args.out_dir / "summary_partial.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote partial summary to {args.out_dir}", flush=True)


if __name__ == "__main__":
    main()
