"""Independent audit of a final current-contact loaded-edge override.
No candidate solver/adapter or articulated geometry imported. Reconstruct causal
force COP, original feasible bounds, independent URDF FK/elbow constraints and
unscaled damped-task stationarity. Does not certify original task-input assembly,
full episode, physical stability, images, or training admission.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls


def near(a, b, tol=1e-7):
    a, b = np.asarray(a, float), np.asarray(b, float)
    assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all(), 'shape/nonfinite'
    assert np.max(abs(a-b), initial=0) <= tol, 'value mismatch'


def verify(tr, *, row, previous_row, coordinate, current, previous_command,
           parent_command, final_command, packet, object_xyz, object_quat,
           core_size, side, selected, hand, elbows):
    assert selected is True and side in ('left', 'right')
    t = row['step']
    assert coordinate['step'] == tr['step'] == t and previous_row['step'] == t-1
    assert row['mode'] == previous_row['mode'] == 'top_push'
    assert row.get('recontacts', 0) == previous_row.get('recontacts', 0)
    assert not (row.get('route_stop_reason') or row.get('release_reason'))
    assert not coordinate.get('terminal_joint_hold') and not coordinate.get('region_joint_override')
    assert coordinate.get('controller_kind') != 'verified_unloaded_recontact_joint_path'
    assert tr['eligible'] is True and tr['accepted'] is True and tr['override'] is True
    assert tr['reason'] == 'current_contact_nominal_edge_repair'
    ctx = tr['context']
    for name, value in dict(enabled=True, selected=True, mode='top_push', previous_mode='top_push',
                            recontacts=row.get('recontacts', 0), previous_recontacts=previous_row.get('recontacts', 0),
                            parent_guard=False, terminal_hold=False, region_override=False, unloaded_override=False).items():
        assert ctx[name] == value, ('context', name)
    assert packet['after_action_step'] == ctx['packet_after_action_step'] == t-1
    key, actor = ('box', 'parcel_box') if side == 'right' else ('mailer', 'mailer')
    xyz = np.asarray(object_xyz, float)
    R = Rotation.from_quat(object_quat).as_matrix()
    near(packet['post_action_pose'][key], xyz, 1e-6)
    near(ctx['object_xyz'], xyz, 0)
    near(ctx['object_rotation'], R, 1e-7)
    near(ctx['core_size'], core_size, 0)
    points, loads = [], []
    for contact in packet['parcel_contacts']:
        slots = [i for i, name in enumerate(contact['shapes']) if '/'+actor+'/' in name]
        if len(slots) != 1 or not any(side+'_wrist' in name for name in contact['shapes']):
            continue
        force = np.asarray(contact['force_world_N'], float) * (1 if slots[0] == 1 else -1)
        load = -float(force @ R[:, 2])
        assert np.isfinite(load)
        if load > .05:
            points.append(contact['position_world']); loads.append(load)
    total = sum(loads)
    assert total >= .3, 'not currently loaded'
    near(ctx['load_n'], total, 2e-6)
    near(ctx['previous_load_n'], previous_row.get('contact_load', {}).get('observed_vertical_load_n', 0), 0)
    cop = R.T @ (np.average(points, axis=0, weights=loads) - xyz)
    near(ctx['current_cop_local'], cop, 2e-8)
    axes = [k for k in (0, 1) if core_size[k]/2-abs(cop[k]) <= .01]
    assert axes and tr['threatened_axes'] == axes
    inp = coordinate['task_inputs']
    assert coordinate['active_side'] == side and coordinate['bounded_solver'] is True
    assert coordinate['contact_normal_tracking'] is not None and coordinate['contact_bout_yaw_tracking'] is None
    assert coordinate['waist_preference_rad'] is None and coordinate['preferred_waist_step_rad'] == 0
    q, prev, x = (np.asarray(v, float) for v in (current, previous_command, final_command))
    assert q.shape == prev.shape == x.shape == (11,)
    near(q, coordinate['upper_q'], 1e-7); near(q, inp['current'], 1e-6)
    near(prev, inp['previous'], 0)
    near(tr['parent_upper_command'], parent_command, 0)
    near(tr['final_upper_command'], x, 0); near(tr['command'], x, 0)
    near(x.astype(np.float32).astype(float), x, 0)
    lower = np.maximum.reduce([np.array(inp['lower']), q-np.array(inp['step_limits']), prev-.055])
    upper = np.minimum.reduce([np.array(inp['upper']), q+np.array(inp['step_limits']), prev+.055])
    near(tr['bound_low'], lower, 1e-7); near(tr['bound_high'], upper, 1e-7)
    assert np.all(lower < upper) and min(x-lower) >= -2e-7 and min(upper-x) >= -2e-7
    offset = np.asarray(row['control_offset_local'], float)
    def point(z):
        T = hand.fk(z, side)
        return T[:3, 3] + T[:3, :3] @ offset
    origin = point(q)
    near(origin, row['observed_support_xyz'], 2e-6)
    near(origin, coordinate['control_point_positions'][side], 2e-6)
    near(origin, tr['measured_reference'], 2e-6)
    direction = -1 if side == 'right' else 1
    A = np.vstack([[-np.sign(cop[k])*R[:, k] for k in axes], [0, direction, 0]])
    def constraints(z):
        return np.r_[A @ (point(z)-origin), elbows.gap(z)-.005]
    values = constraints(x)
    assert min(values[:len(A)]) >= -1e-7 and min(values[len(A):]) >= -2e-7
    parent_values = constraints(np.asarray(parent_command, float))
    parent = np.asarray(parent_command, float)
    assert (min(parent_values[:len(A)]) < -1e-7 or min(parent_values[len(A):]) < -2e-7
            or min(parent-lower) < -2e-7 or min(upper-parent) < -2e-7), 'unnecessary override'
    # Same original unscaled task gradient and 1e-6 stationarity threshold.
    J, error, damping = (np.asarray(inp[k], float) for k in ('jacobian', 'error', 'damping'))
    assert J.shape == (9, 11) and error.shape == (9,) and damping.shape == (11,)
    assert np.isfinite(J).all() and np.isfinite(error).all() and np.isfinite(damping).all()
    gradient = J.T @ (J @ (x-q)-error) + damping*damping*(x-q)
    h, I = 1e-5, np.eye(11)
    G = np.column_stack([(constraints(x+I[i]*h)-constraints(x-I[i]*h))/(2*h) for i in range(11)])
    normals = [G[i] for i in range(len(values)) if values[i] <= 1e-6]
    for i in range(11):
        if x[i]-lower[i] <= 2e-6: normals.append(I[i])
        if upper[i]-x[i] <= 2e-6: normals.append(-I[i])
    if normals:
        B = np.array(normals); norms = np.linalg.norm(B, axis=1); B = B[norms > 1e-12]/norms[norms > 1e-12, None]
        _, residual = nnls(B.T, gradient, maxiter=1000)
    else:
        residual = np.linalg.norm(gradient)
    return dict(step=t, stationarity_residual=float(residual), current_normal_load_n=total,
                cop_local=cop.tolist(), nominal_inward_and_forward_m=values[:len(A)].tolist(),
                min_elbow_gap_m=float(min(values[len(A):])+.005), passed=bool(residual <= 1e-6))
