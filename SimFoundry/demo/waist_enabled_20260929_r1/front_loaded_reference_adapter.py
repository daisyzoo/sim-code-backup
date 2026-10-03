"""Unwired post-COP admission for a measured initial-front contact.

Apply after the parent and initial-front runtime, before any robot action.
An empty feasible set requests episode termination before issuing this action;
this adapter never fabricates a recontact, moves a parcel, or raises a bound.
The parent pressure and safety transition has already run exactly once.
"""
import numpy as np
from front_initial_loaded_reference_cap import cap_loaded_reference


def admit(*, enabled, row, state, runtime, previous_xy, normal_load_n, step):
    if type(enabled) is not bool:
        raise ValueError('Explicit enable flag required')
    if not enabled:
        return row, None
    captured = runtime is not None and runtime.center_local is not None
    capture_step = None
    if captured:
        events = [r for r in runtime.rows if r['kind'] == 'handover']
        if len(events) != 1:
            raise ValueError('A single measured initial handover is required')
        event = events[0]
        center = np.asarray(runtime.center_local, dtype=float)
        recorded = np.asarray(event['captured_center_local'], dtype=float)
        if (center.shape != (3,) or recorded.shape != (3,)
                or not np.isfinite(center).all() or not np.array_equal(center, recorded)
                or event['measured_ready_count'] < 3
                or event['context']['recontacts'] != 0
                or event['context']['guard_stop']
                or event['step'] > step):
            raise ValueError('Current reference is not bound to a past measured capture')
        capture_step = event['step']
    parent = np.asarray(row['target_xyz'], dtype=float)
    if parent.shape != (3,) or not np.isfinite(parent).all():
        raise ValueError('Invalid parent waypoint')
    # Guard/release precedence is explicit, even for an inconsistent push label.
    guarded = bool(row.get('route_stop_reason') or row.get('release_reason'))
    advice = cap_loaded_reference(
        enabled=True, capture_complete=captured,
        mode='parent_guard' if guarded else row['mode'], parent_xy=parent[:2],
        previous_xy=previous_xy, reference_xy=row.get('observed_support_xyz', [])[:2],
        surface_xy=row.get('parcel_top_xyz', [])[:2], normal_load_n=normal_load_n)
    advice = dict(advice, parent_target_xyz=parent.tolist(), capture_step=capture_step,
                  parent_guard_precedence=guarded, scope='post_COP_before_action')
    result = dict(row, loaded_reference_cap=advice)
    if advice['requires_recontact']:
        # There is no verified recovery implementation here. Stop, record failure,
        # and never send either the old parent action or a discontinuous repair.
        return result, dict(kind='stop', phase='front_loaded_reference_cap',
                            step=step, reason=advice['reason'], record=advice)
    if advice['applied']:
        if state.command is None or not np.array_equal(np.asarray(state.command), parent):
            raise ValueError('Parent command history does not match its waypoint')
        if not np.array_equal(np.asarray(state.last_emitted_xy), parent[:2]):
            raise ValueError('Parent COP history does not match its waypoint')
        command = (*advice['command_xy'], float(parent[2]))
        state.command = command
        state.last_emitted_xy = tuple(command[:2])
        result['target_xyz'] = command
    return result, None
