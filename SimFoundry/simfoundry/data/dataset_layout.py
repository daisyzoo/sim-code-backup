"""Canonical dataset paths for sorting-station collection (one task per directory tree).

0831 batch: ``push_box_to_bin`` only → ``sorting_station_g1_23_0831``.
Other stump tasks use sibling dirs so training mixes are explicit.
"""

from __future__ import annotations

from pathlib import Path

# task_id → (npz_dir_name, unitree_dir_name) under SimFoundry root / datasets/
SORTING_TASK_DATASET_DIRS: dict[str, tuple[str, str]] = {
    "push_box_to_bin": (
        "sorting_station_g1_23_0831",
        "sorting_station_g1_23_unitree_0831",
    ),
    "nudge_mailer_to_bin": (
        "sorting_station_g1_23_mailer_0831",
        "sorting_station_g1_23_mailer_unitree_0831",
    ),
    "sweep_parcels_apart": (
        "sorting_station_g1_23_sweep_0831",
        "sorting_station_g1_23_sweep_unitree_0831",
    ),
}

SORTING_SCENE_ID = "sorting_station_g1_23"


def sorting_dataset_dirs(
    task_id: str,
    *,
    root: Path,
) -> tuple[Path, Path] | None:
    """Return (npz_dir, unitree_dir) for a known sorting task, or None to use registry default."""
    pair = SORTING_TASK_DATASET_DIRS.get(task_id)
    if pair is None:
        return None
    npz_name, unitree_name = pair
    base = root / "datasets"
    return base / npz_name, base / unitree_name
