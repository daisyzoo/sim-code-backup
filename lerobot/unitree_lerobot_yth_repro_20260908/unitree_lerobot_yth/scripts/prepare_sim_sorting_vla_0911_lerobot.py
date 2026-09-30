#!/usr/bin/env python3
"""Convert VLA-0911 Unitree JSON → LeRobot v3.0.

Keeps ``observation.images.color_0`` and the collect-time unified English prompt.
Does not rewrite task text from Chinese.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "unitree_lerobot" / "lerobot" / "src"))

from wrap_flat_unitree_json_dataset import Args as WrapArgs, main as wrap_main  # noqa: E402

UNIFIED_PROMPT = (
    "Sort the package on the table by type. If there is no package on the table, keep both "
    "arms still and wait. If it is a black bag, press and hold the bag down with the left "
    "hand, then push it to the left sorting area. If it is a box, press and hold the box "
    "down with the right hand, then push it to the right sorting area."
)
JOINT_ORDER = [
    "left_arm_joint_0",
    "left_arm_joint_1",
    "left_arm_joint_2",
    "left_arm_joint_3",
    "left_arm_joint_4",
    "right_arm_joint_0",
    "right_arm_joint_1",
    "right_arm_joint_2",
    "right_arm_joint_3",
    "right_arm_joint_4",
    "waist_yaw_joint",
]


def _stats_block(arr: np.ndarray) -> dict:
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 11:
        raise ValueError(f"expected [N,11], got {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError("non-finite values in stats array")
    return {
        "min": arr.min(axis=0).tolist(),
        "max": arr.max(axis=0).tolist(),
        "mean": arr.mean(axis=0).tolist(),
        "std": arr.std(axis=0, ddof=0).tolist(),
        "count": [int(arr.shape[0])],
        "q01": np.quantile(arr, 0.01, axis=0).tolist(),
        "q10": np.quantile(arr, 0.10, axis=0).tolist(),
        "q50": np.quantile(arr, 0.50, axis=0).tolist(),
        "q90": np.quantile(arr, 0.90, axis=0).tolist(),
        "q99": np.quantile(arr, 0.99, axis=0).tolist(),
    }


def _episode_task_ids(source_root: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    for path in sorted(source_root.glob("episode_*")):
        if not (path / "data.json").is_file():
            continue
        eid = int(path.name.split("_")[-1])
        payload = json.loads((path / "data.json").read_text())
        out[eid] = payload["info"]["simfoundry"]["task_id"]
        goal = payload["text"]["goal"]
        if goal != UNIFIED_PROMPT:
            raise SystemExit(f"{path.name} goal is not the unified prompt:\n{goal}")
    return out


def convert(raw_dir: Path, out_root: Path, repo_id: str) -> None:
    from unitree_lerobot.utils.constants import ROBOT_CONFIGS
    from unitree_lerobot.utils.convert_unitree_json_to_lerobot import (
        DatasetConfig,
        JsonDataset,
        create_empty_dataset,
        populate_dataset,
        write_detailed_task_annotations,
    )

    robot_type = "Unitree_G1_23Dof_Arms5_Waist1"
    ROBOT_CONFIGS[robot_type] = replace(
        ROBOT_CONFIGS[robot_type],
        cameras=["color_0"],
        camera_to_image_key={"color_0": "color_0"},
    )

    class PromptedJsonDataset(JsonDataset):
        def get_item(self, index: int | None = None) -> dict:
            item = super().get_item(index)
            item["task"] = UNIFIED_PROMPT
            return item

    if out_root.exists():
        shutil.rmtree(out_root)
    json_dataset = PromptedJsonDataset(raw_dir, robot_type)
    dataset = create_empty_dataset(
        repo_id,
        robot_type=robot_type,
        fps=json_dataset.fps,
        mode="video",
        root=out_root,
        has_effort=False,
        has_velocity=False,
        dataset_config=DatasetConfig(image_writer_processes=4, image_writer_threads=4),
    )
    populate_dataset(dataset, raw_dir, robot_type=robot_type, json_dataset=json_dataset)
    write_detailed_task_annotations(dataset.root, json_dataset)
    dataset.finalize()
    print(f"converted -> {out_root}  episodes={json_dataset.__len__()} fps={json_dataset.fps}")


def _load_train_arrays(out_root: Path, train: list[int]) -> tuple[np.ndarray, np.ndarray]:
    import pyarrow.parquet as pq

    train_set = set(train)
    states, actions = [], []
    for path in sorted((out_root / "data").glob("chunk-*/file-*.parquet")):
        table = pq.read_table(path, columns=["episode_index", "observation.state", "action"])
        ep = table.column("episode_index").to_numpy()
        st = table.column("observation.state").to_pylist()
        ac = table.column("action").to_pylist()
        for i, episode in enumerate(ep):
            if int(episode) not in train_set:
                continue
            states.append(np.asarray(st[i], dtype=np.float32).reshape(-1))
            actions.append(np.asarray(ac[i], dtype=np.float32).reshape(-1))
    if not states:
        raise RuntimeError("no training rows in parquet")
    return np.stack(states, axis=0), np.stack(actions, axis=0)


def write_split_and_stats(out_root: Path, source_root: Path, seed: int = 42) -> tuple[list[int], list[int], int]:
    task_ids = _episode_task_ids(source_root)
    by_task: dict[str, list[int]] = defaultdict(list)
    for eid, tid in sorted(task_ids.items()):
        by_task[tid].append(eid)
    rng = np.random.RandomState(seed)
    val: list[int] = []
    for tid, ids in by_task.items():
        shuffled = list(ids)
        rng.shuffle(shuffled)
        n_val = 1 if len(shuffled) <= 12 else max(1, round(0.1 * len(shuffled)))
        val.extend(shuffled[:n_val])
    val = sorted(set(val))
    train = sorted(set(task_ids) - set(val))
    split = {
        "schema_version": 1,
        "grouping": "stratified_by_task_id",
        "task_counts": {k: len(v) for k, v in by_task.items()},
        "requested_seed": seed,
        "task": UNIFIED_PROMPT,
        "joint_order": JOINT_ORDER,
        "train": train,
        "validation": val,
        "source": str(source_root),
    }
    split_path = out_root / "meta" / "train_validation_split.json"
    split_path.write_text(json.dumps(split, indent=2), encoding="utf-8")
    states, actions = _load_train_arrays(out_root, train)
    if states.shape[1] != 11 or actions.shape[1] != 11:
        raise ValueError(f"expected 11D, got state {states.shape} action {actions.shape}")
    payload = {
        "observation.state": _stats_block(states),
        "action": _stats_block(actions),
        "episode_indices": train,
        "joint_order": JOINT_ORDER,
    }
    stats_path = out_root / "meta" / "train_only_stats.json"
    stats_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    info = json.loads((out_root / "meta" / "info.json").read_text())
    feats = info.get("features", {})
    cam = "observation.images.color_0"
    if cam not in feats:
        raise SystemExit(f"camera key {cam} missing; have {list(feats)}")
    print(
        f"split train={len(train)} val={len(val)} train_frames={states.shape[0]} "
        f"camera={cam} tasks={dict(split['task_counts'])}"
    )
    print(f"  wrote {split_path}")
    print(f"  wrote {stats_path}")
    return train, val, int(states.shape[0])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source-root",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/SimFoundry/datasets/sorting_station_g1_23_unitree_vla_0911"),
    )
    p.add_argument(
        "--wrap-root",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/lerobot/data/raw/sorting_station_g1_23_unitree_vla_0911_wrapped"),
    )
    p.add_argument(
        "--out-root",
        type=Path,
        default=Path("/home/user/Documents/zoo/sim/lerobot/lerobot_sim_sorting_vla_0911"),
    )
    p.add_argument("--repo-id", default="local/sorting_station_sim_vla_0911")
    p.add_argument("--skip-convert", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    _episode_task_ids(args.source_root)
    wrap_main(
        WrapArgs(
            source_root=args.source_root,
            output_root=args.wrap_root,
            task_name="sorting_station_sim_vla_0911",
            mode="symlink",
            overwrite=True,
        )
    )
    if not args.skip_convert:
        convert(args.wrap_root, args.out_root, args.repo_id)
    train, val, n_frames = write_split_and_stats(args.out_root, args.source_root)
    steps_path = args.out_root / "meta" / "recommended_train_steps.json"
    steps_path.write_text(
        json.dumps(
            {
                "train_episodes": len(train),
                "val_episodes": len(val),
                "train_frames": n_frames,
                "one_epoch_steps": n_frames,
                "two_epoch_steps": n_frames * 2,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {steps_path}")


if __name__ == "__main__":
    main()
