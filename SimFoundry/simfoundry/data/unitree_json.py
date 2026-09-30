"""Unitree EpisodeWriter-compatible JSON export (matches pick_cup_soring_0824 layout).

The real dataset folder name is legacy; teleop on the sorting station is a
**push/sort** task (11 DoF: 5+5 arms + waist_yaw), not pick-and-place.

Layout per episode::

    episode_XXXX/
      colors/NNNNNN_color_0.jpg   # BGR JPEG, 640x480
      data.json

``data.json`` schema matches ``unitree_lerobot/.../episode_writer.py`` used by
the real G1 teleop stack. Training typically consumes 11-D::

    left_arm.qpos(5) + right_arm.qpos(5) + body.qpos[0](1)
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np

from simfoundry.data.schema import TrajectoryEpisode
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES, u1_sorting_default_qpos_np

# Indices into G1_U1_23DOF_JOINT_NAMES / TrajectoryEpisode.q
_LEFT_ARM = slice(13, 18)  # shoulder pitch/roll/yaw, elbow, wrist_roll
_RIGHT_ARM = slice(18, 23)
_WAIST_YAW = 12

_LEFT_ARM_NAMES = [
    "kLeftShoulderPitch",
    "kLeftShoulderRoll",
    "kLeftShoulderYaw",
    "kLeftElbow",
    "kLeftWristRoll",
]
_RIGHT_ARM_NAMES = [
    "kRightShoulderPitch",
    "kRightShoulderRoll",
    "kRightShoulderYaw",
    "kRightElbow",
    "kRightWristRoll",
]
_BODY_NAMES = ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"]


def _qpos_group(values: np.ndarray) -> dict[str, list]:
    return {"qpos": [float(x) for x in np.asarray(values, dtype=np.float64).tolist()], "qvel": [], "torque": []}


def _split_23(q: np.ndarray) -> dict[str, dict[str, list]]:
    """Map 23-DoF U1 vector → Unitree left_arm / right_arm / body groups."""
    q = np.asarray(q, dtype=np.float64).reshape(-1)
    if q.shape[0] != 23:
        raise ValueError(f"expected 23-DoF q, got {q.shape}")
    body = np.asarray([q[_WAIST_YAW], 0.0, 0.0], dtype=np.float64)
    return {
        "left_arm": _qpos_group(q[_LEFT_ARM]),
        "right_arm": _qpos_group(q[_RIGHT_ARM]),
        "left_ee": _qpos_group([]),
        "right_ee": _qpos_group([]),
        "body": _qpos_group(body),
    }


def _rgb_chw_to_bgr_hwc(frame: np.ndarray) -> np.ndarray:
    """uint8 [3,H,W] or [H,W,3] RGB → uint8 [H,W,3] BGR for cv2.imwrite."""
    x = np.asarray(frame)
    if x.ndim == 3 and x.shape[0] in (3, 4):
        rgb = np.transpose(x[:3], (1, 2, 0))
    elif x.ndim == 3 and x.shape[-1] in (3, 4):
        rgb = x[..., :3]
    else:
        raise ValueError(f"unexpected rgb shape {x.shape}")
    return rgb[..., ::-1].copy()


def next_episode_id(task_dir: Path) -> int:
    task_dir = Path(task_dir)
    if not task_dir.is_dir():
        return 0
    ids = []
    for p in task_dir.iterdir():
        if p.is_dir() and p.name.startswith("episode_"):
            try:
                ids.append(int(p.name.split("_")[-1]))
            except ValueError:
                continue
    return (max(ids) + 1) if ids else 0


def export_episode_unitree_json(
    episode: TrajectoryEpisode,
    task_dir: str | Path,
    *,
    episode_id: int | None = None,
    fps: float = 15.0,
    goal: str | None = None,
    desc: str | None = None,
    steps: str = "",
    author: str = "simfoundry",
) -> Path:
    """Write one episode in Unitree JSON layout under ``task_dir/episode_XXXX``."""
    import cv2

    task_dir = Path(task_dir)
    task_dir.mkdir(parents=True, exist_ok=True)
    eid = next_episode_id(task_dir) if episode_id is None else int(episode_id)
    ep_dir = task_dir / f"episode_{eid:04d}"
    color_dir = ep_dir / "colors"
    color_dir.mkdir(parents=True, exist_ok=True)

    t = episode.rgb.shape[0]
    if episode.q.shape[0] != t or episode.action.shape[0] != t:
        raise ValueError("rgb/q/action length mismatch")

    # Prefer U1 joint naming when embodiment is U1; else still slice 23-DoF the same way.
    joint_names = {
        "left_arm": list(_LEFT_ARM_NAMES),
        "left_ee": [],
        "right_arm": list(_RIGHT_ARM_NAMES),
        "right_ee": [],
        "body": list(_BODY_NAMES),
    }
    info: dict[str, Any] = {
        "version": "1.0.0",
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "author": author,
        "image": {"width": 640, "height": 480, "fps": float(fps)},
        "depth": {"width": 640, "height": 480, "fps": float(fps)},
        "audio": {"sample_rate": 16000, "channels": 1, "format": "PCM", "bits": 16},
        "joint_names": joint_names,
        "tactile_names": {"left_ee": [], "right_ee": []},
        "sim_state": f"scene={episode.scene_id};task={episode.task_id};embodiment={episode.embodiment_id}",
        "simfoundry": {
            "scene_id": episode.scene_id,
            "task_id": episode.task_id,
            "embodiment_id": episode.embodiment_id,
            "full_joint_names": list(episode.joint_names or G1_U1_23DOF_JOINT_NAMES),
            **({"collect": episode.collect_meta} if episode.collect_meta else {}),
        },
    }
    text = {
        "goal": goal if goal is not None else episode.instruction,
        "desc": desc if desc is not None else episode.instruction,
        "steps": steps,
    }

    default_q = u1_sorting_default_qpos_np()
    frames: list[dict[str, Any]] = []
    for i in range(t):
        color_name = f"{i:06d}_color_0.jpg"
        bgr = _rgb_chw_to_bgr_hwc(episode.rgb[i])
        if bgr.shape[0] != 480 or bgr.shape[1] != 640:
            bgr = cv2.resize(bgr, (640, 480), interpolation=cv2.INTER_AREA)
        if not cv2.imwrite(str(color_dir / color_name), bgr):
            raise RuntimeError(f"failed to write {color_dir / color_name}")
        q_abs = np.asarray(episode.q[i], dtype=np.float64)
        # Real teleop logs absolute qpos in both states and actions.
        if episode.action.shape[-1] == 23:
            cmd = np.asarray(episode.action[i], dtype=np.float64)
            # Back-compat: if action looks like offset (near zero at rest), convert.
            if np.abs(cmd).max() < 0.35 and np.abs(q_abs).max() > 0.35:
                cmd = default_q + cmd
        else:
            cmd = q_abs
        frames.append(
            {
                "idx": i,
                "colors": {"color_0": f"colors/{color_name}"},
                "depths": {},
                "states": _split_23(q_abs),
                "actions": _split_23(cmd),
                "tactiles": None,
                "audios": None,
                "sim_state": None,
            }
        )

    payload = {"info": info, "text": text, "data": frames}
    json_path = ep_dir / "data.json"
    json_path.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")
    return ep_dir


def export_npz_dir_to_unitree_json(
    npz_dir: str | Path,
    out_dir: str | Path,
    *,
    fps: float = 15.0,
    overwrite: bool = False,
) -> list[Path]:
    """Convert ``*_epXXX.npz`` seed files into Unitree episode folders."""
    from simfoundry.data.schema import load_episode

    npz_dir = Path(npz_dir)
    out_dir = Path(out_dir)
    if out_dir.exists() and overwrite:
        import shutil

        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(npz_dir.glob("*.npz"))
    written: list[Path] = []
    for path in paths:
        ep = load_episode(path)
        written.append(export_episode_unitree_json(ep, out_dir, fps=fps))
    return written
