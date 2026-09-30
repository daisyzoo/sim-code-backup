"""Opt-in helpers; legacy datasets and LoRA tasks keep their existing behavior."""
import json
import os
from pathlib import Path
import numpy as np


def read_split(path):
    split = json.loads(Path(path).read_text())
    train, val = split["train"], split["validation"]
    if not train or not val or any(type(ep) is not int or ep < 0 for ep in train + val):
        raise ValueError("Expected nonempty nonnegative integer episode lists")
    if len(set(train)) != len(train) or len(set(val)) != len(val) or set(train) & set(val):
        raise ValueError("Duplicate or overlapping train/validation episodes")
    return split


def apply_training_stats(cfg, dataset):
    path = os.environ.get("PI05_TRAIN_STATS_FILE")
    if not path:
        return
    split = read_split(os.environ["PI05_SHARED_SPLIT_FILE"])
    if cfg.dataset.episodes not in (split["train"], split["validation"]):
        raise ValueError("Dataset selection differs from declared split")
    payload = json.loads(Path(path).read_text())
    if payload["episode_indices"] != split["train"]:
        raise ValueError("Statistics must come from the declared training episodes")
    frames = sum(dataset.meta.episodes[ep]["dataset_to_index"] - dataset.meta.episodes[ep]["dataset_from_index"] for ep in split["train"])
    if {int(ep) for ep in dataset.hf_dataset["episode_index"]} != set(cfg.dataset.episodes):
        raise ValueError("Actual loaded episode coverage differs from requested split")
    for key in ("observation.state", "action"):
        dim = dataset.meta.features[key]["shape"][0]
        stats = {name: np.asarray(value) for name, value in payload[key].items()}
        if stats["count"].tolist() != [frames]:
            raise ValueError(f"Incorrect training statistics frame count: {key}")
        for field in ("min", "max", "mean", "std", "q01", "q99"):
            if stats[field].shape != (dim,) or not np.isfinite(stats[field]).all():
                raise ValueError(f"Invalid {key}/{field}; expected dimension {dim}")
        dataset.meta.stats[key] = stats


def audit_parameters(policy, optimizer, output_dir, is_main_process):
    if os.environ.get("PI05_PARAMETER_AUDIT", "0") != "1":
        return
    named = dict(policy.named_parameters())
    trainable = {name: p for name, p in named.items() if p.requires_grad}
    optimized = {id(p) for group in optimizer.param_groups for p in group["params"]}
    if not trainable or any(id(p) not in optimized for p in trainable.values()):
        raise ValueError("Empty or incompletely optimized trainable parameter set")
    if os.environ.get("PI05_REQUIRE_EXPERT_ONLY", "0") == "1":
        cfg = policy.config
        if not cfg.train_expert_only or cfg.lora_rank != 0 or not cfg.mask_action_padding:
            raise ValueError("Expected expert-only, no LoRA and padding loss mask")
        allowed = ("gemma_expert", "action_in_proj", "action_out_proj", "time_mlp_in", "time_mlp_out")
        if any(not any(part in name for part in allowed) for name in trainable):
            raise ValueError("Unexpected trainable parameters outside action modules")
    if os.environ.get("PI05_REQUIRE_LANGUAGE_ADAPTER", "0") == "1":
        cfg = policy.config
        if not cfg.train_expert_with_language_lora or not cfg.mask_action_padding:
            raise ValueError("Expected full expert plus language LoRA with padding mask")
        action_parts = ("gemma_expert", "action_in_proj", "action_out_proj", "time_mlp_in", "time_mlp_out")
        language = {n: p for n, p in trainable.items() if "paligemma" in n and "language_model" in n and "lora_" in n}
        if not language:
            raise ValueError("Language adapters missing from optimized parameters")
        for name, param in named.items():
            action = any(part in name for part in action_parts)
            allowed = action or name in language
            if param.requires_grad != allowed:
                raise ValueError(f"Incorrect language-adapter training scope: {name}")
    if not is_main_process:
        return
    lookup = {id(p): name for name, p in named.items()}
    report = {"total_parameters": sum(p.numel() for p in named.values()),
              "trainable_parameters": sum(p.numel() for p in trainable.values()),
              "trainable": [{"name": n, "shape": list(p.shape), "count": p.numel()} for n, p in trainable.items()],
              "optimizer_groups": [{"lr": g["lr"], "weight_decay": g.get("weight_decay"),
                                    "parameters": [lookup.get(id(p), "<unnamed>") for p in g["params"]]} for g in optimizer.param_groups]}
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "trainable_parameters.json").write_text(json.dumps(report, indent=2) + "\n")
