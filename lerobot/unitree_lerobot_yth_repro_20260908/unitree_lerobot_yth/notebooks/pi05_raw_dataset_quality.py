"""Quality checks for Unitree raw JSON datasets intended for LeRobot/pi0.5.

This module is deliberately independent of the project converter so that malformed
raw data can be diagnosed before conversion.  It never modifies the source dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


CHANNEL_SPECS = (
    ("state", "states", "left_arm", 5),
    ("state", "states", "right_arm", 5),
    ("state", "states", "body", 3),
    ("action", "actions", "left_arm", 5),
    ("action", "actions", "right_arm", 5),
    ("action", "actions", "body", 3),
)

CONTROL_NAMES_11D = [
    "left_shoulder_pitch",
    "left_shoulder_roll",
    "left_shoulder_yaw",
    "left_elbow",
    "left_wrist_roll",
    "right_shoulder_pitch",
    "right_shoulder_roll",
    "right_shoulder_yaw",
    "right_elbow",
    "right_wrist_roll",
    "waist_yaw",
]

# G1-23 limits from unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf.
# These detect impossible values; deployment may intentionally use tighter soft limits.
G1_23_LIMITS = {
    "left_shoulder_pitch": (-3.0892, 2.6704),
    "left_shoulder_roll": (-1.5882, 2.2515),
    "left_shoulder_yaw": (-2.618, 2.618),
    "left_elbow": (-1.0472, 2.0944),
    "left_wrist_roll": (-1.972222054, 1.972222054),
    "right_shoulder_pitch": (-3.0892, 2.6704),
    "right_shoulder_roll": (-2.2515, 1.5882),
    "right_shoulder_yaw": (-2.618, 2.618),
    "right_elbow": (-1.0472, 2.0944),
    "right_wrist_roll": (-1.972222054, 1.972222054),
    "waist_yaw": (-2.618, 2.618),
}


def _issue(issues: list[dict[str, Any]], level: str, episode: str, kind: str, detail: str) -> None:
    issues.append({"level": level, "episode": episode, "kind": kind, "detail": detail})


def _finite_vector(value: Any, expected: int) -> tuple[np.ndarray | None, str | None]:
    if not isinstance(value, list):
        return None, f"expected list, got {type(value).__name__}"
    if len(value) != expected:
        return None, f"expected length {expected}, got {len(value)}"
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        return None, f"not numeric: {exc}"
    if not np.all(np.isfinite(array)):
        return None, "contains NaN or Inf"
    return array, None


def _safe_quantile(x: np.ndarray, q: float) -> float:
    return float(np.quantile(x, q)) if x.size else math.nan


def _hash_file(path: Path) -> str:
    digest = hashlib.blake2b(digest_size=16)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_dataset(
    dataset_root: str | Path,
    *,
    image_sample_stride: int = 20,
    verify_all_images: bool = False,
) -> dict[str, Any]:
    """Scan one flat directory containing episode_XXXX directories."""
    root = Path(dataset_root).expanduser().resolve()
    episode_dirs = sorted(path for path in root.glob("episode_*") if path.is_dir())
    if not episode_dirs:
        raise FileNotFoundError(f"No episode_* directories found under {root}")

    issues: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    all_arrays: dict[str, list[np.ndarray]] = {
        f"{role}.{part}": [] for role, _, part, _ in CHANNEL_SPECS
    }
    episode_arrays: dict[str, dict[str, np.ndarray]] = {}
    goal_counter: Counter[str] = Counter()
    fps_counter: Counter[float] = Counter()
    resolution_counter: Counter[str] = Counter()
    referenced_images: set[Path] = set()
    image_hashes: Counter[str] = Counter()
    trajectory_hash_groups: dict[str, list[str]] = {}

    for episode_dir in episode_dirs:
        episode = episode_dir.name
        json_path = episode_dir / "data.json"
        if not json_path.is_file():
            _issue(issues, "ERROR", episode, "missing_json", str(json_path))
            continue
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:  # malformed input: retain exact parser message
            _issue(issues, "ERROR", episode, "invalid_json", repr(exc))
            continue

        info = payload.get("info", {})
        image_info = info.get("image", {})
        fps = image_info.get("fps")
        width = image_info.get("width")
        height = image_info.get("height")
        if isinstance(fps, (int, float)) and np.isfinite(fps) and fps > 0:
            fps = float(fps)
            fps_counter[fps] += 1
        else:
            _issue(issues, "ERROR", episode, "invalid_fps", repr(fps))
            fps = math.nan
        resolution_counter[f"{width}x{height}"] += 1
        goal = str(payload.get("text", {}).get("goal", "")).strip()
        goal_counter[goal] += 1
        frames = payload.get("data")
        if not isinstance(frames, list) or not frames:
            _issue(issues, "ERROR", episode, "empty_or_missing_data", repr(type(frames).__name__))
            continue

        frame_ids: list[int] = []
        ep_values: dict[str, list[np.ndarray]] = {
            f"{role}.{part}": [] for role, _, part, _ in CHANNEL_SPECS
        }
        missing_image_count = 0
        bad_image_count = 0
        sampled_image_count = 0
        previous_thumbnail: np.ndarray | None = None
        near_duplicate_pairs = 0

        for position, frame in enumerate(frames):
            idx = frame.get("idx")
            if isinstance(idx, int):
                frame_ids.append(idx)
            else:
                _issue(issues, "ERROR", episode, "invalid_frame_idx", f"position={position}, idx={idx!r}")

            for role, root_key, part, expected_dim in CHANNEL_SPECS:
                value = frame.get(root_key, {}).get(part, {}).get("qpos")
                array, error = _finite_vector(value, expected_dim)
                if error:
                    _issue(
                        issues,
                        "ERROR",
                        episode,
                        "invalid_qpos",
                        f"frame={position}, {root_key}.{part}.qpos: {error}",
                    )
                else:
                    ep_values[f"{role}.{part}"].append(array)

            colors = frame.get("colors")
            relative = colors.get("color_0") if isinstance(colors, dict) else None
            if not relative:
                missing_image_count += 1
                _issue(issues, "ERROR", episode, "missing_image_reference", f"frame={position}")
                continue
            image_path = (episode_dir / relative).resolve()
            referenced_images.add(image_path)
            if not image_path.is_file():
                missing_image_count += 1
                _issue(issues, "ERROR", episode, "missing_image_file", f"frame={position}, path={relative}")
                continue

            should_decode = verify_all_images or position % max(image_sample_stride, 1) == 0 or position == len(frames) - 1
            if not should_decode:
                continue
            sampled_image_count += 1
            try:
                with Image.open(image_path) as image:
                    image.load()
                    actual_width, actual_height = image.size
                    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
                if actual_width != width or actual_height != height:
                    _issue(
                        issues,
                        "ERROR",
                        episode,
                        "image_shape_mismatch",
                        f"frame={position}, metadata={width}x{height}, actual={actual_width}x{actual_height}",
                    )
                gray = rgb.mean(axis=2)
                brightness = float(gray.mean())
                contrast = float(gray.std())
                dx = np.diff(gray, axis=1)
                dy = np.diff(gray, axis=0)
                sharpness = float((dx.var() + dy.var()) / 2.0)
                thumbnail = np.asarray(
                    Image.fromarray(rgb.astype(np.uint8)).convert("L").resize((32, 24)), dtype=np.float32
                )
                frame_delta = math.nan
                if previous_thumbnail is not None:
                    frame_delta = float(np.mean(np.abs(thumbnail - previous_thumbnail)))
                    if frame_delta < 0.1:
                        near_duplicate_pairs += 1
                previous_thumbnail = thumbnail
                file_hash = _hash_file(image_path)
                image_hashes[file_hash] += 1
                image_rows.append(
                    {
                        "episode": episode,
                        "frame": position,
                        "brightness": brightness,
                        "contrast": contrast,
                        "sharpness": sharpness,
                        "sampled_frame_delta": frame_delta,
                    }
                )
            except Exception as exc:
                bad_image_count += 1
                _issue(issues, "ERROR", episode, "unreadable_image", f"frame={position}, {exc!r}")

        expected_ids = list(range(len(frames)))
        if frame_ids != expected_ids:
            _issue(
                issues,
                "ERROR",
                episode,
                "non_contiguous_frame_idx",
                f"first={frame_ids[:5]}, last={frame_ids[-5:]}, expected 0..{len(frames)-1}",
            )

        valid_episode = all(len(values) == len(frames) for values in ep_values.values())
        if valid_episode:
            arrays = {name: np.stack(values) for name, values in ep_values.items()}
            episode_arrays[episode] = arrays
            for name, array in arrays.items():
                all_arrays[name].append(array)
            digest = hashlib.sha256()
            for name in sorted(arrays):
                digest.update(np.asarray(arrays[name], dtype=np.float64).tobytes())
            trajectory_hash_groups.setdefault(digest.hexdigest(), []).append(episode)
        duration_s = len(frames) / fps if np.isfinite(fps) else math.nan
        episode_rows.append(
            {
                "episode": episode,
                "frames": len(frames),
                "fps": fps,
                "duration_s": duration_s,
                "goal": goal,
                "valid_numeric": valid_episode,
                "missing_images": missing_image_count,
                "bad_sampled_images": bad_image_count,
                "sampled_images": sampled_image_count,
                "near_duplicate_sample_pairs": near_duplicate_pairs,
            }
        )

    # Filesystem-level image checks. A non-JPEG in colors is intentionally included.
    actual_images = {
        path.resolve()
        for episode_dir in episode_dirs
        for path in (episode_dir / "colors").glob("*")
        if path.is_file()
    }
    orphan_images = sorted(actual_images - referenced_images)
    for path in orphan_images[:1000]:
        _issue(issues, "WARN", path.parent.parent.name, "unreferenced_image", str(path.relative_to(root)))
    if len(orphan_images) > 1000:
        _issue(issues, "WARN", "DATASET", "unreferenced_image_truncated", f"total={len(orphan_images)}")

    control_arrays: dict[str, np.ndarray] = {}
    for role in ("state", "action"):
        left = np.concatenate(all_arrays[f"{role}.left_arm"], axis=0)
        right = np.concatenate(all_arrays[f"{role}.right_arm"], axis=0)
        body = np.concatenate(all_arrays[f"{role}.body"], axis=0)[:, :1]
        control_arrays[role] = np.concatenate([left, right, body], axis=1)

    joint_rows: list[dict[str, Any]] = []
    for role, values in control_arrays.items():
        for index, name in enumerate(CONTROL_NAMES_11D):
            x = values[:, index]
            lower, upper = G1_23_LIMITS[name]
            joint_rows.append(
                {
                    "role": role,
                    "joint": name,
                    "count": x.size,
                    "mean": float(x.mean()),
                    "std": float(x.std()),
                    "min": float(x.min()),
                    "p01": _safe_quantile(x, 0.01),
                    "p05": _safe_quantile(x, 0.05),
                    "median": _safe_quantile(x, 0.50),
                    "p95": _safe_quantile(x, 0.95),
                    "p99": _safe_quantile(x, 0.99),
                    "max": float(x.max()),
                    "range": float(np.ptp(x)),
                    "urdf_lower": lower,
                    "urdf_upper": upper,
                    "below_urdf_limit": int(np.sum(x < lower)),
                    "above_urdf_limit": int(np.sum(x > upper)),
                }
            )

    temporal_rows: list[dict[str, Any]] = []
    episode_joint_rows: list[dict[str, Any]] = []
    relationship_chunks: dict[str, list[np.ndarray]] = {"same": [], "next": []}
    for episode, arrays in episode_arrays.items():
        fps = float(next(row["fps"] for row in episode_rows if row["episode"] == episode))
        state = np.concatenate([arrays["state.left_arm"], arrays["state.right_arm"], arrays["state.body"][:, :1]], axis=1)
        action = np.concatenate([arrays["action.left_arm"], arrays["action.right_arm"], arrays["action.body"][:, :1]], axis=1)
        relationship_chunks["same"].append(action - state)
        if len(state) > 1:
            relationship_chunks["next"].append(action[:-1] - state[1:])
        for role, values in (("state", state), ("action", action)):
            delta = np.diff(values, axis=0)
            speed = np.abs(delta) * fps
            for index, name in enumerate(CONTROL_NAMES_11D):
                d = np.abs(delta[:, index])
                s = speed[:, index]
                temporal_rows.append(
                    {
                        "episode": episode,
                        "role": role,
                        "joint": name,
                        "median_abs_step": _safe_quantile(d, 0.50),
                        "p95_abs_step": _safe_quantile(d, 0.95),
                        "p99_abs_step": _safe_quantile(d, 0.99),
                        "max_abs_step": float(d.max()) if d.size else math.nan,
                        "p99_abs_speed_rad_s": _safe_quantile(s, 0.99),
                        "max_abs_speed_rad_s": float(s.max()) if s.size else math.nan,
                        "zero_step_fraction": float(np.mean(d < 1e-6)) if d.size else math.nan,
                    }
                )
                episode_joint_rows.append(
                    {
                        "episode": episode,
                        "role": role,
                        "joint": name,
                        "start": float(values[0, index]),
                        "end": float(values[-1, index]),
                        "min": float(values[:, index].min()),
                        "max": float(values[:, index].max()),
                        "range": float(np.ptp(values[:, index])),
                        "std": float(values[:, index].std()),
                    }
                )

    relationship_rows: list[dict[str, Any]] = []
    disagreement_rows: list[dict[str, Any]] = []
    same = np.concatenate(relationship_chunks["same"], axis=0)
    nxt = np.concatenate(relationship_chunks["next"], axis=0)
    for index, name in enumerate(CONTROL_NAMES_11D):
        for alignment, error in (("action[t]-state[t]", same[:, index]), ("action[t]-state[t+1]", nxt[:, index])):
            relationship_rows.append(
                {
                    "joint": name,
                    "alignment": alignment,
                    "mae": float(np.mean(np.abs(error))),
                    "p95_abs_error": _safe_quantile(np.abs(error), 0.95),
                    "max_abs_error": float(np.max(np.abs(error))),
                    "bias": float(np.mean(error)),
                }
            )
        absolute_same_error = np.abs(same[:, index])
        for threshold in (0.05, 0.10, 0.20):
            count = int(np.sum(absolute_same_error > threshold))
            disagreement_rows.append(
                {
                    "joint": name,
                    "threshold_rad": threshold,
                    "frames_over_threshold": count,
                    "fraction": count / absolute_same_error.size,
                }
            )

    duplicate_rows: list[dict[str, Any]] = []
    for digest, episodes in sorted(trajectory_hash_groups.items()):
        if len(episodes) > 1:
            duplicate_rows.append(
                {
                    "sha256_numeric_trajectory": digest,
                    "copies": len(episodes),
                    "episodes": ",".join(episodes),
                }
            )

    episode_df = pd.DataFrame(episode_rows)
    joint_df = pd.DataFrame(joint_rows)
    temporal_df = pd.DataFrame(temporal_rows)
    episode_joint_df = pd.DataFrame(episode_joint_rows)
    relationship_df = pd.DataFrame(relationship_rows)
    disagreement_df = pd.DataFrame(disagreement_rows)
    duplicate_df = pd.DataFrame(
        duplicate_rows,
        columns=["sha256_numeric_trajectory", "copies", "episodes"],
    )
    image_df = pd.DataFrame(image_rows)
    issue_df = pd.DataFrame(issues, columns=["level", "episode", "kind", "detail"])

    temporal_summary = (
        temporal_df.groupby(["role", "joint"], as_index=False)
        .agg(
            median_episode_p99_step=("p99_abs_step", "median"),
            worst_step=("max_abs_step", "max"),
            median_episode_p99_speed_rad_s=("p99_abs_speed_rad_s", "median"),
            worst_speed_rad_s=("max_abs_speed_rad_s", "max"),
            median_zero_step_fraction=("zero_step_fraction", "median"),
        )
    )

    duplicate_sampled_files = int(sum(count - 1 for count in image_hashes.values() if count > 1))
    summary = {
        "dataset_root": str(root),
        "episodes": len(episode_dirs),
        "valid_numeric_episodes": int(episode_df["valid_numeric"].sum()),
        "total_frames": int(episode_df["frames"].sum()),
        "total_duration_minutes": float(episode_df["duration_s"].sum() / 60.0),
        "episode_frames": episode_df["frames"].describe().to_dict(),
        "fps_counts": {str(key): value for key, value in sorted(fps_counter.items())},
        "resolution_counts": dict(resolution_counter),
        "goal_counts": dict(goal_counter),
        "error_count": int((issue_df["level"] == "ERROR").sum()) if not issue_df.empty else 0,
        "warning_count": int((issue_df["level"] == "WARN").sum()) if not issue_df.empty else 0,
        "missing_referenced_images": int(episode_df["missing_images"].sum()),
        "bad_sampled_images": int(episode_df["bad_sampled_images"].sum()),
        "sampled_images": int(episode_df["sampled_images"].sum()),
        "duplicate_sampled_image_files": duplicate_sampled_files,
        "unreferenced_image_files": len(orphan_images),
        "exact_duplicate_trajectory_groups": len(duplicate_rows),
        "extra_exact_duplicate_trajectories": int(sum(row["copies"] - 1 for row in duplicate_rows)),
        "episode_name_first": episode_dirs[0].name,
        "episode_name_last": episode_dirs[-1].name,
    }

    return {
        "summary": summary,
        "episodes": episode_df,
        "joints": joint_df,
        "temporal_per_episode": temporal_df,
        "temporal_summary": temporal_summary,
        "episode_joints": episode_joint_df,
        "state_action_relationship": relationship_df,
        "state_action_disagreement": disagreement_df,
        "duplicate_trajectories": duplicate_df,
        "images": image_df,
        "issues": issue_df,
        "control_arrays": control_arrays,
        "episode_arrays": episode_arrays,
    }


def save_report(result: dict[str, Any], output_dir: str | Path) -> Path:
    """Write machine-readable tables and compact diagnostic plots."""
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(result["summary"], ensure_ascii=False, indent=2, default=float) + "\n",
        encoding="utf-8",
    )
    for key in (
        "episodes",
        "joints",
        "temporal_per_episode",
        "temporal_summary",
        "episode_joints",
        "state_action_relationship",
        "state_action_disagreement",
        "duplicate_trajectories",
        "images",
        "issues",
    ):
        result[key].to_csv(output / f"{key}.csv", index=False)

    episode_df = result["episodes"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(episode_df["frames"], bins=25, edgecolor="black")
    axes[0].set(title="Episode length", xlabel="frames", ylabel="episodes")
    axes[1].plot(episode_df["episode"], episode_df["frames"], linewidth=1)
    axes[1].set(title="Length by episode", xlabel="episode", ylabel="frames")
    axes[1].tick_params(axis="x", labelrotation=90, labelsize=5)
    fig.tight_layout()
    fig.savefig(output / "episode_lengths.png", dpi=160)
    plt.close(fig)

    names = CONTROL_NAMES_11D
    fig, axes = plt.subplots(4, 3, figsize=(16, 14), sharex=False)
    axes = axes.ravel()
    for index, name in enumerate(names):
        axis = axes[index]
        axis.hist(result["control_arrays"]["state"][:, index], bins=60, alpha=0.65, label="state")
        axis.hist(result["control_arrays"]["action"][:, index], bins=60, alpha=0.45, label="action")
        axis.set_title(name)
        axis.set_xlabel("rad")
    axes[0].legend()
    axes[-1].axis("off")
    fig.suptitle("State/action distributions (11D; body roll/pitch excluded)")
    fig.tight_layout()
    fig.savefig(output / "joint_distributions.png", dpi=160)
    plt.close(fig)

    temporal = result["temporal_summary"]
    action_temporal = temporal[temporal["role"] == "action"].set_index("joint").loc[names]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    axes[0].bar(names, action_temporal["median_episode_p99_speed_rad_s"])
    axes[0].set(title="Typical episode action speed p99", ylabel="rad/s")
    axes[0].tick_params(axis="x", rotation=70)
    axes[1].bar(names, action_temporal["worst_speed_rad_s"])
    axes[1].set(title="Worst one-frame action speed", ylabel="rad/s")
    axes[1].tick_params(axis="x", rotation=70)
    fig.tight_layout()
    fig.savefig(output / "action_speed.png", dpi=160)
    plt.close(fig)

    episode_joints = result["episode_joints"]
    action_ranges = episode_joints[episode_joints["role"] == "action"].pivot(
        index="episode", columns="joint", values="range"
    )[names]
    fig, axis = plt.subplots(figsize=(15, 6))
    image = axis.imshow(action_ranges.to_numpy().T, aspect="auto", interpolation="nearest", cmap="viridis")
    axis.set_yticks(range(len(names)), labels=names)
    axis.set_xlabel("episode index (sorted)")
    axis.set_title("Per-episode action range (rad)")
    fig.colorbar(image, ax=axis, label="range (rad)")
    fig.tight_layout()
    fig.savefig(output / "episode_action_ranges.png", dpi=160)
    plt.close(fig)

    if not result["images"].empty:
        image_df = result["images"]
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        for axis, column in zip(axes, ("brightness", "contrast", "sharpness"), strict=True):
            axis.hist(image_df[column].dropna(), bins=50, edgecolor="black")
            axis.set_title(column)
        fig.tight_layout()
        fig.savefig(output / "sampled_image_quality.png", dpi=160)
        plt.close(fig)
    return output


def print_console_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=float))
    print("\nJoint statistics:")
    print(result["joints"].to_string(index=False))
    print("\nTemporal summary:")
    print(result["temporal_summary"].to_string(index=False))
    print("\nState/action relationship:")
    print(result["state_action_relationship"].to_string(index=False))
    print("\nSame-frame action/state disagreement:")
    print(result["state_action_disagreement"].to_string(index=False))
    print("\nExact duplicate numeric trajectories:")
    print(result["duplicate_trajectories"].to_string(index=False) if not result["duplicate_trajectories"].empty else "none")
    issues = result["issues"]
    print("\nIssue counts:")
    print(issues.groupby(["level", "kind"]).size().to_string() if not issues.empty else "none")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("dataset_quality_report"))
    parser.add_argument("--image-sample-stride", type=int, default=20)
    parser.add_argument("--verify-all-images", action="store_true")
    args = parser.parse_args()
    result = scan_dataset(
        args.dataset_root,
        image_sample_stride=args.image_sample_stride,
        verify_all_images=args.verify_all_images,
    )
    output = save_report(result, args.output_dir)
    print_console_summary(result)
    print(f"\nReport written to: {output}")


if __name__ == "__main__":
    main()
