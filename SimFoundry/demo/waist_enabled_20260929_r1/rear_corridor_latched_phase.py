"""Measured rear-corridor hysteresis; pure proposal, no robot/simulator writes.

The original 20 mm entry margin remains. A triggered phase stays active until
measured clearance reaches 22 mm or the target passes the obstacle along Y.
Contact/mode guards retain priority. Commit the returned state only after the
collector accepts the actual final command. This is not a success criterion.
"""
import copy
import numpy as np

ENTRY_MARGIN_M = .020
EXIT_RESERVE_M = .002


def initial_state():
    return dict(active=False, last_step=0, entry_step=None)


def propose_phase(*, state, step, row, coordinate, target_xyz, obstacle_xyz,
                  target_rotation, obstacle_rotation, target_size, obstacle_size):
    if (set(state) != {'active', 'last_step', 'entry_step'} or
            type(state['active']) is not bool or type(state['last_step']) is not int or
            state['last_step'] < 0 or type(step) is not int or step <= state['last_step']):
        raise ValueError('Invalid or stale phase state')
    entry = state['entry_step']
    if ((state['active'] and (type(entry) is not int or not 1 <= entry <= state['last_step'])) or
            (not state['active'] and entry is not None)):
        raise ValueError('Phase has no valid triggering observation')
    if row['step'] != step or coordinate['step'] != step:
        raise ValueError('Phase requires current controller observations')
    vectors = [np.asarray(x, float) for x in
               (target_xyz, obstacle_xyz, target_size, obstacle_size)]
    if any(x.shape != (3,) or not np.isfinite(x).all() for x in vectors):
        raise ValueError('Invalid phase geometry')
    target, other, size, osize = vectors
    if min(size) <= 0 or min(osize) <= 0:
        raise ValueError('Invalid object size')
    rotations = [np.asarray(x, float) for x in (target_rotation, obstacle_rotation)]
    for rot in rotations:
        if (rot.shape != (3, 3) or not np.isfinite(rot).all() or
                not np.allclose(rot.T @ rot, np.eye(3), atol=1e-6) or
                np.linalg.det(rot) < .99999):
            raise ValueError('Invalid object rotation')
    side = coordinate['active_side']
    if side not in ('left', 'right'):
        raise ValueError('Invalid active side')
    rad, orad = [abs(rot) @ dims / 2 for rot, dims in zip(rotations, (size, osize))]
    required_x = float(other[0] + orad[0] + rad[0] + ENTRY_MARGIN_M)
    deficit = required_x - float(target[0])
    pending = bool((-1 if side == 'right' else 1) * (target[1] - other[1]) <=
                   rad[1] + orad[1] + ENTRY_MARGIN_M)
    eligible = bool(row['mode'] == 'top_push' and not row.get('route_stop_reason') and
                    not row.get('release_reason') and not coordinate.get('region_joint_override') and
                    not coordinate.get('terminal_joint_hold') and
                    row.get('rear_cop_centering', {}).get('override'))
    after = copy.deepcopy(state)
    after['last_step'] = step
    if state['active']:
        if not pending or deficit <= -EXIT_RESERVE_M:
            after.update(active=False, entry_step=None)
            reason = 'passed_obstacle' if not pending else 'measured_exit_reserve'
        else:
            reason = 'continue_recovery' if eligible else 'preserve_phase_under_original_guard'
    elif eligible and pending and deficit > 0:
        after.update(active=True, entry_step=step)
        reason = 'original_deficit_trigger'
    else:
        reason = 'no_trigger'
    return dict(step=step, before=copy.deepcopy(state), after=after, reason=reason,
                eligible=eligible, obstacle_pending=pending, original_deficit_m=deficit,
                required_target_x=required_x, original_planning_margin_m=ENTRY_MARGIN_M,
                exit_reserve_m=EXIT_RESERVE_M,
                request_recovery=bool(after['active'] and eligible),
                geometry={name:np.asarray(value, float).tolist() for name, value in zip(
                    ('target_xyz','obstacle_xyz','target_rotation','obstacle_rotation',
                     'target_size','obstacle_size'),
                    (target_xyz,obstacle_xyz,target_rotation,obstacle_rotation,target_size,obstacle_size))})
