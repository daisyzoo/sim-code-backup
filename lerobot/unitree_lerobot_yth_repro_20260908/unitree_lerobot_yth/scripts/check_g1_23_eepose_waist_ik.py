#!/usr/bin/env python3

"""Check whether G1-23 right_ee.qpos + waist yaw targets are IK-reachable."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Literal

import numpy as np
import tqdm
import tyro

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from unitree_lerobot.eval_robot.robot_control.robot_arm_ik import G1_23_RightArmWaistIK
except ModuleNotFoundError as exc:
    if exc.name in {"casadi", "pinocchio", "logging_mp"}:
        raise SystemExit(
            f"Missing dependency {exc.name!r}. Run this script with the unitree_lerobot conda environment, for example:\n"
            f"  /home/igs/miniconda3/envs/unitree_lerobot/bin/python {Path(__file__).as_posix()} --raw-dir <RAW_DIR>"
        ) from exc
    raise


@dataclasses.dataclass(frozen=True)
class Args:
    raw_dir: Path
    root_key: Literal["states", "actions", "both"] = "actions"
    max_frames: int | None = None
    pos_warn_m: float = 0.03
    quat_warn: float = 0.10
    context_frames: int = 2


def iter_episode_jsons(raw_dir: Path) -> list[Path]:
    return sorted(path for path in raw_dir.glob("*/episode_*/data.json") if path.is_file())


def quat_distance(a_xyzw: np.ndarray, b_xyzw: np.ndarray) -> float:
    a = a_xyzw / max(np.linalg.norm(a_xyzw), 1e-8)
    b = b_xyzw / max(np.linalg.norm(b_xyzw), 1e-8)
    return float(1.0 - abs(np.dot(a, b)))


def get_targets(frame: dict, root_key: str) -> tuple[np.ndarray, float, np.ndarray | None]:
    root = frame[root_key]
    right_ee_pose = np.asarray(root["right_ee"]["qpos"], dtype=np.float32)
    waist_yaw = float(root["body"]["qpos"][0])
    right_arm = root.get("right_arm", {}).get("qpos")
    current_right_arm_q = None if right_arm is None else np.asarray(right_arm, dtype=np.float32)
    return right_ee_pose, waist_yaw, current_right_arm_q


def format_context(payload: dict, frame_index: int, root_key: str, radius: int) -> list[str]:
    frames = payload.get("data", [])
    start = max(0, frame_index - radius)
    end = min(len(frames), frame_index + radius + 1)
    rows: list[str] = []
    prev_pose = None
    prev_waist = None
    prev_arm = None
    for idx in range(start, end):
        try:
            pose, waist, arm = get_targets(frames[idx], root_key)
        except Exception as exc:
            rows.append(f"context frame={idx} root_key={root_key} error={exc}")
            continue
        pos_delta = None if prev_pose is None else float(np.linalg.norm(pose[:3] - prev_pose[:3]))
        quat_delta = None if prev_pose is None else quat_distance(pose[3:7], prev_pose[3:7])
        waist_delta = None if prev_waist is None else float(waist - prev_waist)
        arm_delta_max = None
        if prev_arm is not None and arm is not None:
            arm_delta_max = float(np.max(np.abs(arm - prev_arm)))
        rows.append(
            f"context frame={idx} root_key={root_key} waist={waist:.6f} "
            f"d_waist={None if waist_delta is None else round(waist_delta, 6)} "
            f"pos={pose[:3].tolist()} d_pos_m={None if pos_delta is None else round(pos_delta, 6)} "
            f"quat={pose[3:7].tolist()} d_quat={None if quat_delta is None else round(quat_delta, 6)} "
            f"raw_right_arm_q={None if arm is None else arm.tolist()} "
            f"d_arm_max={None if arm_delta_max is None else round(arm_delta_max, 6)}"
        )
        prev_pose = pose
        prev_waist = waist
        prev_arm = arm
    return rows


def main() -> None:
    args = tyro.cli(Args)
    if not args.raw_dir.is_dir():
        raise FileNotFoundError(f"raw_dir does not exist: {args.raw_dir}")

    episode_jsons = iter_episode_jsons(args.raw_dir)
    if not episode_jsons:
        raise FileNotFoundError(f"No */episode_*/data.json files found in: {args.raw_dir}")

    root_keys = ["states", "actions"] if args.root_key == "both" else [args.root_key]
    ik = G1_23_RightArmWaistIK()

    count = 0
    failures = 0
    pos_errors: list[float] = []
    quat_errors: list[float] = []
    warned = 0
    issue_records: list[str] = []

    for json_path in tqdm.tqdm(episode_jsons, desc="Checking right ee + waist IK"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        ik_reset_for_episode = False
        for frame_index, frame in enumerate(payload.get("data", [])):
            for root_key in root_keys:
                if args.max_frames is not None and count >= args.max_frames:
                    break
                try:
                    right_ee_pose, waist_yaw, current_right_arm_q = get_targets(frame, root_key)
                    if not ik_reset_for_episode:
                        ik.reset(current_right_arm_q, waist_yaw)
                        ik_reset_for_episode = True
                    right_arm_q, solved_waist_yaw = ik.solve_ik(right_ee_pose, waist_yaw, current_right_arm_q)
                    if not getattr(ik, "last_success", True):
                        failures += 1
                        issue_records.append(
                            "FAIL "
                            f"path={json_path} frame={frame_index} root_key={root_key} "
                            f"waist={waist_yaw:.6f} target_pos={right_ee_pose[:3].tolist()} "
                            f"target_quat={right_ee_pose[3:7].tolist()}"
                        )
                        issue_records.extend(
                            f"  {row}" for row in format_context(payload, frame_index, root_key, args.context_frames)
                        )
                    solved_pose = ik.forward_right_ee_pose(right_arm_q, solved_waist_yaw)
                    pos_error = float(np.linalg.norm(solved_pose[:3] - right_ee_pose[:3]))
                    q_error = quat_distance(solved_pose[3:7], right_ee_pose[3:7])
                    pos_errors.append(pos_error)
                    quat_errors.append(q_error)
                    if pos_error > args.pos_warn_m or q_error > args.quat_warn:
                        warned += 1
                        issue_records.append(
                            "WARN "
                            f"path={json_path} frame={frame_index} root_key={root_key} "
                            f"pos_err_m={pos_error:.6f} quat_err={q_error:.6f} "
                            f"target_waist={waist_yaw:.6f} solved_waist={solved_waist_yaw:.6f} "
                            f"target_pos={right_ee_pose[:3].tolist()} solved_pos={solved_pose[:3].tolist()} "
                            f"target_quat={right_ee_pose[3:7].tolist()} solved_quat={solved_pose[3:7].tolist()} "
                            f"seed_right_arm_q={None if current_right_arm_q is None else current_right_arm_q.tolist()} "
                            f"solved_right_arm_q={right_arm_q.tolist()}"
                        )
                        issue_records.extend(
                            f"  {row}" for row in format_context(payload, frame_index, root_key, args.context_frames)
                        )
                except Exception as exc:
                    failures += 1
                    issue_records.append(f"FAIL path={json_path} frame={frame_index} root_key={root_key} error={exc}")
                    issue_records.extend(
                        f"  {row}" for row in format_context(payload, frame_index, root_key, args.context_frames)
                    )
                count += 1
            if args.max_frames is not None and count >= args.max_frames:
                break
        if args.max_frames is not None and count >= args.max_frames:
            break

    pos = np.asarray(pos_errors, dtype=np.float32)
    quat = np.asarray(quat_errors, dtype=np.float32)
    print("G1-23 right ee + waist IK check:")
    print(f"  raw_dir:      {args.raw_dir}")
    print(f"  checked:      {count}")
    print(f"  failures:     {failures}")
    print(f"  warned:       {warned}")
    if pos.size:
        print(f"  pos_err_m:    mean={pos.mean():.6f} p95={np.quantile(pos, 0.95):.6f} max={pos.max():.6f}")
        print(f"  quat_err:     mean={quat.mean():.6f} p95={np.quantile(quat, 0.95):.6f} max={quat.max():.6f}")
    if issue_records:
        print("  issues:")
        for record in issue_records:
            print(f"    {record}")


if __name__ == "__main__":
    main()
