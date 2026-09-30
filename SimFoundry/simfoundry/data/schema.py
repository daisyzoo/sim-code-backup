"""Trajectory format shared by VLA and WAM dataloaders."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from simfoundry.embodiment import (
    D435I_INTRINSICS,
    EMBODIMENT_ID,
    G1_23DOF_JOINT_NAMES,
    KNOWN_EMBODIMENT_IDS,
)

TRAJECTORY_VERSION = 1


@dataclass
class TrajectoryEpisode:
    rgb: np.ndarray  # uint8 [T, 3, 480, 640]
    q: np.ndarray  # float32 [T, 23]
    action: np.ndarray  # float32 [T, 23]
    instruction: str
    scene_id: str
    task_id: str
    embodiment_id: str = EMBODIMENT_ID
    fx: float = D435I_INTRINSICS.fx
    fy: float = D435I_INTRINSICS.fy
    cx: float = D435I_INTRINSICS.cx
    cy: float = D435I_INTRINSICS.cy
    joint_names: tuple[str, ...] = G1_23DOF_JOINT_NAMES
    collect_meta: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        t = self.rgb.shape[0]
        if self.rgb.ndim != 4 or self.rgb.shape[1:] != (3, D435I_INTRINSICS.height, D435I_INTRINSICS.width):
            raise ValueError(f"rgb must be [T,3,480,640], got {self.rgb.shape}")
        if self.q.shape != (t, 23):
            raise ValueError(f"q must be [T,23], got {self.q.shape}")
        if self.action.shape != (t, 23):
            raise ValueError(f"action must be [T,23], got {self.action.shape}")
        if self.embodiment_id not in KNOWN_EMBODIMENT_IDS:
            raise ValueError(f"unexpected embodiment_id={self.embodiment_id}")
        if len(self.joint_names) != 23:
            raise ValueError("joint_names must list the 23 DoF")


def save_episode(episode: TrajectoryEpisode, path: str | Path) -> Path:
    episode.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        rgb=episode.rgb.astype(np.uint8),
        q=episode.q.astype(np.float32),
        action=episode.action.astype(np.float32),
        instruction=np.array(episode.instruction),
        scene_id=np.array(episode.scene_id),
        task_id=np.array(episode.task_id),
        embodiment_id=np.array(episode.embodiment_id),
        intrinsics=np.asarray([episode.fx, episode.fy, episode.cx, episode.cy], dtype=np.float32),
        joint_names=np.array(list(episode.joint_names)),
        version=np.asarray(TRAJECTORY_VERSION),
        collect_meta=np.array(json.dumps(episode.collect_meta)),
    )
    return path


def _as_str(value: Any) -> str:
    arr = np.asarray(value)
    if arr.ndim == 0:
        item = arr.item()
        return item.decode() if isinstance(item, bytes) else str(item)
    return str(arr)


def load_episode(path: str | Path) -> TrajectoryEpisode:
    data: Any = np.load(path, allow_pickle=False)
    collect_meta: dict[str, Any] = {}
    if "collect_meta" in data:
        raw = data["collect_meta"]
        item = np.asarray(raw).item()
        text = item.decode() if isinstance(item, bytes) else str(item)
        if text:
            collect_meta = json.loads(text)
    episode = TrajectoryEpisode(
        rgb=data["rgb"],
        q=data["q"],
        action=data["action"],
        instruction=_as_str(data["instruction"]),
        scene_id=_as_str(data["scene_id"]),
        task_id=_as_str(data["task_id"]),
        embodiment_id=_as_str(data["embodiment_id"]),
        fx=float(data["intrinsics"][0]),
        fy=float(data["intrinsics"][1]),
        cx=float(data["intrinsics"][2]),
        cy=float(data["intrinsics"][3]),
        joint_names=tuple(_as_str(x) for x in data["joint_names"].tolist()),
        collect_meta=collect_meta,
    )
    episode.validate()
    return episode
