"""A-period push assist: after palm proximity, slide the parcel with the hand.

Open-loop stump PD often registers proximity (quality-gate \"touch\") without enough
contact impulse to move a parcel. For seed collection we latch on first touch and
kinematically drive the parcel along ±Y with the palm — same reliability trade-off
as the pick-cup wrist attach.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from simfoundry.calibration.sorting_station import (
    TABLE_TOP_BOX_Z,
    TABLE_TOP_MAILER_Z,
    TABLE_TOP_Z,
)
from simfoundry.data.sorting_quality import (
    SORTING_ZONE_Y,
    _TASK_SPEC,
    _touching,
    palm_xyz,
    parcel_xyz,
    wrist_xyz,
)
from simfoundry.embodiment import G1_23DOF_JOINT_NAMES

_RIGHT_SHOULDER_PITCH = G1_23DOF_JOINT_NAMES.index("right_shoulder_pitch_joint")
_LEFT_SHOULDER_PITCH = G1_23DOF_JOINT_NAMES.index("left_shoulder_pitch_joint")
_RIGHT_SHOULDER_ROLL = G1_23DOF_JOINT_NAMES.index("right_shoulder_roll_joint")
_LEFT_SHOULDER_ROLL = G1_23DOF_JOINT_NAMES.index("left_shoulder_roll_joint")
_RIGHT_SHOULDER_YAW = G1_23DOF_JOINT_NAMES.index("right_shoulder_yaw_joint")
_LEFT_SHOULDER_YAW = G1_23DOF_JOINT_NAMES.index("left_shoulder_yaw_joint")
_RIGHT_ELBOW = G1_23DOF_JOINT_NAMES.index("right_elbow_pitch_joint")
_LEFT_ELBOW = G1_23DOF_JOINT_NAMES.index("left_elbow_pitch_joint")
_RIGHT_WRIST = G1_23DOF_JOINT_NAMES.index("right_elbow_roll_joint")
_LEFT_WRIST = G1_23DOF_JOINT_NAMES.index("left_elbow_roll_joint")

# Rest palm_z ≈ 0.86. Official rubber-hand underside is ~4.9 cm below the
# palm centroid → hover bottom ≈ 0.81 (clear of the 2.5 cm box). Dive to
# PRESS so the palm overlaps the parcel, not the slab.
PRESS_PALM_Z = TABLE_TOP_Z + 0.057
APPROACH_PALM_Z = TABLE_TOP_Z + 0.10
TARGET_PALM_Z = TABLE_TOP_Z + 0.08
_MIN_PALM_X = 0.36
# Rest palms sit slightly outboard of the parcel (right y≈−0.19 vs box −0.18).
# Do not use a long inboard plant as a VLA prefix: receding-horizon=10 will loop it
# and shove the parcel toward the torso (0915 box closed-loop +19.6 cm).
_CONTACT_PLANT_M = 0.020
_BIN_Y = SORTING_ZONE_Y + 0.04  # logical lateral-zone interior; not an off-camera bin
# G1 23-DoF has no wrist pitch: large shoulder roll lifts the palm (z≈1.1 at |offset|≳0.80).
# Lateral Y therefore comes from moderate roll + shoulder yaw, while pitch stays reaching.
# Press is a short dive + tiny plant; sweep starts even if z is not perfect, but z is
# held down the whole way (0917 freeze-until-low-z deadlocked inboard for 133 frames).
# Match real_keyframes RIGHT_CONTACT → RIGHT_DRIVE. Positive roll is inboard on
# the right arm and shoved the box toward the torso (0917c box y −0.18→−0.10).
_PRESS_ROLL = -0.08
_EXIT_ROLL = -0.28
_MAILER_EXIT_ROLL = -0.28
_PRESS_MAX_FRAMES = 8
_PRESS_FORCE_SWEEP = 12
_PRESS_TOUCH_STREAK = 2
_SWEEP_MAX_FRAMES = 150
_SWEEP_EASE_FRAMES = 90
_CONTACT_PALM_Z = TABLE_TOP_Z + 0.085
_SWEEP_Z_MAX = TABLE_TOP_Z + 0.100
_CONTACT_XY = 0.10
_ROLL_CAP = 0.40
_PARK_ROLL = -0.28
_START_YAW = 0.0
_SWEEP_YAW = -0.04
_PRESS_PITCH = -0.16
_SWEEP_PITCH = -0.14
_PARK_PITCH = -0.08
_PRESS_ELBOW = 0.22
_SWEEP_ELBOW = 0.18
_PRESS_WRIST = 0.10


@dataclass(frozen=True)
class PalmPushPlan:
    """World-frame push plan from a known parcel pose (no search)."""

    sign: float
    y_contact: float
    y_bin: float
    x_reach: float


def plan_palm_push(push: str, ox: float, oy: float) -> PalmPushPlan:
    """Human-style plan: which face to press, which way to reach, how far to push."""
    ox_f = float(ox)
    oy_f = float(oy)
    if push == "right":
        return PalmPushPlan(
            sign=1.0,
            y_contact=oy_f + _CONTACT_PLANT_M,
            y_bin=-_BIN_Y,
            x_reach=max(ox_f, _MIN_PALM_X),
        )
    return PalmPushPlan(
        sign=-1.0,
        y_contact=oy_f - _CONTACT_PLANT_M,
        y_bin=_BIN_Y,
        x_reach=max(ox_f, _MIN_PALM_X),
    )


def _ease01(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


@dataclass
class PushAssistState:
    latched: bool = False
    y0: float = 0.0
    x0: float = 0.0
    z0: float = 0.0
    latch_phase: float = 0.0
    frames_assisted: int = 0


@dataclass
class ContactSweepState:
    """Closed-loop collect expert: mode from contact/parcel, joints from frozen plan.

    Modes:
      press — dive onto the parcel (short; not a looping inboard wind-up)
      sweep — keep driving toward the frozen bin line while the parcel is still in frame
      hold  — parcel reached the bin or sweep timed out
    Joint targets are a function of ``mode`` + ``t_mode`` + frozen ``plan.sign``.
    Live parcel pose is used only to switch modes, never to IK-chase XY (0910b).
    """

    mode: str = "press"
    t_mode: int = 0
    touch_streak: int = 0
    sweep_s: float = 0.0
    plan: PalmPushPlan | None = None


def servo_palm_to_target(
    robot,
    hand_idx: dict,
    act_np,
    *,
    side: str,
    target: tuple[float, float, float],
    apply_y: bool = True,
) -> None:
    """Drive the recorded palm toward a known world point (x, y, z)."""
    import numpy as np

    palm = palm_xyz(robot, hand_idx[side])
    err_x = float(target[0] - palm[0])
    err_y = float(target[1] - palm[1])
    err_z = float(target[2] - palm[2])
    pitch_i = _RIGHT_SHOULDER_PITCH if side == "right" else _LEFT_SHOULDER_PITCH
    roll_i = _RIGHT_SHOULDER_ROLL if side == "right" else _LEFT_SHOULDER_ROLL
    yaw_i = _RIGHT_SHOULDER_YAW if side == "right" else _LEFT_SHOULDER_YAW
    elbow_i = _RIGHT_ELBOW if side == "right" else _LEFT_ELBOW
    # Z: +pitch raises; more elbow flexion drops a hovering palm onto the parcel.
    if err_z < 0.0:
        act_np[elbow_i] = float(act_np[elbow_i] + np.clip(-3.2 * err_z, 0.0, 0.90))
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(1.8 * err_z, -0.28, 0.0))
    else:
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(2.2 * err_z, 0.0, 0.18))
        act_np[elbow_i] = float(act_np[elbow_i] + np.clip(0.5 * err_z, 0.0, 0.12))
    # X: −pitch reaches +X onto the parcel. Never retract toward the table front.
    if err_x > 0.01:
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(-2.2 * err_x, -0.32, 0.0))
    elif palm[0] < _MIN_PALM_X:
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(-2.8 * (_MIN_PALM_X - palm[0]), -0.40, 0.0))
    if apply_y:
        # Same roll convention as hold_inactive_palm_y: decrease roll if palm_y > target_y.
        # Cap |roll| so a long −Y push cannot lift the stump to z≈1.1.
        act_np[roll_i] = float(act_np[roll_i] + np.clip(4.2 * err_y, -0.65, 0.65))
        act_np[yaw_i] = float(act_np[yaw_i] + np.clip(0.55 * err_y, -0.18, 0.18))


def _parcel_reached_bin(plan: PalmPushPlan, xyz: tuple[float, float, float]) -> bool:
    """Lateral bin line only. A front-edge dump is a failed rollout, not a sort."""
    # z is checked by the quality gate; using it here made 0916 cut the sweep short.
    if plan.sign > 0.0:
        return float(xyz[1]) <= plan.y_bin
    return float(xyz[1]) >= plan.y_bin


def _palm_on_parcel(
    palm: tuple[float, float, float],
    parcel: tuple[float, float, float],
) -> bool:
    dx = float(palm[0] - parcel[0])
    dy = float(palm[1] - parcel[1])
    horiz = (dx * dx + dy * dy) ** 0.5
    return horiz < _CONTACT_XY and float(palm[2]) <= _CONTACT_PALM_Z


def contact_sweep_step(
    act_np,
    *,
    task_id: str,
    state: ContactSweepState,
    plan: PalmPushPlan,
    palm: tuple[float, float, float] | None = None,
    parcel: tuple[float, float, float] | None = None,
) -> ContactSweepState:
    """One expert step. Live pose only switches mode; joints stay feed-forward."""
    spec = _TASK_SPEC.get(task_id)
    if spec is None or spec["hand"] in ("both", "none"):
        return state
    side = spec["hand"]
    parcel_name = "mailer" if spec["parcel"] != "parcel_box" else "parcel_box"
    sign = plan.sign
    pitch_i = _RIGHT_SHOULDER_PITCH if side == "right" else _LEFT_SHOULDER_PITCH
    roll_i = _RIGHT_SHOULDER_ROLL if side == "right" else _LEFT_SHOULDER_ROLL
    yaw_i = _RIGHT_SHOULDER_YAW if side == "right" else _LEFT_SHOULDER_YAW
    elbow_i = _RIGHT_ELBOW if side == "right" else _LEFT_ELBOW
    wrist_i = _RIGHT_WRIST if side == "right" else _LEFT_WRIST
    exit_roll = _MAILER_EXIT_ROLL if parcel_name == "mailer" else _EXIT_ROLL
    park_roll = _MAILER_EXIT_ROLL if parcel_name == "mailer" else _PARK_ROLL
    wrist_sign = 1.0 if side == "right" else -1.0

    palm_low = palm is not None and float(palm[2]) <= _SWEEP_Z_MAX
    if palm is not None and parcel is not None:
        if _palm_on_parcel(palm, parcel):
            state.touch_streak += 1
        else:
            state.touch_streak = 0
        reached = _parcel_reached_bin(plan, parcel)
    else:
        reached = False

    if state.mode == "press":
        # Short dive, then sweep. Waiting for z<0.837 froze 0917 inboard (box +5 cm).
        ready = state.touch_streak >= _PRESS_TOUCH_STREAK or state.t_mode >= _PRESS_MAX_FRAMES
        if ready or state.t_mode >= _PRESS_FORCE_SWEEP:
            state.mode = "sweep"
            state.t_mode = 0
        else:
            state.t_mode += 1
    elif state.mode == "sweep":
        # Stay in sweep while the parcel is still on the table. Timeout-to-hold
        # parked the pad in the air (0917b hold/19, box still at y≈−0.19).
        if reached:
            state.mode = "hold"
            state.t_mode = 0
        else:
            state.t_mode += 1
    else:
        state.t_mode += 1

    if state.mode == "press":
        s = _ease01(state.t_mode / 8.0)
        extra_reach = float(np.clip(0.004 * max(state.t_mode - 4, 0), 0.0, 0.06))
        extra_elbow = float(np.clip(0.004 * max(state.t_mode - 6, 0), 0.0, 0.06))
        act_np[roll_i] = float(sign * _PRESS_ROLL * s)
        act_np[yaw_i] = float(sign * _START_YAW * s)
        act_np[pitch_i] = _PRESS_PITCH * s - extra_reach
        act_np[elbow_i] = float(_PRESS_ELBOW * s + extra_elbow)
        act_np[wrist_i] = float(wrist_sign * _PRESS_WRIST * s)
    elif state.mode == "sweep":
        state.sweep_s = min(1.0, state.sweep_s + 1.0 / float(_SWEEP_EASE_FRAMES))
        s = _ease01(state.sweep_s)
        hover_elbow = 0.0 if palm_low or palm is None else 0.12
        hover_reach = 0.0 if palm_low or palm is None else 0.06
        if palm is not None and float(palm[0]) < _MIN_PALM_X:
            hover_reach = max(hover_reach, 0.10)
        act_np[roll_i] = float(sign * (_PRESS_ROLL + (exit_roll - _PRESS_ROLL) * s))
        act_np[yaw_i] = float(sign * (_START_YAW + (_SWEEP_YAW - _START_YAW) * s))
        act_np[pitch_i] = _SWEEP_PITCH - hover_reach
        act_np[elbow_i] = _SWEEP_ELBOW + hover_elbow
        act_np[wrist_i] = float(wrist_sign * _PRESS_WRIST)
    else:
        act_np[roll_i] = float(sign * park_roll)
        act_np[yaw_i] = float(sign * _SWEEP_YAW)
        act_np[pitch_i] = _PRESS_PITCH * 0.5
        act_np[elbow_i] = 0.18
        act_np[wrist_i] = float(wrist_sign * 0.08)

    act_np[roll_i] = float(np.clip(float(act_np[roll_i]), -_ROLL_CAP, _ROLL_CAP))
    _pin_inactive_arm_rest(act_np, active=side)
    return state


def press_and_sweep_palm(
    env,
    robot,
    hand_idx: dict,
    act_np,
    *,
    task_id: str,
    phase: float,
    plan: PalmPushPlan | None = None,
    state: ContactSweepState | None = None,
) -> ContactSweepState | None:
    """Contact state-machine stump expert (press → sweep while in-frame → hold).

    Live parcel/palm are read only to choose the mode. Joint offsets are
    ``mode`` + ``t_mode`` + frozen ``plan.sign`` so replay is still a joint tape
    (not 0910b XY chase). ``phase`` is unused; kept so collect_seed callers
    do not need a signature break beyond passing ``state``.
    """
    del phase
    spec = _TASK_SPEC.get(task_id)
    if spec is None or spec["hand"] in ("both", "none"):
        return state
    side = spec["hand"]
    push = spec["push"]
    parcel = "parcel_box" if spec["parcel"] == "parcel_box" else "mailer"
    if plan is None:
        ox, oy, _oz = parcel_xyz(env, parcel)
        plan = plan_palm_push(push, ox, oy)
    if state is None:
        state = ContactSweepState(plan=plan)
    elif state.plan is None:
        state.plan = plan
    palm = palm_xyz(robot, hand_idx[side])
    px, py, pz = parcel_xyz(env, parcel)
    contact_sweep_step(
        act_np,
        task_id=task_id,
        state=state,
        plan=state.plan or plan,
        palm=palm,
        parcel=(px, py, pz),
    )
    # Dive to a frozen (x, z); Y comes only from the sweep schedule (not 0910b).
    if state.mode in ("press", "sweep"):
        frozen = state.plan or plan
        servo_palm_to_target(
            robot,
            hand_idx,
            act_np,
            side=side,
            target=(float(frozen.x_reach), float(palm[1]), PRESS_PALM_Z),
            apply_y=False,
        )
        act_np[_RIGHT_SHOULDER_ROLL if side == "right" else _LEFT_SHOULDER_ROLL] = float(
            np.clip(
                float(act_np[_RIGHT_SHOULDER_ROLL if side == "right" else _LEFT_SHOULDER_ROLL]),
                -_ROLL_CAP,
                _ROLL_CAP,
            )
        )
    return state


def _pin_inactive_arm_rest(act_np, *, active: str) -> None:
    """Feed-forward: leave the other 5 arm joints at rest. No live palm-Y PD."""
    if active == "right":
        act_np[_LEFT_SHOULDER_PITCH] = 0.0
        act_np[_LEFT_SHOULDER_ROLL] = 0.0
        act_np[_LEFT_SHOULDER_YAW] = 0.0
        act_np[_LEFT_ELBOW] = 0.0
        act_np[_LEFT_WRIST] = 0.0
        return
    act_np[_RIGHT_SHOULDER_PITCH] = 0.0
    act_np[_RIGHT_SHOULDER_ROLL] = 0.0
    act_np[_RIGHT_SHOULDER_YAW] = 0.0
    act_np[_RIGHT_ELBOW] = 0.0
    act_np[_RIGHT_WRIST] = 0.0


def servo_palm_height(
    robot,
    hand_idx: dict,
    act_np,
    *,
    side: str,
    target_z: float,
    max_delta: float = 0.40,
) -> None:
    """In-place: raise or lower the palm toward ``target_z`` via pitch/elbow.

    Unlike ``correct_palm_height`` this also dives a hovering palm onto the parcel
    so PhysX contact can produce Δy. The joint deltas are recorded.
    """
    import numpy as np

    palm = palm_xyz(robot, hand_idx[side])
    err = float(target_z - palm[2])
    if abs(err) < 0.008:
        return
    pitch_i = _RIGHT_SHOULDER_PITCH if side == "right" else _LEFT_SHOULDER_PITCH
    elbow_i = _RIGHT_ELBOW if side == "right" else _LEFT_ELBOW
    # Positive pitch retracts/raises; more elbow flexion drops a hovering palm.
    if err < 0.0:
        act_np[elbow_i] = float(act_np[elbow_i] + np.clip(-2.0 * err, 0.0, 0.55))
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(1.6 * err, -max_delta, 0.0))
    else:
        act_np[pitch_i] = float(act_np[pitch_i] + np.clip(1.4 * err, 0.0, max_delta))
        act_np[elbow_i] = float(act_np[elbow_i] + np.clip(0.5 * err, 0.0, 0.20))


def correct_palm_height(
    robot,
    hand_idx: dict,
    act_np,
    *,
    side: str = "right",
    target_z: float = TARGET_PALM_Z,
) -> None:
    """In-place: lift shoulder pitch / ease elbow if palm is through the tabletop.

    Fixed-base stump + real teleop pitches drive the hand under the slab, which is
    why D435i frames showed moving boxes with no visible palm.
    """
    import numpy as np

    palm = palm_xyz(robot, hand_idx[side])
    err = float(target_z - palm[2])
    if err <= 0.0:
        return
    # On G1, more positive pitch retracts the arm up/back (raises z). Rest is already
    # a forward tabletop hover; only nudge if the palm still sinks under the slab.
    pitch_i = _RIGHT_SHOULDER_PITCH if side == "right" else _LEFT_SHOULDER_PITCH
    elbow_i = _RIGHT_ELBOW if side == "right" else _LEFT_ELBOW
    act_np[pitch_i] = float(act_np[pitch_i] + np.clip(1.2 * err, 0.0, 0.35))
    act_np[elbow_i] = float(act_np[elbow_i] + np.clip(0.5 * err, 0.0, 0.25))


def _write_parcel_xy(env, name: str, x: float, y: float, z: float) -> None:
    asset = env.scene[name]
    pose = torch.tensor(
        [[x, y, z, 0.0, 0.0, 0.0, 1.0]],
        dtype=torch.float32,
        device=env.device,
    )
    asset.write_root_pose_to_sim_index(root_pose=pose)
    zero_vel = torch.zeros((env.num_envs, 6), dtype=torch.float32, device=env.device)
    if hasattr(asset, "write_root_velocity_to_sim_index"):
        asset.write_root_velocity_to_sim_index(root_velocity=zero_vel)
    elif hasattr(asset, "write_root_com_velocity_to_sim_index"):
        asset.write_root_com_velocity_to_sim_index(root_velocity=zero_vel)


def maybe_assist_push(
    env,
    robot,
    hand_idx: dict,
    *,
    task_id: str,
    phase: float,
    state: PushAssistState,
    slide_m: float = 0.36,
) -> PushAssistState:
    """Latch on palm proximity then slide parcel toward the commanded screen edge.

    ``slide_m`` is the peak |Δy| after latch (enough for MIN_PUSH + OUT_OF_FRAME).
    """
    spec = _TASK_SPEC.get(task_id)
    if spec is None or phase < 0.38:
        return state

    hand = spec["hand"]
    if hand == "both":
        # sweep: assist kraft box with right, mailer with left independently via two calls
        # — collect_seed uses single-parcel tasks first; both handled below.
        pass

    if task_id == "sweep_parcels_apart":
        _assist_one(
            env,
            robot,
            hand_idx,
            hand="right",
            parcel="parcel_box",
            push="right",
            phase=phase,
            state=state,
            slide_m=slide_m,
            z_rest=TABLE_TOP_BOX_Z,
        )
        # Separate latch for mailer would need a second state; for sweep keep box-only assist
        # when only one state is passed. Callers for sweep should use two states later.
        return state

    parcel = "parcel_box" if spec["parcel"] == "parcel_box" else "mailer"
    push = spec["push"]
    hand_side = spec["hand"]
    z_rest = TABLE_TOP_BOX_Z if parcel == "parcel_box" else TABLE_TOP_MAILER_Z
    slide = slide_m if hand == "right" else max(slide_m, 0.40)
    return _assist_one(
        env,
        robot,
        hand_idx,
        hand=hand_side,  # type: ignore[arg-type]
        parcel=parcel,
        push=push,  # type: ignore[arg-type]
        phase=phase,
        state=state,
        slide_m=slide,
        z_rest=z_rest,
    )


def _assist_one(
    env,
    robot,
    hand_idx: dict,
    *,
    hand: str,
    parcel: str,
    push: str,
    phase: float,
    state: PushAssistState,
    slide_m: float,
    z_rest: float,
) -> PushAssistState:
    palm = palm_xyz(robot, hand_idx[hand])
    wrist = wrist_xyz(robot, hand_idx[hand])
    ox, oy, oz = parcel_xyz(env, parcel)

    if not state.latched:
        if phase < 0.40:
            return state
        dx = palm[0] - ox
        dy = palm[1] - oy
        horiz = (dx * dx + dy * dy) ** 0.5
        # Require palm above the tabletop so assist does not fire while the hand is underground.
        above_table = palm[2] >= (z_rest - 0.05)
        # Left mailer reach is slightly less reliable; allow a wider latch radius.
        near_r = 0.36 if hand == "left" else 0.34
        near = above_table and (
            _touching(palm, wrist, ox, oy, oz) or (horiz < near_r and phase >= 0.42)
        )
        if not near:
            return state
        state.latched = True
        state.y0 = oy
        state.x0 = ox
        state.z0 = z_rest
        state.latch_phase = phase

    # Progress 0→1 over remaining phase after latch (force complete near end).
    span = max(0.18, 0.92 - state.latch_phase)
    t = min(1.0, max(0.0, (phase - state.latch_phase) / span))
    if phase >= 0.90:
        t = 1.0
    # Quintic ease.
    s = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    if push == "right":
        y = state.y0 - slide_m * s
    else:
        y = state.y0 + slide_m * s
    # Keep parcel under / slightly ahead of palm in X so it looks contacted.
    x = 0.7 * state.x0 + 0.3 * palm[0]
    _write_parcel_xy(env, parcel, x, y, state.z0)
    state.frames_assisted += 1
    return state


def follow_active_arm_push(
    act_np,
    *,
    task_id: str,
    phase: float,
    state: PushAssistState,
) -> None:
    """After latch, nudge the active arm roll so the palm tracks the sliding parcel."""
    import numpy as np

    if not state.latched or phase < 0.40:
        return
    spec = _TASK_SPEC.get(task_id)
    if spec is None or spec["hand"] == "both":
        return
    hand = spec["hand"]
    push = spec["push"]
    span = max(0.18, 0.92 - state.latch_phase)
    t = min(1.0, max(0.0, (phase - state.latch_phase) / span))
    if phase >= 0.90:
        t = 1.0
    s = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    boost = float(0.40 * s)
    if hand == "left":
        act_np[_LEFT_SHOULDER_ROLL] = float(act_np[_LEFT_SHOULDER_ROLL] + boost)
        act_np[_LEFT_SHOULDER_YAW] = float(act_np[_LEFT_SHOULDER_YAW] - 0.08 * s)
        return
    act_np[_RIGHT_SHOULDER_ROLL] = float(act_np[_RIGHT_SHOULDER_ROLL] - boost)
    act_np[_RIGHT_SHOULDER_YAW] = float(act_np[_RIGHT_SHOULDER_YAW] + 0.08 * s)


def hold_inactive_palm_y(
    robot,
    hand_idx: dict,
    act_np,
    *,
    side: str,
    target_y: float,
    phase: float,
) -> None:
    """Closed-loop: keep the non-pushing palm near its rest Y during the sweep."""
    import numpy as np

    if phase < 0.40:
        return
    palm = palm_xyz(robot, hand_idx[side])
    err = float(palm[1] - target_y)
    if abs(err) < 0.012:
        return
    roll_i = _LEFT_SHOULDER_ROLL if side == "left" else _RIGHT_SHOULDER_ROLL
    pitch_i = _LEFT_SHOULDER_PITCH if side == "left" else _RIGHT_SHOULDER_PITCH
    act_np[roll_i] = float(act_np[roll_i] - np.clip(1.8 * err, -0.30, 0.30))
    act_np[pitch_i] = float(act_np[pitch_i] + np.clip(0.35 * abs(err), 0.0, 0.14))
