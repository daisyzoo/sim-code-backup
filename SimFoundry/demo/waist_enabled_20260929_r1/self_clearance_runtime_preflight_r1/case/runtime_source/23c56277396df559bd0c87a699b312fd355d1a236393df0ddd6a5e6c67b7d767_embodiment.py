"""Embodiment constants. Lives outside the scene package on purpose."""

from __future__ import annotations

from dataclasses import dataclass

EMBODIMENT_ID = "g1_edu_23_bimanual"
EMBODIMENT_ID_U1 = "g1_edu_23_u1_rubber"

KNOWN_EMBODIMENT_IDS = frozenset({EMBODIMENT_ID, EMBODIMENT_ID_U1})

# Unitree teleop / pick_cup_soring_0824: info.image.fps == 15 for all 186 episodes.
REAL_TELEOP_FPS = 15.0
# Mean episode length on the real push/sort rig (139–343 frames @ 15 Hz).
SORTING_TELEOP_STEPS = 195
# Active DoF on real teleop: left_arm(5) + right_arm(5) + waist_yaw(1).
SORTING_TELEOP_DOFS = 11

# Unitree G1 EDU 23 DoF (no dexterous hands). Rubber-hand joints in g1.usd are omitted.
G1_23DOF_JOINT_NAMES: tuple[str, ...] = (
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "torso_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_pitch_joint",
    "left_elbow_roll_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_pitch_joint",
    "right_elbow_roll_joint",
)

RIGHT_ARM_JOINT_NAMES: tuple[str, ...] = G1_23DOF_JOINT_NAMES[18:]


@dataclass(frozen=True)
class PinholeIntrinsics:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float

    def as_matrix_row_major(self) -> list[float]:
        return [self.fx, 0.0, self.cx, 0.0, self.fy, self.cy, 0.0, 0.0, 1.0]


# Intel RealSense D435i SN 233622077487, color 640x480.
D435I_INTRINSICS = PinholeIntrinsics(
    width=640,
    height=480,
    fx=605.5006,
    fy=605.4136,
    cx=326.1470,
    cy=249.5715,
)

# Calibrated on sorting station — see simfoundry.calibration.sorting_station.
from simfoundry.calibration.sorting_station import (
    SORTING_D435I_POS,
    SORTING_D435I_ROT_XYZW,
)

D435I_PARENT_LINK = "torso_link"
D435I_OFFSET_POS = SORTING_D435I_POS
D435I_OFFSET_ROT_XYZW = SORTING_D435I_ROT_XYZW
