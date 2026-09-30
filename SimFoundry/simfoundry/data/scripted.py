"""Scripted stump motions. Actions are default-pose offsets in the 23 DoF order."""

from __future__ import annotations

import math

import numpy as np

from simfoundry.data.real_keyframes import (
    LEFT_CONTACT_SIM,
    LEFT_DRIVE_SIM,
    LEFT_REACH,
    RIGHT_CONTACT_SIM,
    RIGHT_DRIVE_SIM,
    RIGHT_REACH,
    SWEEP_ROLL,
    ZERO,
    ArmKeyframe,
    Side,
    clamp_above_table,
)
from simfoundry.embodiment import G1_23DOF_JOINT_NAMES

_LEFT_HIP_PITCH = G1_23DOF_JOINT_NAMES.index("left_hip_pitch_joint")
_LEFT_KNEE = G1_23DOF_JOINT_NAMES.index("left_knee_joint")
_LEFT_ANKLE_PITCH = G1_23DOF_JOINT_NAMES.index("left_ankle_pitch_joint")
_RIGHT_HIP_PITCH = G1_23DOF_JOINT_NAMES.index("right_hip_pitch_joint")
_RIGHT_KNEE = G1_23DOF_JOINT_NAMES.index("right_knee_joint")
_RIGHT_ANKLE_PITCH = G1_23DOF_JOINT_NAMES.index("right_ankle_pitch_joint")
_TORSO = G1_23DOF_JOINT_NAMES.index("torso_joint")
_LEFT_SHOULDER_PITCH = G1_23DOF_JOINT_NAMES.index("left_shoulder_pitch_joint")
_LEFT_SHOULDER_ROLL = G1_23DOF_JOINT_NAMES.index("left_shoulder_roll_joint")
_LEFT_SHOULDER_YAW = G1_23DOF_JOINT_NAMES.index("left_shoulder_yaw_joint")
_LEFT_ELBOW_PITCH = G1_23DOF_JOINT_NAMES.index("left_elbow_pitch_joint")
_RIGHT_SHOULDER_PITCH = G1_23DOF_JOINT_NAMES.index("right_shoulder_pitch_joint")
_RIGHT_SHOULDER_ROLL = G1_23DOF_JOINT_NAMES.index("right_shoulder_roll_joint")
_RIGHT_SHOULDER_YAW = G1_23DOF_JOINT_NAMES.index("right_shoulder_yaw_joint")
_RIGHT_ELBOW_PITCH = G1_23DOF_JOINT_NAMES.index("right_elbow_pitch_joint")
_RIGHT_ELBOW_ROLL = G1_23DOF_JOINT_NAMES.index("right_elbow_roll_joint")
_LEFT_ELBOW_ROLL = G1_23DOF_JOINT_NAMES.index("left_elbow_roll_joint")


def _smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)


def _ease_in_out(x: float) -> float:
    """Quintic ease for silkier Kit playback than cubic smoothstep."""
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def _pin_inactive_arm(action: np.ndarray, active: Side, *, phase: float) -> None:
    """Keep the non-pushing arm in its lower-corner rest (do not pull it across the body)."""
    if phase < 0.45:
        return
    tuck = _smoothstep(min(1.0, (phase - 0.45) / 0.35))
    if active == "left":
        # Mild +roll counters left-sweep coupling that flings the right palm to −Y.
        action[_RIGHT_SHOULDER_PITCH] = 0.12 * tuck
        action[_RIGHT_SHOULDER_ROLL] = 0.14 * tuck
        action[_RIGHT_SHOULDER_YAW] = 0.02 * tuck
        action[_RIGHT_ELBOW_PITCH] = 0.10 * tuck
        return
    action[_LEFT_SHOULDER_PITCH] = 0.12 * tuck
    action[_LEFT_SHOULDER_ROLL] = -0.14 * tuck
    action[_LEFT_SHOULDER_YAW] = -0.02 * tuck
    action[_LEFT_ELBOW_PITCH] = 0.10 * tuck


def _apply_arm_keyframe(
    action: np.ndarray,
    side: Side,
    kf: ArmKeyframe,
    *,
    roll_extra: float = 0.0,
) -> None:
    if side == "right":
        action[_RIGHT_SHOULDER_PITCH] = kf.pitch
        action[_RIGHT_SHOULDER_ROLL] = kf.roll + roll_extra
        action[_RIGHT_SHOULDER_YAW] = kf.yaw
        action[_RIGHT_ELBOW_PITCH] = kf.elbow
        action[_RIGHT_ELBOW_ROLL] = kf.wrist
        return
    action[_LEFT_SHOULDER_PITCH] = kf.pitch
    action[_LEFT_SHOULDER_ROLL] = kf.roll + roll_extra
    action[_LEFT_SHOULDER_YAW] = kf.yaw
    action[_LEFT_ELBOW_PITCH] = kf.elbow
    action[_LEFT_ELBOW_ROLL] = kf.wrist


def _sorting_arm_pose(
    phase: float,
    side: Side,
    *,
    sweep_sign: float = 1.0,
) -> tuple[ArmKeyframe, float]:
    """Real-robot push/sort keyframes: reach → contact → drive → tabletop sweep.

    Phase breakpoints: 8% idle, 35% reach, 52% contact, 72% drive, then sweep.
    ``sweep_sign``: +1 pushes toward +Y (robot/table left), −1 toward −Y (right).
    Left=black file box left; right=kraft box right (matches teleop).
    """
    reach = RIGHT_REACH if side == "right" else LEFT_REACH
    contact = RIGHT_CONTACT_SIM if side == "right" else LEFT_CONTACT_SIM
    drive = RIGHT_DRIVE_SIM if side == "right" else LEFT_DRIVE_SIM

    roll_extra = 0.0
    if phase < 0.08:
        return ZERO, 0.0
    if phase < 0.35:
        t = _ease_in_out((phase - 0.08) / 0.27)
        pose = ZERO.lerp(reach, t)
    elif phase < 0.52:
        t = _ease_in_out((phase - 0.35) / 0.17)
        pose = reach.lerp(contact, t)
    elif phase < 0.68:
        t = _ease_in_out((phase - 0.52) / 0.16)
        pose = contact.lerp(drive, t)
    else:
        t = _smoothstep((phase - 0.68) / 0.32)
        pose = drive
        roll_extra = sweep_sign * SWEEP_ROLL * t
    # Match 1_t0.5.jpg: palms stay above the blue table for the whole motion.
    return clamp_above_table(pose), roll_extra


def walking_gait(t_s: float, amplitude: float = 1.0) -> np.ndarray:
    """In-place / locomoting gait offsets on top of the default standing pose.

    Cadence ~1.55 Hz. ``amplitude`` in [0, 1] scales step size (use ~0.35 for turning).
    """
    action = np.zeros(23, dtype=np.float32)
    amp = max(0.0, min(1.0, float(amplitude)))
    if amp < 1e-3:
        return action
    phase = 2.0 * math.pi * 1.55 * t_s
    swing_l = math.sin(phase)
    swing_r = math.sin(phase + math.pi)
    hip = 0.42 * amp
    knee = 0.32 * amp
    ankle = 0.20 * amp
    action[_LEFT_HIP_PITCH] = hip * swing_l
    action[_RIGHT_HIP_PITCH] = hip * swing_r
    action[_LEFT_KNEE] = knee * max(0.0, swing_l)
    action[_RIGHT_KNEE] = knee * max(0.0, swing_r)
    action[_LEFT_ANKLE_PITCH] = -ankle * swing_l
    action[_RIGHT_ANKLE_PITCH] = -ankle * swing_r
    action[_TORSO] = 0.05 * amp * math.sin(phase * 0.5)
    action[_LEFT_SHOULDER_PITCH] = 0.22 * amp * swing_r
    action[_RIGHT_SHOULDER_PITCH] = 0.22 * amp * swing_l
    return action


def scripted_push_cup_to_bowl(step: int, horizon: int) -> np.ndarray:
    """Right-arm reach then lateral sweep that visibly contacts the cup."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)

    if phase < 0.10:
        return action

    if phase < 0.42:
        s = _smoothstep((phase - 0.10) / 0.32)
        action[_RIGHT_SHOULDER_PITCH] = 0.48 * s
        action[_RIGHT_SHOULDER_ROLL] = -0.12 * s
        action[_RIGHT_SHOULDER_YAW] = -0.18 * s
        action[_RIGHT_ELBOW_PITCH] = -0.55 * s
        action[_RIGHT_ELBOW_ROLL] = 0.08 * s
        return action

    s = _smoothstep((phase - 0.42) / 0.58)
    action[_RIGHT_SHOULDER_PITCH] = 0.48 + 0.06 * s
    action[_RIGHT_SHOULDER_ROLL] = -0.12 + 0.42 * s
    action[_RIGHT_SHOULDER_YAW] = -0.18 - 0.06 * s
    action[_RIGHT_ELBOW_PITCH] = -0.55
    action[_RIGHT_ELBOW_ROLL] = 0.08
    return action


def scripted_pick_cup(step: int, horizon: int) -> np.ndarray:
    """Fast smooth reach → grasp pose → lift (≤10s Kit demo companion).

    Phases (fraction of horizon):
      0.00–0.12  settle
      0.12–0.48  reach to cup (ease-in-out)
      0.48–0.62  hold grasp pose (demo attaches cup here)
      0.62–1.00  lift / retract
    """
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)

    reach = np.array(
        [
            0.38,  # shoulder pitch +
            -0.18,  # shoulder roll
            -0.22,  # shoulder yaw
            -0.55,  # elbow pitch
            0.08,  # elbow roll
        ],
        dtype=np.float32,
    )
    lift = np.array(
        [
            0.18,
            -0.10,
            -0.12,
            -0.35,
            0.05,
        ],
        dtype=np.float32,
    )

    if phase < 0.12:
        return action

    if phase < 0.48:
        s = _ease_in_out((phase - 0.12) / 0.36)
        target = reach * s
    elif phase < 0.62:
        target = reach
    else:
        s = _ease_in_out((phase - 0.62) / 0.38)
        target = reach * (1.0 - s) + lift * s

    action[_RIGHT_SHOULDER_PITCH] = target[0]
    action[_RIGHT_SHOULDER_ROLL] = target[1]
    action[_RIGHT_SHOULDER_YAW] = target[2]
    action[_RIGHT_ELBOW_PITCH] = target[3]
    action[_RIGHT_ELBOW_ROLL] = target[4]
    return action


def scripted_wave_hello(step: int, horizon: int) -> np.ndarray:
    """Raise the right arm and wave (lobby demo, no locomotion)."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)
    if phase < 0.10:
        return action
    lift = _ease_in_out(min(1.0, (phase - 0.10) / 0.20))
    action[_RIGHT_SHOULDER_PITCH] = 0.72 * lift
    action[_RIGHT_SHOULDER_ROLL] = -0.48 * lift
    action[_RIGHT_SHOULDER_YAW] = -0.18 * lift
    action[_RIGHT_ELBOW_PITCH] = -0.32 * lift
    if phase > 0.30:
        wave = math.sin((phase - 0.30) * 12.0 * math.pi)
        action[_RIGHT_SHOULDER_ROLL] += 0.28 * wave * lift
        action[_RIGHT_ELBOW_ROLL] = 0.22 * wave
    return action


def scripted_press_wall_button(step: int, horizon: int) -> np.ndarray:
    """Reach the right stump toward a wall button on the robot's right, then hold."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)
    if phase < 0.08:
        return action
    s = _ease_in_out(min(1.0, (phase - 0.08) / 0.32))
    press = 1.0
    if phase > 0.48:
        press = 1.0 + 0.12 * _smoothstep(min(1.0, (phase - 0.48) / 0.18))
    action[_RIGHT_SHOULDER_PITCH] = 0.42 * s
    action[_RIGHT_SHOULDER_ROLL] = -0.82 * s * press
    action[_RIGHT_SHOULDER_YAW] = 0.28 * s
    action[_RIGHT_ELBOW_PITCH] = -0.55 * s
    action[_RIGHT_ELBOW_ROLL] = 0.10 * s
    return action


def scripted_push_door(step: int, horizon: int) -> np.ndarray:
    """Both arms forward to shove the swing door."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)
    if phase < 0.08:
        return action
    s = _ease_in_out(min(1.0, (phase - 0.08) / 0.35))
    shove = 1.0
    if phase > 0.45:
        shove = 1.0 + 0.15 * _smoothstep(min(1.0, (phase - 0.45) / 0.25))
    action[_LEFT_SHOULDER_PITCH] = 0.52 * s * shove
    action[_RIGHT_SHOULDER_PITCH] = 0.52 * s * shove
    action[_LEFT_SHOULDER_ROLL] = 0.12 * s
    action[_RIGHT_SHOULDER_ROLL] = -0.12 * s
    action[_LEFT_ELBOW_PITCH] = -0.58 * s
    action[_RIGHT_ELBOW_PITCH] = -0.58 * s
    return action


def scripted_nudge_left(step: int, horizon: int) -> np.ndarray:
    """Reach forward then sweep the right stump toward the robot's left."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)
    if phase < 0.10:
        return action
    if phase < 0.40:
        s = _smoothstep((phase - 0.10) / 0.30)
        action[_RIGHT_SHOULDER_PITCH] = 0.50 * s
        action[_RIGHT_SHOULDER_ROLL] = -0.10 * s
        action[_RIGHT_SHOULDER_YAW] = -0.12 * s
        action[_RIGHT_ELBOW_PITCH] = -0.50 * s
        return action
    s = _smoothstep((phase - 0.40) / 0.60)
    action[_RIGHT_SHOULDER_PITCH] = 0.50
    action[_RIGHT_SHOULDER_ROLL] = -0.10 + 0.55 * s
    action[_RIGHT_SHOULDER_YAW] = -0.12
    action[_RIGHT_ELBOW_PITCH] = -0.50
    return action


def scripted_press_table_switch(step: int, horizon: int) -> np.ndarray:
    """Reach forward/down onto a bench switch."""
    action = np.zeros(23, dtype=np.float32)
    phase = step / max(horizon - 1, 1)
    if phase < 0.10:
        return action
    s = _ease_in_out(min(1.0, (phase - 0.10) / 0.35))
    dip = 1.0
    if phase > 0.50:
        dip = 1.0 + 0.18 * _smoothstep(min(1.0, (phase - 0.50) / 0.20))
    action[_RIGHT_SHOULDER_PITCH] = 0.55 * s * dip
    action[_RIGHT_SHOULDER_ROLL] = -0.16 * s
    action[_RIGHT_SHOULDER_YAW] = -0.10 * s
    action[_RIGHT_ELBOW_PITCH] = -0.62 * s
    return action


def scripted_push_toward_right(step: int, horizon: int, *, phase: float | None = None) -> np.ndarray:
    """Right arm on kraft (wood) box → sweep toward −Y (table right)."""
    action = np.zeros(23, dtype=np.float32)
    if phase is None:
        phase = step / max(horizon - 1, 1)
    pose, roll_extra = _sorting_arm_pose(phase, "right", sweep_sign=-1.0)
    if phase >= 0.18:
        reach = _smoothstep(min(1.0, (phase - 0.18) / 0.28))
        pose = ArmKeyframe(pose.pitch - 0.12 * reach, pose.roll, pose.yaw, pose.elbow, pose.wrist)
    if phase >= 0.48:
        shove = _smoothstep(min(1.0, (phase - 0.48) / 0.32))
        roll_extra -= 0.32 * shove
        pose = ArmKeyframe(pose.pitch, pose.roll - 0.14 * shove, pose.yaw, pose.elbow, pose.wrist)
    _apply_arm_keyframe(action, "right", pose, roll_extra=roll_extra)
    _pin_inactive_arm(action, "right", phase=phase)
    return action


def scripted_sweep_parcels_apart(step: int, horizon: int, *, phase: float | None = None) -> np.ndarray:
    """Both arms: black mailer → +Y (left), wood box → −Y (right)."""
    action = np.zeros(23, dtype=np.float32)
    if phase is None:
        phase = step / max(horizon - 1, 1)
    left_pose, left_roll = _sorting_arm_pose(phase, "left", sweep_sign=1.0)
    right_pose, right_roll = _sorting_arm_pose(phase, "right", sweep_sign=-1.0)
    _apply_arm_keyframe(action, "left", left_pose, roll_extra=left_roll)
    _apply_arm_keyframe(action, "right", right_pose, roll_extra=right_roll)
    return action


def scripted_nudge_mailer_across(step: int, horizon: int, *, phase: float | None = None) -> np.ndarray:
    """Left arm on black mailer → sweep toward +Y (table left)."""
    action = np.zeros(23, dtype=np.float32)
    if phase is None:
        phase = step / max(horizon - 1, 1)
    pose, roll_extra = _sorting_arm_pose(phase, "left", sweep_sign=1.0)
    if phase >= 0.18:
        reach = _smoothstep(min(1.0, (phase - 0.18) / 0.28))
        pose = ArmKeyframe(pose.pitch - 0.14 * reach, pose.roll, pose.yaw, pose.elbow, pose.wrist)
    if phase >= 0.48:
        shove = _smoothstep(min(1.0, (phase - 0.48) / 0.32))
        roll_extra += 0.36 * shove
        pose = ArmKeyframe(pose.pitch, pose.roll + 0.16 * shove, pose.yaw, pose.elbow, pose.wrist)
    _apply_arm_keyframe(action, "left", pose, roll_extra=roll_extra)
    _pin_inactive_arm(action, "left", phase=phase)
    return action


def scripted_action(
    task_id: str,
    step: int,
    horizon: int,
    *,
    phase_bias: float = 0.0,
    action_noise: float = 0.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Return default-pose joint offsets; optional phase/noise for domain variation."""

    def _phase(s: int) -> float:
        return min(1.0, max(0.0, s / max(horizon - 1, 1) + phase_bias))

    def _with_noise(action: np.ndarray) -> np.ndarray:
        if action_noise <= 0.0:
            return action
        gen = rng if rng is not None else np.random.default_rng()
        noise = gen.normal(0.0, action_noise, size=action.shape).astype(np.float32)
        # Keep legs/waist steady; vary arms only.
        noise[:13] = 0.0
        return action + noise

    if task_id == "push_cup_to_bowl":
        return _with_noise(scripted_push_cup_to_bowl(step, horizon))
    if task_id == "pick_cup":
        return _with_noise(scripted_pick_cup(step, horizon))
    if task_id == "reach_cup":
        clipped = min(step, max(horizon // 2, 1))
        return _with_noise(scripted_push_cup_to_bowl(clipped, horizon))
    if task_id == "press_wall_button":
        return _with_noise(scripted_press_wall_button(step, horizon))
    if task_id == "push_door":
        return _with_noise(scripted_push_door(step, horizon))
    if task_id in {"press_table_switch", "press_table_switch"}:
        return _with_noise(scripted_press_table_switch(step, horizon))
    if task_id in {"nudge_bottle_left", "sweep_bottle_aside", "clear_front_zone", "push_box_along_table"}:
        return _with_noise(scripted_nudge_left(step, horizon))
    if task_id in {"approach_counter", "approach_table", "wait_no_package"}:
        return _with_noise(np.zeros(23, dtype=np.float32))
    phase = _phase(step)
    if task_id == "push_box_to_bin":
        return _with_noise(scripted_push_toward_right(step, horizon, phase=phase))
    if task_id == "nudge_mailer_to_bin":
        return _with_noise(scripted_nudge_mailer_across(step, horizon, phase=phase))
    if task_id == "sweep_parcels_apart":
        return _with_noise(scripted_sweep_parcels_apart(step, horizon, phase=phase))
    if task_id in {
        "wave_hello",
        "wave_hello",
        "point_at_person",
        "enter_and_push_cup",
        "enter_and_push_cup",
    }:
        return _with_noise(scripted_wave_hello(step, horizon))
    raise KeyError(f"no scripted policy for task_id={task_id}")


scripted_action = scripted_action
walking_gait = walking_gait


def sine_probe(step: int, horizon: int, amplitude: float = 0.08) -> np.ndarray:
    """Tiny arm wiggle used only as a pipeline probe."""
    action = np.zeros(23, dtype=np.float32)
    t = 2.0 * math.pi * step / max(horizon, 1)
    action[_RIGHT_SHOULDER_PITCH] = amplitude * math.sin(t)
    return action
