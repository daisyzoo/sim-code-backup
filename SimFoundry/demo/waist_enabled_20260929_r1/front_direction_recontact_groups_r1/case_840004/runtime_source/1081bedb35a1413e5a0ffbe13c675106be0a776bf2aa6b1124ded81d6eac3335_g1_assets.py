"""Local Unitree G1 assets converted from unitree_ros."""

from __future__ import annotations

from pathlib import Path
import re

import isaaclab.sim as sim_utils
import numpy as np
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg
from isaaclab_assets.robots.unitree import G1_CFG, G1_INSPIRE_FTP_CFG

from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS
from simfoundry.embodiment import G1_23DOF_JOINT_NAMES

_SIMFOUNDRY = Path(__file__).resolve().parents[2]
_LOCAL_INSPIRE_CANDIDATES = (
    _SIMFOUNDRY / "assets" / "robots" / "g1_29dof_inspire_ftp" / "g1_29dof_inspire_ftp.usd",
    _SIMFOUNDRY
    / "assets"
    / "robots"
    / "g1_29dof_inspire_ftp"
    / "g1_29dof_rev_1_0_with_inspire_hand_FTP"
    / "g1_29dof_rev_1_0_with_inspire_hand_FTP.usda",
)
_URDF_SOURCE = (
    _SIMFOUNDRY
    / "third_party"
    / "unitree_ros"
    / "robots"
    / "g1_description"
    / "g1_29dof_rev_1_0_with_inspire_hand_FTP.urdf"
)


def local_inspire_usd() -> Path | None:
    for path in _LOCAL_INSPIRE_CANDIDATES:
        if path.is_file():
            return path
    return None


def inspire_urdf_source() -> Path:
    return _URDF_SOURCE


# Fixed-base stump G1 used by A-period collect/demo (Nucleus g1.usd, 23 DoF action slice).
G1_STUMP_CFG: ArticulationCfg = G1_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

# Official G1 23DoF + U1 rubber look (aligned with picktask-sim geometry).
# Kinematics / collision: official `*_wrist_roll_rubber_hand` STL convexHull
# (`purpose=guide`, not rendered). Visual: plane-cut at x=0.088, densify ring
# (~1 mm), circularize seam, then GeomSubset forearm_silver (white) /
# hand_black. Regen: scripts/regen_g1_hand_partition.py
G1_U1_23DOF_JOINT_NAMES: tuple[str, ...] = (
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
    "waist_yaw_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
)

_LOCAL_U1_CANDIDATES = (
    _SIMFOUNDRY / "assets" / "robots" / "g1_23dof_u1_rubber" / "g1_23dof_rev_1_0_u1_black" / "g1_23dof_rev_1_0_u1_black.usda",
    _SIMFOUNDRY / "assets" / "robots" / "g1_23dof_u1_rubber" / "g1_23dof_rev_1_0" / "g1_23dof_rev_1_0.usda",
)


def local_u1_rubber_usd() -> Path | None:
    for path in _LOCAL_U1_CANDIDATES:
        if path.is_file():
            return path
    return None


# Idle / hover matching demo/real_ref_frames/1_t0.5.jpg at standing pelvis z=0.793:
# both arms forward over the blue table (negative shoulder pitch = reach +X on G1),
# elbows bent so palms sit ~6–12 cm ABOVE TABLE_TOP. Positive pitch retracts behind torso.
# Order: pitch, roll, yaw, elbow, wrist_roll — absolute joint angles in URDF frame.
U1_REAL_REST_LEFT_ARM = (-0.66, 0.22, -0.05, 1.00, 0.20)
U1_REAL_REST_RIGHT_ARM = (-0.66, -0.22, 0.05, 1.00, -0.20)
# Keep waist square to the table (no yaw lean in the initial D435i view).
U1_REAL_REST_WAIST_YAW = 0.0

# Stump leg pose (not logged on the real pick rig; keeps pelvis stable).
U1_STUMP_LEG_JOINT_POS = {
    ".*_hip_pitch_joint": -0.20,
    ".*_knee_joint": 0.42,
    ".*_ankle_pitch_joint": -0.23,
}

# USD / URDF joint names → values for ``ArticulationCfg.init_state.joint_pos``.
U1_REAL_REST_JOINT_POS: dict[str, float] = {
    **U1_STUMP_LEG_JOINT_POS,
    "waist_yaw_joint": U1_REAL_REST_WAIST_YAW,
    "left_shoulder_pitch_joint": U1_REAL_REST_LEFT_ARM[0],
    "left_shoulder_roll_joint": U1_REAL_REST_LEFT_ARM[1],
    "left_shoulder_yaw_joint": U1_REAL_REST_LEFT_ARM[2],
    "left_elbow_joint": U1_REAL_REST_LEFT_ARM[3],
    "left_wrist_roll_joint": U1_REAL_REST_LEFT_ARM[4],
    "right_shoulder_pitch_joint": U1_REAL_REST_RIGHT_ARM[0],
    "right_shoulder_roll_joint": U1_REAL_REST_RIGHT_ARM[1],
    "right_shoulder_yaw_joint": U1_REAL_REST_RIGHT_ARM[2],
    "right_elbow_joint": U1_REAL_REST_RIGHT_ARM[3],
    "right_wrist_roll_joint": U1_REAL_REST_RIGHT_ARM[4],
}

# G1_23DOF action slice aliases (elbow_pitch / wrist on the 23-DoF log order).
_U1_JOINT_NAME_ALIASES: dict[str, str] = {
    "left_elbow_pitch_joint": "left_elbow_joint",
    "right_elbow_pitch_joint": "right_elbow_joint",
    "left_elbow_roll_joint": "left_wrist_roll_joint",
    "right_elbow_roll_joint": "right_wrist_roll_joint",
    "torso_joint": "waist_yaw_joint",
}


def u1_sorting_default_qpos(*, zero_upper_body: bool = False) -> tuple[float, ...]:
    """Default joint vector in ``G1_23DOF_JOINT_NAMES`` order (action zero point)."""
    flat: dict[str, float] = {}
    for pattern, value in U1_REAL_REST_JOINT_POS.items():
        if ".*" in pattern:
            for side in ("left", "right"):
                for joint in ("hip_pitch_joint", "knee_joint", "ankle_pitch_joint"):
                    flat[f"{side}_{joint}"] = value
        else:
            flat[pattern] = value
    for side in ("left", "right"):
        flat.setdefault(f"{side}_hip_roll_joint", 0.0)
        flat.setdefault(f"{side}_hip_yaw_joint", 0.0)
        flat.setdefault(f"{side}_ankle_roll_joint", 0.0)
    q = []
    for name in G1_23DOF_JOINT_NAMES:
        key = _U1_JOINT_NAME_ALIASES.get(name, name)
        q.append(flat.get(key, 0.0))
    if zero_upper_body:
        # Match each leg pattern to its own joint; keep the historical default
        # branch unchanged for frozen experiment replay. Upper body stays zero.
        q = [next((value for pattern, value in U1_STUMP_LEG_JOINT_POS.items()
                   if re.fullmatch(pattern, name)), 0.0)
             for name in G1_U1_23DOF_JOINT_NAMES]
    return tuple(q)


def u1_sorting_default_qpos_np(*, zero_upper_body: bool = False) -> np.ndarray:
    return np.array(u1_sorting_default_qpos(zero_upper_body=zero_upper_body), dtype=np.float32)


# Official g1_23dof_rev_1_0.urdf limits (rad), G1_U1_23DOF_JOINT_NAMES order.
#
# G1 EDU 23-DoF is not the 29-DoF kit:
#   - waist: yaw only (no waist roll / pitch → cannot bow onto the table)
#   - each arm: 5 DoF = shoulder pitch/roll/yaw + elbow + wrist roll
#     (no wrist pitch / yaw → cannot independently flatten the palm)
# Shoulder roll is asymmetric (more abduction than adduction):
#   left  [-1.5882, 2.2515]   right [-2.2515, 1.5882]
# Pushing the box to −Y with the right arm, and the mailer to +Y with the left,
# is the reachable pattern. Crossing the torso toward the opposite bin is not.
# Isaac ``soft_joint_pos_limit_factor=0.92`` saturates before the URDF stop.
# Empirically |shoulder-roll offset| ≳ 0.80 lifts the palm to z≈1.1; keep ≤0.42.
U1_JOINT_LIMIT_LO: tuple[float, ...] = (
    -2.5307, -0.5236, -2.7576, -0.087267, -0.87267, -0.2618,
    -2.5307, -2.9671, -2.7576, -0.087267, -0.87267, -0.2618,
    -2.618,
    -3.0892, -1.5882, -2.618, -1.0472, -1.9722,
    -3.0892, -2.2515, -2.618, -1.0472, -1.9722,
)
U1_JOINT_LIMIT_HI: tuple[float, ...] = (
    2.8798, 2.9671, 2.7576, 2.8798, 0.5236, 0.2618,
    2.8798, 0.5236, 2.7576, 2.8798, 0.5236, 0.2618,
    2.618,
    2.6704, 2.2515, 2.618, 2.0944, 1.9722,
    2.6704, 1.5882, 2.618, 2.0944, 1.9722,
)


def clip_sorting_action_offset(offset: np.ndarray) -> np.ndarray:
    """Clamp U1 sorting targets to URDF limits (reduces table/box penetration from PD overshoot)."""
    default = u1_sorting_default_qpos_np()
    off = np.asarray(offset, dtype=np.float32).reshape(-1)
    if off.shape[0] != 23:
        raise ValueError(f"expected 23-DoF offset, got {off.shape}")
    lo = np.asarray(U1_JOINT_LIMIT_LO, dtype=np.float32)
    hi = np.asarray(U1_JOINT_LIMIT_HI, dtype=np.float32)
    target = np.clip(default + off, lo, hi)
    return (target - default).astype(np.float32)


def g1_u1_rubber_cfg() -> ArticulationCfg:
    """G1 EDU 23 DoF with U1 rubber hands. Falls back to Nucleus g1.usd if USD missing."""
    cfg = G1_CFG.copy()
    cfg.prim_path = "{ENV_REGEX_NS}/Robot"
    local = local_u1_rubber_usd()
    if local is not None:
        cfg.spawn.usd_path = str(local)
    # Converted U1 USD already has PhysicsFixedJoint root_joint on Geometry/pelvis.
    # ArticulationRootAPI is on Geometry (not a rigid body), so Isaac cannot add another.
    cfg.spawn.articulation_props.fix_root_link = False
    cfg.spawn.rigid_props.max_depenetration_velocity = 0.25
    cfg.spawn.articulation_props.solver_position_iteration_count = 16
    cfg.spawn.articulation_props.solver_velocity_iteration_count = 8
    cfg.soft_joint_pos_limit_factor = 0.92
    cfg.init_state = ArticulationCfg.InitialStateCfg(
        # Standing pelvis height (G1_CFG / real sorting stance), not a sunk stump.
        pos=SORTING_ROBOT_POS,
        joint_pos=U1_REAL_REST_JOINT_POS,
        joint_vel={".*": 0.0},
    )
    cfg.actuators = {
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_hip_yaw_joint",
                ".*_hip_roll_joint",
                ".*_hip_pitch_joint",
                ".*_knee_joint",
                "waist_yaw_joint",
            ],
            effort_limit_sim=300,
            stiffness={
                ".*_hip_yaw_joint": 150.0,
                ".*_hip_roll_joint": 150.0,
                ".*_hip_pitch_joint": 200.0,
                ".*_knee_joint": 200.0,
                "waist_yaw_joint": 200.0,
            },
            damping={
                ".*_hip_yaw_joint": 5.0,
                ".*_hip_roll_joint": 5.0,
                ".*_hip_pitch_joint": 5.0,
                ".*_knee_joint": 5.0,
                "waist_yaw_joint": 5.0,
            },
            armature=0.01,
        ),
        "feet": ImplicitActuatorCfg(
            effort_limit_sim=20,
            joint_names_expr=[".*_ankle_pitch_joint", ".*_ankle_roll_joint"],
            stiffness=20.0,
            damping=2.0,
            armature=0.01,
        ),
        "arms": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_shoulder_pitch_joint",
                ".*_shoulder_roll_joint",
                ".*_shoulder_yaw_joint",
                ".*_elbow_joint",
                ".*_wrist_roll_joint",
            ],
            effort_limit_sim=180,
            stiffness=220.0,
            damping=22.0,
            armature=0.01,
        ),
    }
    return cfg


def g1_inspire_ftp_cfg() -> ArticulationCfg:
    """Prefer locally converted unitree_ros mesh; fall back to Isaac Lab Nucleus stub path."""
    cfg = G1_INSPIRE_FTP_CFG.copy()
    cfg.prim_path = "{ENV_REGEX_NS}/Robot"
    local = local_inspire_usd()
    if local is not None:
        cfg.spawn.usd_path = str(local)
    cfg.spawn.articulation_props.fix_root_link = True
    cfg.spawn.rigid_props.disable_gravity = False
    cfg.init_state = ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.74),
        joint_pos={
            ".*_hip_pitch_joint": -0.20,
            ".*_knee_joint": 0.42,
            ".*_ankle_pitch_joint": -0.23,
            "left_shoulder_roll_joint": 0.16,
            "left_shoulder_pitch_joint": 0.35,
            "right_shoulder_roll_joint": -0.16,
            "right_shoulder_pitch_joint": 0.35,
            ".*_elbow_joint": 0.87,
        },
        joint_vel={".*": 0.0},
    )
    # Ensure arms/hands actuators exist even if Nucleus CFG evolves.
    cfg.actuators["arms"] = ImplicitActuatorCfg(
        joint_names_expr=[
            ".*_shoulder_pitch_joint",
            ".*_shoulder_roll_joint",
            ".*_shoulder_yaw_joint",
            ".*_elbow_joint",
            ".*_wrist_.*_joint",
        ],
        effort_limit=300,
        velocity_limit=100,
        stiffness=3000.0,
        damping=100.0,
    )
    cfg.actuators["hands"] = ImplicitActuatorCfg(
        joint_names_expr=[
            ".*_index_.*",
            ".*_middle_.*",
            ".*_thumb_.*",
            ".*_ring_.*",
            ".*_little_.*",
            ".*_pinky_.*",
        ],
        effort_limit_sim=30.0,
        velocity_limit_sim=10.0,
        stiffness=10.0,
        damping=0.2,
        armature=0.001,
    )
    return cfg
