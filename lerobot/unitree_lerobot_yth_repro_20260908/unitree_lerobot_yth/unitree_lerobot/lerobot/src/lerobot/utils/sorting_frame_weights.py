"""Per-frame loss weights for sorting-station PI0.5 training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_POLICY: dict[str, Any] = {
    "schema_version": 1,
    "weights": {
        "wait": 0.10,
        "lift_approach": 0.25,
        "press_sweep": 1.00,
        "hold": 0.50,
    },
    "phase_bounds": {
        "approach_end": 36,
        "sweep_end": 104,
    },
}

POLICY_FILENAME = "sorting_frame_weight_policy.json"


def frame_weight(task_id: str, frame_idx: int, policy: dict[str, Any]) -> float:
    weights = policy["weights"]
    bounds = policy["phase_bounds"]
    approach_end = int(bounds["approach_end"])
    sweep_end = int(bounds["sweep_end"])

    if task_id == "wait_no_package":
        return float(weights["wait"])
    if task_id in ("push_box_to_bin", "nudge_mailer_to_bin"):
        if frame_idx <= approach_end:
            return float(weights["lift_approach"])
        if frame_idx <= sweep_end:
            return float(weights["press_sweep"])
        return float(weights["hold"])
    return 1.0


def load_frame_weight_policy(root: str | Path) -> dict[str, Any] | None:
    path = Path(root) / "meta" / POLICY_FILENAME
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def lookup_frame_weight(policy: dict[str, Any], episode_index: int, frame_index: int) -> float:
    task_id = policy["episode_tasks"][str(episode_index)]
    return frame_weight(task_id, int(frame_index), policy)
