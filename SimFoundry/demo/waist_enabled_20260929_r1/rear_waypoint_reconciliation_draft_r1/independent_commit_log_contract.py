"""Verify complete post-action event coverage before independent state replay.
This checks logging and applied-event mathematics, not continuous modified
physics. Full source, collision, trajectory and next-state audits remain required.
"""
import numpy as np
from independent_post_commit_audit import verify


def verify_complete_log(context, log, metadata, task, *, frames):
    assert type(frames) is int and frames > 0
    assert task in ('push_box_to_bin', 'nudge_mailer_to_bin', 'wait_no_package')
    assert metadata.get('rear_waypoint_reconciliation') is True
    assert log.get('training_ready') is False
    rows = log['rows']
    assert isinstance(rows, list)
    assert len(context['q']) == len(context['u']) == frames
    assert np.isfinite(context['q']).all() and np.isfinite(context['u']).all()
    assert np.max(np.abs(context['q'][0])) < 1e-4
    assert np.max(np.abs(context['u'][0])) < 1e-4
    # The collector logs only after an executed action's post guard accepts.
    # A failed pre/final guard produces no post row; a failed post produces no
    # commit event. Partial episodes remain failures under the original gates.
    expected = []
    for step, post in context['pg'].items():
        assert type(step) is int and 0 <= step < frames
        assert post['step'] == step and post['phase'] == 'post'
        assert type(post['accepted']) is bool
        final = context['fg'][step]
        assert final['step'] == step and final['phase'] == 'final_command'
        assert final['accepted'] is True
        assert np.array_equal(np.asarray(final['command']), context['u'][step])
        if post['accepted']:
            expected.append(step)
    assert expected == sorted(set(expected))
    steps = [row['step'] for row in rows]
    assert all(type(step) is int for step in steps)
    assert steps == expected, 'missing, duplicated, reordered or unexecuted event'
    for row in rows:
        assert type(row['applied']) is bool
        assert row['version'] == 'rear_box_post_commit_adapter_draft_v1'
        assert row['current_action_changed'] is False
        assert row['training_ready'] is False
        assert isinstance(row['reason'], str) and row['reason']
        if row['step'] == 0:
            assert row['applied'] is False
            assert row['reason'] == 'first_zero_frame_preserved'
    applied = [row for row in rows if row['applied']]
    count = metadata['rear_waypoint_reconciliation_applied_frames']
    assert type(count) is int and count == len(applied)
    fr = context.get('fr')
    rear = bool(fr and fr['plan'].get('rear_cop_centering', {}).get('enabled'))
    selected = task == 'push_box_to_bin' and rear
    if task != 'wait_no_package':
        declaration = fr['plan']['rear_waypoint_reconciliation']
        assert declaration == dict(requested=True, enabled=selected,
            post_successful_action_only=True, post_guard_required=True,
            changes='next_state_command_y_and_last_waypoint_y_only',
            current_action_unchanged=True, default_off=True, training_ready=False)
    if selected:
        result = verify(context, applied)
    else:
        assert not applied, 'state update outside rear box branch'
        assert all(row['reason'] == 'not_rear_box' for row in rows if row['step'] > 0)
        result = dict(passed=True, applied_events=0, records=[],
                      verified_post_commit={}, training_ready=False)
    return dict(passed=True, executed_accepted_post_actions=len(expected),
                complete_event_rows=len(rows), selected=selected,
                independently_verified_events=result,
                continuous_state_replay_required=True, training_ready=False)
