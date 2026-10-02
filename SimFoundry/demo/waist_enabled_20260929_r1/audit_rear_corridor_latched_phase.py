"""Independent measured phase reconstruction, without importing the controller.

Call once in executed-action order, with geometry read from native observations
and the independently checked parent control record. Does not certify commands,
pressure, contact, or task success; those audits remain separately mandatory.
"""
import copy
import numpy as np


class PhaseVerifier:
    def __init__(self):
        self.state = dict(active=False, last_step=0, entry_step=None)

    def verify(self, record, *, row, coordinate, geometry, side, executed=True):
        t = record['step']
        assert type(t) is int and t == self.state['last_step'] + 1
        assert t == row['step'] == coordinate['step']
        assert side in ('left', 'right') and coordinate.get('active_side', side) == side
        assert type(executed) is bool
        phase = record['phase']
        assert phase['step'] == t and phase['before'] == self.state
        names = ('target_xyz', 'obstacle_xyz', 'target_rotation', 'obstacle_rotation',
                 'target_size', 'obstacle_size')
        assert set(phase['geometry']) == set(names)
        g = {name:np.asarray(geometry[name], float) for name in names}
        for name, value in g.items():
            assert np.isfinite(value).all()
            assert np.allclose(value, np.asarray(phase['geometry'][name], float), atol=2e-7, rtol=0), name
        for name in ('target_xyz', 'obstacle_xyz', 'target_size', 'obstacle_size'):
            assert g[name].shape == (3,)
        assert min(g['target_size']) > 0 and min(g['obstacle_size']) > 0
        for name in ('target_rotation', 'obstacle_rotation'):
            rot = g[name]
            assert rot.shape == (3, 3) and np.allclose(rot.T @ rot, np.eye(3), atol=1e-6)
            assert np.linalg.det(rot) >= .99999
        # Direct per-axis projection, independently reconstructed from observations.
        radii = []
        for which in ('target', 'obstacle'):
            radii.append([sum(abs(g[which+'_rotation'][axis,j]) * g[which+'_size'][j]
                              for j in range(3)) / 2 for axis in range(3)])
        target, other = g['target_xyz'], g['obstacle_xyz']
        required = float(other[0] + radii[1][0] + radii[0][0] + .020)
        deficit = required - float(target[0])
        pending = bool((-1 if side == 'right' else 1) * (target[1]-other[1]) <=
                       radii[0][1] + radii[1][1] + .020)
        eligible = bool(row['mode'] == 'top_push' and
                        not any((row.get('route_stop_reason'), row.get('release_reason'),
                                 coordinate.get('region_joint_override'),
                                 coordinate.get('terminal_joint_hold'))) and
                        row.get('rear_cop_centering', {}).get('override'))
        if self.state['active']:
            active = pending and deficit > -.002
            reason = ('continue_recovery' if eligible else 'preserve_phase_under_original_guard') if active else (
                'passed_obstacle' if not pending else 'measured_exit_reserve')
        else:
            active = eligible and pending and deficit > 0.
            reason = 'original_deficit_trigger' if active else 'no_trigger'
        expected = dict(active=bool(active), last_step=t,
                        entry_step=(self.state['entry_step'] if self.state['active'] else t) if active else None)
        assert type(phase['after']['active']) is bool and phase['after'] == expected
        assert phase['reason'] == reason
        assert phase['eligible'] is eligible and phase['obstacle_pending'] is pending
        assert phase['request_recovery'] is bool(active and eligible)
        assert phase['original_planning_margin_m'] == .020 and phase['exit_reserve_m'] == .002
        assert abs(phase['required_target_x'] - required) < 1e-12
        assert abs(phase['original_deficit_m'] - deficit) < 1e-12
        if executed:
            assert record['kind'] != 'stop' and record['phase_committed'] == expected
            if active and eligible:
                assert record['kind'] in ('loaded_recovery', 'unload')
            else:
                assert record['kind'] == 'unchanged'
            self.state = copy.deepcopy(expected)
        else:
            assert 'phase_committed' not in record
        return dict(passed=True, step=t, active=bool(active), reason=reason,
                    original_deficit_m=deficit, executed=executed, training_ready=False)
