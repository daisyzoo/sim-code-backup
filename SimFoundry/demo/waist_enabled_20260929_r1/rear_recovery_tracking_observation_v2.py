"""Causal same-bout Cartesian tracking residual for a recovery-only hypothesis.

Uses current measured q and previous emitted command at the SAME current local
material point. No future state, force synthesis or simulator writes. Z is
reported but never used to bypass the original pressure controller.
"""
import numpy as np


def observe(*, enabled=False, guard=None, row=None, coordinate=None, current=None,
            previous=None, previous_record=None):
    if type(enabled) is not bool:
        raise ValueError('Explicit tracking option required')
    if not enabled:
        return dict(accepted=False, reason='disabled')
    if (not previous_record or previous_record.get('kind') != 'loaded_recovery' or
            previous_record.get('step') != row['step'] - 1):
        return dict(accepted=False, reason='no_previous_executed_recovery')
    commit=previous_record.get('commit')
    phase=previous_record.get('phase_committed',{})
    if (not isinstance(commit,dict) or commit.get('kind')!='committed_recovery_reference' or
            commit.get('step')!=previous_record['step'] or
            commit.get('final_guard',{}).get('accepted') is not True or
            'emitted_command' not in previous_record or phase.get('active') is not True or
            phase.get('last_step')!=previous_record['step']):
        raise ValueError('Previous recovery was not committed')
    if (row['mode'] != 'top_push' or row.get('route_stop_reason') or row.get('release_reason') or
            not row.get('rear_cop_centering', {}).get('override') or
            coordinate.get('region_joint_override') or coordinate.get('terminal_joint_hold') or
            row['recontacts'] != previous_record['parent_row']['recontacts']):
        return dict(accepted=False, reason='original_mode_contact_or_bout_guard')
    q, prev, offset = [np.asarray(x, float) for x in
                       (current, previous, row['control_offset_local'])]
    if q.shape != (11,) or prev.shape != (11,) or offset.shape != (3,) or not all(
            np.isfinite(x).all() for x in (q, prev, offset)):
        raise ValueError('Invalid measured tracking input')
    if (coordinate['step'] != row['step'] or not np.array_equal(q, coordinate['upper_q']) or
            not np.array_equal(prev, coordinate['task_inputs']['previous']) or
            not np.array_equal(prev, previous_record['emitted_command']) or
            not np.array_equal(prev, commit['final_guard']['command'])):
        raise ValueError('Tracking observation is not causal current/previous data')
    side = coordinate['active_side']
    if side != previous_record['parent_coordinate']['active_side']:
        raise ValueError('Tracking observation crossed active hands')
    def point(x):
        transform, _, _ = guard.model.fk(side, x)
        return transform[:3, 3] + transform[:3, :3] @ offset
    measured, previous_nominal = point(q), point(prev)
    if np.max(abs(measured - np.asarray(row['observed_support_xyz']))) > 2e-6:
        raise ValueError('Tracking reference differs from measured FK')
    residual = measured - previous_nominal
    # Reject a transient outside the declared model domain instead of silently
    # clipping it and pretending the clipped value was actually measured.
    accepted = bool(abs(residual[0]) <= .0015 and abs(residual[1]) <= .0005)
    return dict(accepted=accepted,
                reason='previous_actual_tracking_residual' if accepted else 'outside_tracking_domain',
                step=row['step'], previous_step=previous_record['step'], side=side,
                current_q=q.tolist(), previous_emitted_command=prev.tolist(),
                control_offset_local=offset.tolist(), measured_reference_xyz=measured.tolist(),
                previous_nominal_reference_xyz=previous_nominal.tolist(),
                observed_residual_xyz_m=residual.tolist(),
                correction_xyz_m=[float(residual[0]), float(residual[1]), 0.] if accepted else [0., 0., 0.],
                maximum_bias_xy_m=[.0015, .0005],
                scope='Causal kinematic residual; predictive validity requires new physical comparison')
