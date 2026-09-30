"""Export SimFoundry npz episodes to HuggingFace LeRobotDataset v2.1.

Target consumers: ACT / Pi0 / SmolVLA via ``lerobot``. Isaac remains the
simulation producer; this module is the training-side handoff.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np
import pandas as pd

from simfoundry.data.schema import TrajectoryEpisode, load_episode
from simfoundry.embodiment import D435I_INTRINSICS, EMBODIMENT_ID, G1_23DOF_JOINT_NAMES, KNOWN_EMBODIMENT_IDS

# HF LeRobot / ACT-Pi0 convention.
IMAGE_KEY = "observation.images.d435i"
STATE_KEY = "observation.state"
ACTION_KEY = "action"
CODEBASE_VERSION = "v2.1"
DEFAULT_FPS = 30.0
CHUNKS_SIZE = 1000


@dataclass(frozen=True)
class LeRobotExportResult:
    root: Path
    num_episodes: int
    num_frames: int
    num_tasks: int


def _episode_chunk(episode_index: int) -> int:
    return episode_index // CHUNKS_SIZE


def _stats_1d(arr: np.ndarray) -> dict[str, list[float] | list[int]]:
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, None]
    return {
        "min": arr.min(axis=0).tolist(),
        "max": arr.max(axis=0).tolist(),
        "mean": arr.mean(axis=0).tolist(),
        "std": arr.std(axis=0).tolist(),
        "count": [int(arr.shape[0])],
    }


def _stats_image_nchw(rgb: np.ndarray) -> dict[str, Any]:
    """Per-channel image stats with shape [C,1,1] (LeRobot-friendly, compact)."""
    x = rgb.astype(np.float64) / 255.0  # [T,C,H,W]
    mean = x.mean(axis=(0, 2, 3)).reshape(3, 1, 1)
    std = x.std(axis=(0, 2, 3)).reshape(3, 1, 1)
    amin = x.min(axis=(0, 2, 3)).reshape(3, 1, 1)
    amax = x.max(axis=(0, 2, 3)).reshape(3, 1, 1)
    return {
        "min": amin.tolist(),
        "max": amax.tolist(),
        "mean": mean.tolist(),
        "std": std.tolist(),
        "count": [int(rgb.shape[0])],
    }


def _write_mp4_nchw(rgb: np.ndarray, path: Path, fps: float) -> str:
    """rgb: uint8 [T,3,H,W] RGB → MP4. Returns the fourcc actually used."""
    if rgb.ndim != 4 or rgb.shape[1] != 3:
        raise ValueError(f"expected [T,3,H,W], got {rgb.shape}")
    t, _, h, w = rgb.shape
    path.parent.mkdir(parents=True, exist_ok=True)
    # Prefer mp4v on Linux workstations: OpenCV's avc1/H264 often binds to broken
    # h264_v4l2m2m and only emits noisy errors. LeRobot / torchvision can decode mp4v.
    last_error: Exception | None = None
    for fourcc_name in ("mp4v", "avc1"):
        fourcc = cv2.VideoWriter_fourcc(*fourcc_name)
        writer = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
        if not writer.isOpened():
            writer.release()
            continue
        try:
            for i in range(t):
                bgr = cv2.cvtColor(rgb[i].transpose(1, 2, 0), cv2.COLOR_RGB2BGR)
                writer.write(bgr)
        except Exception as exc:  # noqa: BLE001 — try next codec
            last_error = exc
            writer.release()
            if path.exists():
                path.unlink(missing_ok=True)
            continue
        writer.release()
        if path.exists() and path.stat().st_size > 0:
            return fourcc_name
        if path.exists():
            path.unlink(missing_ok=True)
    raise RuntimeError(f"failed to write video {path}; last_error={last_error}")


def _build_info(
    *,
    total_episodes: int,
    total_frames: int,
    total_tasks: int,
    fps: float,
    height: int,
    width: int,
    joint_names: tuple[str, ...],
    video_codec: str,
) -> dict[str, Any]:
    return {
        "codebase_version": CODEBASE_VERSION,
        "robot_type": EMBODIMENT_ID,
        "total_episodes": total_episodes,
        "total_frames": total_frames,
        "total_tasks": total_tasks,
        "total_videos": total_episodes,
        "total_chunks": max(1, (total_episodes + CHUNKS_SIZE - 1) // CHUNKS_SIZE) if total_episodes else 0,
        "chunks_size": CHUNKS_SIZE,
        "fps": fps,
        "splits": {"train": f"0:{total_episodes}"},
        "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
        "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        "features": {
            IMAGE_KEY: {
                "dtype": "video",
                "shape": [height, width, 3],
                "names": ["height", "width", "channels"],
                "info": {
                    "video.fps": fps,
                    "video.codec": video_codec,
                    "video.pix_fmt": "yuv420p",
                    "video.is_depth_map": False,
                    "has_audio": False,
                },
            },
            STATE_KEY: {
                "dtype": "float32",
                "shape": [len(joint_names)],
                "names": list(joint_names),
            },
            ACTION_KEY: {
                "dtype": "float32",
                "shape": [len(joint_names)],
                "names": list(joint_names),
            },
            "timestamp": {"dtype": "float32", "shape": [1]},
            "frame_index": {"dtype": "int64", "shape": [1]},
            "episode_index": {"dtype": "int64", "shape": [1]},
            "index": {"dtype": "int64", "shape": [1]},
            "task_index": {"dtype": "int64", "shape": [1]},
        },
    }


def export_episodes_to_lerobot(
    episodes: Iterable[TrajectoryEpisode],
    output_dir: str | Path,
    *,
    fps: float = DEFAULT_FPS,
    overwrite: bool = False,
) -> LeRobotExportResult:
    """Write a LeRobot v2.1 dataset from in-memory SimFoundry episodes."""
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"{output_dir} is not empty; pass overwrite=True to replace")
    if overwrite and output_dir.exists():
        # Only wipe known leaves so we don't delete unrelated user data next door.
        for sub in ("meta", "data", "videos"):
            path = output_dir / sub
            if path.exists():
                import shutil

                shutil.rmtree(path)

    episode_list = list(episodes)
    if not episode_list:
        raise ValueError("no episodes to export")

    tasks: dict[str, int] = {}
    episodes_meta: list[dict[str, Any]] = []
    episodes_stats: list[dict[str, Any]] = []
    global_index = 0
    height = D435I_INTRINSICS.height
    width = D435I_INTRINSICS.width

    video_codec = "mp4v"
    ref_joint_names: tuple[str, ...] | None = None
    ref_embodiment_id: str | None = None
    for ep_idx, episode in enumerate(episode_list):
        episode.validate()
        if episode.rgb.shape[1:] != (3, height, width):
            raise ValueError(f"episode {ep_idx}: rgb shape {episode.rgb.shape} != [T,3,{height},{width}]")
        if len(episode.joint_names) != 23:
            raise ValueError(f"episode {ep_idx}: expected 23 joint names, got {len(episode.joint_names)}")
        if episode.embodiment_id not in KNOWN_EMBODIMENT_IDS:
            raise ValueError(f"episode {ep_idx}: unknown embodiment_id={episode.embodiment_id}")
        if ref_joint_names is None:
            ref_joint_names = episode.joint_names
            ref_embodiment_id = episode.embodiment_id
        elif episode.joint_names != ref_joint_names:
            raise ValueError(f"episode {ep_idx}: joint_names must match the first episode in the batch")
        elif episode.embodiment_id != ref_embodiment_id:
            raise ValueError(f"episode {ep_idx}: embodiment_id must match the first episode in the batch")

        instruction = episode.instruction
        if instruction not in tasks:
            tasks[instruction] = len(tasks)
        task_index = tasks[instruction]
        t = episode.rgb.shape[0]
        chunk = _episode_chunk(ep_idx)

        data_path = output_dir / "data" / f"chunk-{chunk:03d}" / f"episode_{ep_idx:06d}.parquet"
        video_path = (
            output_dir / "videos" / f"chunk-{chunk:03d}" / IMAGE_KEY / f"episode_{ep_idx:06d}.mp4"
        )
        data_path.parent.mkdir(parents=True, exist_ok=True)
        video_codec = _write_mp4_nchw(episode.rgb, video_path, fps)

        timestamps = (np.arange(t, dtype=np.float32) / float(fps)).reshape(t, 1)
        frame_index = np.arange(t, dtype=np.int64).reshape(t, 1)
        episode_index = np.full((t, 1), ep_idx, dtype=np.int64)
        index = np.arange(global_index, global_index + t, dtype=np.int64).reshape(t, 1)
        task_indices = np.full((t, 1), task_index, dtype=np.int64)

        # Store vectors as fixed-size lists for parquet (HF datasets friendly).
        df = pd.DataFrame(
            {
                STATE_KEY: [row.astype(np.float32) for row in episode.q],
                ACTION_KEY: [row.astype(np.float32) for row in episode.action],
                "timestamp": timestamps.reshape(-1).astype(np.float32),
                "frame_index": frame_index.reshape(-1),
                "episode_index": episode_index.reshape(-1),
                "index": index.reshape(-1),
                "task_index": task_indices.reshape(-1),
            }
        )
        df.to_parquet(data_path, index=False)

        episodes_meta.append(
            {
                "episode_index": ep_idx,
                "tasks": [instruction],
                "length": int(t),
                "scene_id": episode.scene_id,
                "task_id": episode.task_id,
                "embodiment_id": episode.embodiment_id,
            }
        )
        episodes_stats.append(
            {
                "episode_index": ep_idx,
                "stats": {
                    STATE_KEY: _stats_1d(episode.q),
                    ACTION_KEY: _stats_1d(episode.action),
                    IMAGE_KEY: _stats_image_nchw(episode.rgb),
                    "timestamp": _stats_1d(timestamps),
                    "frame_index": _stats_1d(frame_index.astype(np.float64)),
                    "episode_index": _stats_1d(episode_index.astype(np.float64)),
                    "index": _stats_1d(index.astype(np.float64)),
                    "task_index": _stats_1d(task_indices.astype(np.float64)),
                },
            }
        )
        global_index += t

    meta_dir = output_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    assert ref_joint_names is not None and ref_embodiment_id is not None
    info = _build_info(
        total_episodes=len(episode_list),
        total_frames=global_index,
        total_tasks=len(tasks),
        fps=fps,
        height=height,
        width=width,
        joint_names=ref_joint_names,
        video_codec=video_codec,
    )
    (meta_dir / "info.json").write_text(json.dumps(info, indent=2) + "\n")

    with (meta_dir / "tasks.jsonl").open("w", encoding="utf-8") as f:
        for task, task_index in sorted(tasks.items(), key=lambda kv: kv[1]):
            f.write(json.dumps({"task_index": task_index, "task": task}, ensure_ascii=False) + "\n")

    with (meta_dir / "episodes.jsonl").open("w", encoding="utf-8") as f:
        for row in episodes_meta:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (meta_dir / "episodes_stats.jsonl").open("w", encoding="utf-8") as f:
        for row in episodes_stats:
            f.write(json.dumps(row) + "\n")

    # Extra sidecar for SimFoundry ↔ real-robot alignment (ignored by stock LeRobot loaders).
    (meta_dir / "simfoundry.json").write_text(
        json.dumps(
            {
                "embodiment_id": ref_embodiment_id,
                "joint_names": list(ref_joint_names),
                "camera": {
                    "key": IMAGE_KEY,
                    "width": width,
                    "height": height,
                    "fx": D435I_INTRINSICS.fx,
                    "fy": D435I_INTRINSICS.fy,
                    "cx": D435I_INTRINSICS.cx,
                    "cy": D435I_INTRINSICS.cy,
                    "model": "Intel RealSense D435i",
                },
                "source": "simfoundry_npz",
                "notes": (
                    "Isaac SimFoundry intermediate npz → LeRobot v2.1. "
                    "Train ACT/Pi0/SmolVLA with the same keys as real-robot LeRobot captures."
                ),
            },
            indent=2,
        )
        + "\n"
    )

    return LeRobotExportResult(
        root=output_dir,
        num_episodes=len(episode_list),
        num_frames=global_index,
        num_tasks=len(tasks),
    )


def export_npz_dir_to_lerobot(
    npz_dir: str | Path,
    output_dir: str | Path,
    *,
    pattern: str = "*.npz",
    fps: float = DEFAULT_FPS,
    overwrite: bool = False,
) -> LeRobotExportResult:
    """Load all matching npz episodes and export a LeRobot v2.1 dataset."""
    npz_dir = Path(npz_dir)
    paths = sorted(npz_dir.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"no files matching {pattern} under {npz_dir}")
    episodes = [load_episode(p) for p in paths]
    return export_episodes_to_lerobot(episodes, output_dir, fps=fps, overwrite=overwrite)
