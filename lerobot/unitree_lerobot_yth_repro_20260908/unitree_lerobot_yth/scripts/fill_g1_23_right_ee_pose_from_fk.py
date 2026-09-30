#!/usr/bin/env python3

"""Fill missing G1-23 right_ee.qpos values in Unitree JSON episodes.

The pose definition follows xr_teleoperate's G1_23_ArmIK convention:
``R_ee`` is an operational frame attached to ``right_wrist_roll_joint`` with a
local translation of ``[0.20, 0, 0]``. The IK model locks waist yaw, so FK for
this offline fill intentionally leaves waist yaw at zero to match existing
``right_ee.qpos`` data.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pinocchio as pin
import tqdm
import tyro


DEFAULT_URDF_PATH = Path(
    "/home/igs/Desktop/project/vla/unitree_lerobot/unitree_lerobot/eval_robot/assets/g1/g1_body23.urdf"
)
RIGHT_ARM_Q_SLICE = slice(18, 23)


@dataclasses.dataclass(frozen=True)
class Args:
    raw_dir: Path
    urdf_path: Path = DEFAULT_URDF_PATH
    overwrite_existing: bool = False
    use_waist_yaw: bool = False
    dry_run: bool = False


class RightEeFk:
    def __init__(self, urdf_path: Path) -> None:
        self.model = pin.buildModelFromUrdf(str(urdf_path))
        self.model.addFrame(
            pin.Frame(
                "R_ee",
                self.model.getJointId("right_wrist_roll_joint"),
                pin.SE3(np.eye(3), np.array([0.20, 0.0, 0.0])),
                pin.FrameType.OP_FRAME,
            )
        )
        self.data = self.model.createData()
        self.frame_id = self.model.getFrameId("R_ee")
        self.waist_q_index = int(self.model.joints[self.model.getJointId("waist_yaw_joint")].idx_q)

    def compute(self, right_arm_qpos: list[float], waist_yaw: float = 0.0) -> list[float]:
        if len(right_arm_qpos) != 5:
            raise ValueError(f"Expected right_arm.qpos length 5, got {len(right_arm_qpos)}")

        q = np.zeros(self.model.nq)
        q[self.waist_q_index] = float(waist_yaw)
        q[RIGHT_ARM_Q_SLICE] = np.asarray(right_arm_qpos, dtype=np.float64)

        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)

        transform = self.data.oMf[self.frame_id]
        quat_xyzw = pin.Quaternion(transform.rotation).coeffs()
        return np.concatenate([transform.translation, quat_xyzw]).astype(float).tolist()


def is_missing_pose(value: object) -> bool:
    return value is None or (isinstance(value, list) and len(value) == 0)


def iter_episode_jsons(raw_dir: Path) -> list[Path]:
    return sorted(path for path in raw_dir.glob("*/episode_*/data.json") if path.is_file())


def ensure_right_ee_schema(payload: dict) -> None:
    joint_names = payload.setdefault("info", {}).setdefault("joint_names", {})
    joint_names.setdefault("right_ee", ["x", "y", "z", "qx", "qy", "qz", "qw"])
    tactile_names = payload.setdefault("info", {}).setdefault("tactile_names", {})
    tactile_names.setdefault("right_ee", [])


def fill_payload(payload: dict, fk: RightEeFk, overwrite_existing: bool, use_waist_yaw: bool) -> tuple[int, int]:
    filled = 0
    existing = 0
    ensure_right_ee_schema(payload)

    for frame in payload.get("data", []):
        for root_key in ("states", "actions"):
            root = frame.get(root_key)
            if not isinstance(root, dict):
                continue

            right_ee = root.setdefault("right_ee", {})
            current_pose = right_ee.get("qpos")
            if not overwrite_existing and not is_missing_pose(current_pose):
                existing += 1
                continue

            right_arm = root.get("right_arm", {})
            right_arm_qpos = right_arm.get("qpos")
            if right_arm_qpos is None:
                raise KeyError(f"Missing {root_key}.right_arm.qpos")

            waist_yaw = 0.0
            if use_waist_yaw:
                body_qpos = root.get("body", {}).get("qpos")
                if body_qpos is None or len(body_qpos) < 1:
                    raise KeyError(f"Missing {root_key}.body.qpos[0]")
                waist_yaw = float(body_qpos[0])

            right_ee["qpos"] = fk.compute(right_arm_qpos, waist_yaw)
            right_ee.setdefault("qvel", [])
            right_ee.setdefault("torque", [])
            filled += 1

    return filled, existing


def main() -> None:
    args = tyro.cli(Args)
    if not args.raw_dir.is_dir():
        raise FileNotFoundError(f"raw_dir does not exist: {args.raw_dir}")
    if not args.urdf_path.is_file():
        raise FileNotFoundError(f"urdf_path does not exist: {args.urdf_path}")

    fk = RightEeFk(args.urdf_path)
    episode_jsons = iter_episode_jsons(args.raw_dir)
    if not episode_jsons:
        raise FileNotFoundError(f"No */episode_*/data.json files found in: {args.raw_dir}")

    total_filled = 0
    total_existing = 0
    touched_episodes = 0

    for json_path in tqdm.tqdm(episode_jsons, desc="Filling right_ee.qpos"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        filled, existing = fill_payload(payload, fk, args.overwrite_existing, args.use_waist_yaw)
        total_filled += filled
        total_existing += existing
        if filled:
            touched_episodes += 1
            if not args.dry_run:
                json_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=4),
                    encoding="utf-8",
                )

    print("Filled G1-23 right_ee.qpos from FK:")
    print(f"  raw_dir:          {args.raw_dir}")
    print(f"  urdf_path:        {args.urdf_path}")
    print(f"  episodes:         {len(episode_jsons)}")
    print(f"  touched_episodes: {touched_episodes}")
    print(f"  filled_values:    {total_filled}")
    print(f"  existing_values:  {total_existing}")
    print(f"  use_waist_yaw:    {args.use_waist_yaw}")
    print(f"  dry_run:          {args.dry_run}")


if __name__ == "__main__":
    main()
