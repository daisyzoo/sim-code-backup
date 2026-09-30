"""Cartesian palm-path expert for physics-only sorting collection.

The 23-DoF G1 has five joints per arm and no wrist pitch/yaw.  A shoulder-roll
schedule therefore lifts the palm while it moves laterally.  This expert uses
the simulator's geometric Jacobian to keep the palm at a fixed X/Z while
it sweeps in Y.  The Cartesian path is frozen from the initial parcel pose;
only the joint-space servo is closed loop.  Recorded demonstrations still
contain ordinary absolute joint targets and can be replayed open loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from isaaclab.utils.math import quat_apply

from simfoundry.calibration.sorting_station import TABLE_TOP_Z
from simfoundry.data.sorting_quality import PALM_OFFSET
from simfoundry.embodiment import G1_23DOF_JOINT_NAMES


_ARM_ACTION_INDICES = {
    "left": tuple(range(13, 18)),
    "right": tuple(range(18, 23)),
}
_ARM_JOINT_NAMES = {
    "left": (
        "left_shoulder_pitch_joint",
        "left_shoulder_roll_joint",
        "left_shoulder_yaw_joint",
        "left_elbow_joint",
        "left_wrist_roll_joint",
    ),
    "right": (
        "right_shoulder_pitch_joint",
        "right_shoulder_roll_joint",
        "right_shoulder_yaw_joint",
        "right_elbow_joint",
        "right_wrist_roll_joint",
    ),
}

# The official U1 rubber-hand collision mesh is about 9.8 cm thick around the
# tracked black-palm centroid (half-height ~= 4.9 cm).  A centre target of
# table+7 cm drove its underside roughly 2.4 cm into the 4.5 cm box before the
# lateral sweep, ejecting boxes toward the table front.  A no-overlap target
# at +9.5 cm then lost sustained lateral contact, so retain about 1 cm of
# compliant overlap instead of reusing the old cube-proxy height.
CONTACT_PALM_Z = TABLE_TOP_Z + 0.095
# Lift before crossing the parcel. The former diagonal approach stayed only
# about 4 cm above the parcel and could brush it in the wrong direction.
STAGING_PALM_Z = TABLE_TOP_Z + 0.250
# Press the centre from above; the quality gate rejects any rare tilted-pad
# friction response that initially moves the parcel the wrong way.
# With the official wrist+rubber-hand convex hull, top-down pressing produces
# a fore/aft impulse from the wedge-shaped hull.  Stage the palm on the torso
# side of the package, then let its outer edge establish contact during the
# lateral sweep.  The sign is mirrored by ``direction`` below.
# Keep enough lateral clearance for the full official convex hull (not just
# its visual black-palm width) while descending; contact should begin only
# during the commanded outward sweep.
# With the non-crossing opposite arm, approach already starts behind the
# parcel. Establish side contact 3 cm earlier so the reachable sweep delivers
# the extra travel that the 0.13 m staging offset lacked.
CONTACT_SIDE_OFFSET = -0.13
# With the non-crossing arm there is no need to reach beyond the parcel first.
# Stay 2 cm torso-side to trade excess X reach for lateral workspace while the
# 16.5 cm-long rubber hand still overlaps the parcel in X.
CONTACT_X_BIAS = 0.040
# The non-crossing opposite arm currently achieves only ~0.20 m for a 0.30 m
# request, leaving the parcel 2--4 cm short.  Request farther outside while
# remaining well inside the 0.75 m tabletop half-width.
EXIT_Y = 0.300
LIFT_END = 16
APPROACH_END = 36
PRESS_END = 48
SWEEP_END = 104


@dataclass
class CartesianSweepState:
    side: str
    parcel_x: float
    parcel_y: float
    push_direction: float | None = None
    start_palm: tuple[float, float, float] | None = None
    joint_ids: tuple[int, ...] | None = None
    jacobian_body_idx: int | None = None
    mode: str = "lift"
    mode_step: int = 0
    exit_y: float = EXIT_Y
    front_reposition_distance: float = 0.0
    front_reposition_measured_start: bool = False
    front_reposition_start_x: float | None = None
    front_reposition_hold_yz: bool = False
    front_reposition_start_yz: tuple | None = None
    contact_x_bias: float = CONTACT_X_BIAS
    contact_palm_z: float = CONTACT_PALM_Z
    staging_palm_z: float = STAGING_PALM_Z
    contact_side_offset: float = CONTACT_SIDE_OFFSET
    goal_release: bool = False
    release_start_palm: tuple[float, float, float] | None = None
    far_sweep_retreat_m: float = 0.0
    contact_confirmed_sweep: bool = False
    engaged_sweep_start: tuple[float, float, float] | None = None
    object_feedback_lead: float = 0.0
    feedback_target_y: float | None = None
    feedback_hold_y: float | None = None
    last_target_xyz: tuple[float, float, float] | None = None
    finger_heading_weight: float = 0.0
    bounded_servo_memory: bool = False
    last_joint_target: tuple[float, ...] | None = None
    # Opt-in diagnostic: wait for three measured low-palm frames.
    settled_contact: bool = False
    contact_settle_count: int = 0
    # Diagnostic only: pause sweep clock until physical palm height recovers.
    recover_contact_height: bool = False
    sweep_height_paused: bool = False
    sweep_height_settle_count: int = 0
    sweep_pause_frames: int = 0


def _smooth01(value: float) -> float:
    value = min(1.0, max(0.0, float(value)))
    return value * value * (3.0 - 2.0 * value)


def cartesian_target(
    state: CartesianSweepState,
    step: int,
) -> tuple[float, float, float]:
    """Return the frozen approach -> press -> lateral-sweep palm path."""
    if state.start_palm is None:
        raise ValueError("start_palm must be initialized before requesting a target")
    direction = state.push_direction
    if direction is None:
        direction = -1.0 if state.side == "right" else 1.0
    contact_y = state.parcel_y + direction * state.contact_side_offset
    exit_y = direction * state.exit_y
    target_x = state.parcel_x + state.contact_x_bias
    lifted = (state.start_palm[0], state.start_palm[1], state.staging_palm_z)
    staging = (target_x, contact_y, state.staging_palm_z)
    contact = (target_x, contact_y, state.contact_palm_z)
    exit_pose = (target_x, exit_y, state.contact_palm_z)

    if step < LIFT_END:
        s = _smooth01(step / max(LIFT_END - 1, 1))
        return tuple(float(a + (b - a) * s) for a, b in zip(state.start_palm, lifted))
    if step < APPROACH_END:
        s = _smooth01((step - LIFT_END) / max(APPROACH_END - LIFT_END - 1, 1))
        return tuple(float(a + (b - a) * s) for a, b in zip(lifted, staging))
    if step < PRESS_END:
        s = _smooth01((step - APPROACH_END) / max(PRESS_END - APPROACH_END - 1, 1))
        return tuple(float(a + (b - a) * s) for a, b in zip(staging, contact))
    if step < SWEEP_END:
        s = _smooth01((step - PRESS_END) / max(SWEEP_END - PRESS_END - 1, 1))
        return tuple(float(a + (b - a) * s) for a, b in zip(contact, exit_pose))
    return exit_pose


def damped_position_step(
    jacobian: torch.Tensor,
    error: torch.Tensor,
    *,
    damping: float = 0.045,
    max_joint_step: float = 0.055,
) -> torch.Tensor:
    """Damped-least-squares joint increment for a 3-D position error."""
    if jacobian.shape != (3, 5):
        raise ValueError(f"expected position Jacobian (3, 5), got {tuple(jacobian.shape)}")
    if error.shape != (3,):
        raise ValueError(f"expected error (3,), got {tuple(error.shape)}")
    eye = torch.eye(3, dtype=jacobian.dtype, device=jacobian.device)
    dq = jacobian.T @ torch.linalg.solve(jacobian @ jacobian.T + damping**2 * eye, error)
    return torch.clamp(dq, -max_joint_step, max_joint_step)


def finger_heading_row(axis: torch.Tensor) -> torch.Tensor:
    """Derivative of atan2(a_y, a_x) with respect to world angular velocity."""
    denom = torch.clamp(axis[0] ** 2 + axis[1] ** 2, min=1e-6)
    return torch.stack((-axis[2] * axis[0] / denom,
                        -axis[2] * axis[1] / denom, axis.new_ones(())))


def heading_position_step(jac_pos, jac_angular, error, axis, weight):
    # Soft one-axis orientation constraint; no attempt to command a full 6D
    # pose on a five-DoF arm. Skip near-vertical fingers where yaw is singular.
    if float(axis[0] ** 2 + axis[1] ** 2) < .04:
        return damped_position_step(jac_pos, error)
    yaw = torch.atan2(axis[1], axis[0])
    jac_yaw = finger_heading_row(axis) @ jac_angular
    jac = torch.cat((jac_pos, weight * jac_yaw.unsqueeze(0)), dim=0)
    rhs = torch.cat((error, (weight * torch.clamp(-.72 * yaw, -.15, .15)).reshape(1)))
    eye = torch.eye(4, dtype=jac.dtype, device=jac.device)
    dq = jac.T @ torch.linalg.solve(jac @ jac.T + .045**2 * eye, rhs)
    return torch.clamp(dq, -.055, .055)


def object_feedback_target_y(state, observed_y, direction, contact_y):
    if observed_y is None or not np.isfinite(observed_y):
        raise ValueError("Object feedback requires finite current physical parcel Y")
    if state.feedback_target_y is None:
        state.feedback_target_y = contact_y
    goal = observed_y + direction * state.object_feedback_lead
    goal = float(np.clip(goal, -state.exit_y, state.exit_y))
    # At most6mm/control frame, smoothly introduced over12frames. Follow the
    # moving object instead of advancing a timer regardless of physical contact.
    limit = .006 * _smooth01(state.mode_step / 12.)
    state.feedback_target_y += float(np.clip(goal - state.feedback_target_y, -limit, limit))
    return state.feedback_target_y


def _resolve_kinematics(robot, hand_idx: int, state: CartesianSweepState) -> None:
    if state.joint_ids is None:
        ids = []
        for name in _ARM_JOINT_NAMES[state.side]:
            try:
                ids.append(robot.joint_names.index(name))
            except ValueError as exc:
                raise RuntimeError(f"missing {state.side} arm joint {name!r}") from exc
        state.joint_ids = tuple(ids)
    if state.jacobian_body_idx is None:
        state.jacobian_body_idx = hand_idx - 1 if robot.is_fixed_base else hand_idx


def cartesian_sweep_palm(
    robot,
    hand_idx: dict,
    act_np: np.ndarray,
    *,
    state: CartesianSweepState,
    step: int,
    default_q: np.ndarray,
    observed_parcel_y: float | None = None,
) -> CartesianSweepState:
    """Write one five-joint arm target into a 23-D default-relative action."""
    side = state.side
    if (state.object_feedback_lead or state.goal_release) and (observed_parcel_y is None or not np.isfinite(observed_parcel_y)):
        raise ValueError("Object feedback requires finite current parcel position")
    body_idx = hand_idx[side]
    _resolve_kinematics(robot, body_idx, state)
    assert state.joint_ids is not None
    assert state.jacobian_body_idx is not None

    body_pos = robot.data.body_pos_w.torch[0, body_idx]
    body_quat = robot.data.body_quat_w.torch[0, body_idx]
    local_offset = torch.tensor(PALM_OFFSET, dtype=body_pos.dtype, device=body_pos.device)
    offset_w = quat_apply(body_quat.unsqueeze(0), local_offset.unsqueeze(0))[0]
    palm = body_pos + offset_w
    if state.start_palm is None:
        state.start_palm = tuple(float(v) for v in palm)

    if state.front_reposition_distance:
        from simfoundry.data.sorting_reposition import front_reposition_target
        target_xyz = front_reposition_target(state, palm)
    else:
        direction = state.push_direction
        if direction is None:
            direction = -1.0 if side == "right" else 1.0
        target_x = state.parcel_x + state.contact_x_bias
        contact_y = state.parcel_y + direction * state.contact_side_offset
        lifted = (state.start_palm[0], state.start_palm[1], state.staging_palm_z)
        staging = (target_x, contact_y, state.staging_palm_z)
        contact = (target_x, contact_y, state.contact_palm_z)
        exit_pose = (target_x, direction * state.exit_y, state.contact_palm_z)

        if state.goal_release and state.mode in ('sweep', 'engaged_sweep', 'hold'):
            from simfoundry.data.reach_sweep import ready_to_release
            if ready_to_release(state.parcel_y, observed_parcel_y, direction):
                state.release_start_palm = tuple(float(v) for v in palm)
                state.mode, state.mode_step = 'goal_release', 0

        # Advance on measured palm pose, never merely because a wall-clock step
        # elapsed. This prevents the arm from descending while it still trails on
        # the wrong side of a centre-start package.
        if state.mode == "lift" and float(palm[2]) >= state.staging_palm_z - 0.025:
            state.mode, state.mode_step = "cross", 0
        elif state.mode == "cross":
            close_xy = abs(float(palm[0]) - target_x) < 0.060 and abs(float(palm[1]) - contact_y) < 0.050
            high = float(palm[2]) >= state.staging_palm_z - 0.025
            if close_xy and high:
                state.mode, state.mode_step = "press", 0
        elif state.mode == "press":
            # The five-DoF arm gives up some X reach while descending. Preserve the
            # forward-biased collision-safe approach, but allow the sweep once the
            # palm is low and laterally centred over the package.
            centered = abs(float(palm[0]) - target_x) < 0.110 and abs(float(palm[1]) - contact_y) < 0.035
            down = float(palm[2]) <= max(state.contact_palm_z + 0.020, TABLE_TOP_Z + 0.135)
            if state.settled_contact:
                down = float(palm[2]) <= state.contact_palm_z + 0.006
                state.contact_settle_count = state.contact_settle_count + 1 if centered and down else 0
                ready = state.contact_settle_count >= 3
            else:
                ready = centered and down
            if ready:
                state.mode, state.mode_step = "sweep", 0
        elif state.mode == "sweep":
            if state.object_feedback_lead:
                if observed_parcel_y is None or not np.isfinite(observed_parcel_y):
                    raise ValueError("Missing physical object feedback")
                reached = direction * observed_parcel_y >= max(.23, direction * state.parcel_y + .18)
                if reached:
                    state.feedback_hold_y = float(palm[1])
                    state.mode, state.mode_step = "hold", 0
                elif (state.contact_confirmed_sweep
                        and direction * (observed_parcel_y - state.parcel_y) >= .015
                        and abs(float(palm[1]) - observed_parcel_y) < .08
                        and float(palm[2]) <= state.contact_palm_z + .006):
                    # Actual parcel motion confirms force transfer before the main
                    # sweep. Start from measured palm pose, not a stale waypoint.
                    state.engaged_sweep_start = tuple(float(v) for v in palm)
                    state.mode, state.mode_step = "engaged_sweep", 0
            elif state.mode_step >= 58:
                state.mode, state.mode_step = "hold", 0

        elif state.mode == "engaged_sweep":
            reached = direction * observed_parcel_y >= max(.23, direction * state.parcel_y + .18)
            if reached:
                state.feedback_hold_y = float(palm[1])
                state.mode, state.mode_step = "hold", 0
            elif state.mode_step >= 58:
                state.mode, state.mode_step = "hold", 0

        if state.recover_contact_height and state.mode == "sweep":
            if float(palm[2]) > state.contact_palm_z + 0.010:
                state.sweep_height_paused = True
                state.sweep_height_settle_count = 0
            if state.sweep_height_paused:
                if float(palm[2]) <= state.contact_palm_z + 0.006:
                    state.sweep_height_settle_count += 1
                else:
                    state.sweep_height_settle_count = 0
                if state.sweep_height_settle_count >= 3:
                    state.sweep_height_paused = False
                    state.sweep_height_settle_count = 0
                else:
                    state.sweep_pause_frames += 1

        if state.mode == "lift":
            target_xyz = lifted
        elif state.mode == 'goal_release':
            assert state.release_start_palm is not None
            target_xyz = (*state.release_start_palm[:2], max(state.staging_palm_z, state.release_start_palm[2]))
        elif state.mode == "cross":
            target_xyz = staging
        elif state.mode == "press":
            target_xyz = contact
        elif state.mode == "sweep":
            if state.object_feedback_lead:
                y = object_feedback_target_y(state, observed_parcel_y, direction, contact_y)
                target_xyz = (target_x, y, state.contact_palm_z)
            else:
                s = _smooth01(state.mode_step / 57.0)
                target_xyz = tuple(float(a + (b - a) * s) for a, b in zip(contact, exit_pose))
        elif state.mode == "engaged_sweep":
            assert state.engaged_sweep_start is not None
            s = _smooth01(state.mode_step / 57.0)
            target_xyz = tuple(float(a + (b - a) * s) for a, b in zip(state.engaged_sweep_start, exit_pose))
        else:
            target_xyz = (target_x, state.feedback_hold_y, state.contact_palm_z) if state.feedback_hold_y is not None else exit_pose
        if state.far_sweep_retreat_m and state.mode in ('sweep', 'engaged_sweep', 'hold'):
            from simfoundry.data.reach_sweep import retreating_sweep_x
            target_xyz = (retreating_sweep_x(target_x, target_xyz[1], direction, state.exit_y, state.far_sweep_retreat_m), target_xyz[1], target_xyz[2])
        state.last_target_xyz = tuple(float(v) for v in target_xyz)
        if not (state.recover_contact_height and state.mode == "sweep" and state.sweep_height_paused):
            state.mode_step += 1

    target = torch.tensor(target_xyz, dtype=palm.dtype, device=palm.device)
    # Limit Cartesian feedback so contacts do not produce a large one-frame jump.
    error = torch.clamp(0.72 * (target - palm), -0.035, 0.035)

    jacobi_cols = [j + robot.num_base_dofs for j in state.joint_ids]
    jac = robot.data.body_link_jacobian_w.torch[
        0, state.jacobian_body_idx, :, jacobi_cols
    ]
    # Shift the translational Jacobian from link origin to the palm-pad centre:
    # v_palm = v_link + omega x r = v_link - skew(r) omega.
    skew = torch.stack(
        (
            torch.stack((offset_w.new_zeros(()), -offset_w[2], offset_w[1])),
            torch.stack((offset_w[2], offset_w.new_zeros(()), -offset_w[0])),
            torch.stack((-offset_w[1], offset_w[0], offset_w.new_zeros(()))),
        )
    )
    jac_pos = jac[:3] - skew @ jac[3:]
    dq = damped_position_step(jac_pos, error)
    if state.finger_heading_weight and state.mode != "lift":
        axis = quat_apply(body_quat.unsqueeze(0), palm.new_tensor([[1., 0., 0.]]))[0]
        dq = heading_position_step(jac_pos, jac[3:], error, axis, state.finger_heading_weight)
    current_q = robot.data.joint_pos.torch[0, list(state.joint_ids)]
    q_target = current_q + dq
    if state.bounded_servo_memory:
        # Accumulate requested increments to overcome steady tracking bias, but
        # cap target lead relative to measured q. Collector still limits joint
        # range and command slew; no force or state is directly modified.
        previous_target = (current_q if state.last_joint_target is None else
                           current_q.new_tensor(state.last_joint_target))
        q_target = current_q + torch.clamp(previous_target + dq - current_q, -.10, .10)
        state.last_joint_target = tuple(float(v) for v in q_target.detach())

    action_ids = _ARM_ACTION_INDICES[side]
    for action_i, value in zip(action_ids, q_target):
        act_np[action_i] = float(value) - float(default_q[action_i])
    # Park the inactive hand outward before the active hand crosses the
    # centreline. This preserves the proven long push while preventing the
    # two rendered arms from intersecting in the demonstration.
    inactive = "left" if side == "right" else "right"
    act_np[list(_ARM_ACTION_INDICES[inactive])] = 0.0
    inactive_roll_i = _ARM_ACTION_INDICES[inactive][1]
    act_np[inactive_roll_i] = 0.30 if inactive == "left" else -0.30
    act_np[G1_23DOF_JOINT_NAMES.index("torso_joint")] = 0.0
    return state
