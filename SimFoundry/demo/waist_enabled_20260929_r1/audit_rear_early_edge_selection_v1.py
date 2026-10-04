"""Independent LP audit of eligible early-edge selection and full-parent fallback.
Only called after separately verified original loaded rear COP feedback.
No production governor import; this is one component, not full episode admission.
"""
import numpy as np
from scipy.optimize import linprog

def _independent_xy(previous, command, reference, rotation, size, local, direction, margin):
    """Independent LP direction maximization; no candidate helper import."""
    delta = command - previous
    if direction * delta[1] < -1e-10:
        return dict(override=False, reason='parent_nonforward_preserved')
    axes = np.flatnonzero(size[:2] / 2 - abs(local[:2]) < margin)
    if not len(axes):
        return dict(override=False, reason='no_near_core_edge')
    low = max(previous[0] - 0.002, reference[0] - 0.03)
    high = min(previous[0] + 0.002, reference[0] + 0.03)
    if low > high:
        return dict(override=False, reason='no_cartesian_slew_and_lead_interval')
    lower, upper = ((low - previous[0]) * 1000, (high - previous[0]) * 1000)
    A = []
    b = []
    for axis in axes:
        normal = rotation[:, axis] * (1 if local[axis] >= 0 else -1)
        A.append([float(normal[0]), float(normal[1] * delta[1] * 1000)])
        b.append(float(-normal[2] * delta[2] * 1000))
    A.extend([[-1, 0], [1, 0], [0, -1], [0, 1]])
    b.extend([-lower, upper, 0, 1])
    A = np.asarray(A)
    b = np.asarray(b)
    evidence = dict(near_axes=axes.tolist(), feasible_x_interval_m=[low, high], constraints_mm=A.tolist(), rhs_mm=b.tolist())
    fit = linprog([0, -1], A_ub=A, b_ub=b, bounds=[(None, None), (None, None)], method='highs', options={'primal_feasibility_tolerance': 1e-09, 'dual_feasibility_tolerance': 1e-09})
    if not fit.success:
        assert fit.status == 2, fit.message
        return dict(override=False, reason='no_joint_XY_direction', **evidence)
    assert np.max(A @ fit.x - b) <= 1e-08
    scale = float(np.clip(fit.x[1], 0.0, 1.0))
    opts = dict(A_ub=A, b_ub=b, bounds=[(None, None), (scale, scale)], method='highs', options={'primal_feasibility_tolerance': 1e-09, 'dual_feasibility_tolerance': 1e-09})
    lf = linprog([1, 0], **opts)
    hf = linprog([-1, 0], **opts)
    assert lf.success and hf.success
    dx = float(np.clip(delta[0] * 1000, lf.x[0], hf.x[0]))
    assert np.max(A @ np.array([dx, scale]) - b) <= 1e-08
    emitted = command.copy()
    emitted[0] = previous[0] + dx / 1000
    emitted[1] = previous[1] + scale * delta[1]
    if np.max(abs(emitted - command)) < 1e-10:
        return dict(override=False, reason='original_direction_feasible', scale=scale, **evidence)
    return dict(override=True, reason='joint_XY_nonoutward_reference', command_xyz=emitted.tolist(), scale=scale, parent_delta_xyz_m=delta.tolist(), reference_delta_xyz_m=(emitted - previous).tolist(), projected_local_xy_delta_m=(rotation.T @ (emitted - previous))[:2].tolist(), **evidence)

def verify_selection(*,observed,early_enabled,side,enabled,mode,previous_xyz,parent_xyz,reference_xyz,object_rotation,core_size,cop_local,normal_load_n,direction):
    assert type(early_enabled) is bool and type(enabled) is bool
    assert enabled and mode=='top_push' and side in ('left','right')
    assert cop_local is not None and np.isfinite(normal_load_n) and normal_load_n>=.3
    assert not isinstance(direction,bool) and direction in (-1,1)
    args=[np.asarray(v,float) for v in [previous_xyz,parent_xyz,reference_xyz,object_rotation,core_size,cop_local]]
    assert [x.shape for x in args]==[(3,),(3,),(3,),(3,3),(3,),(3,)] and all(np.isfinite(x).all() for x in args)
    assert np.allclose(args[3].T@args[3],np.eye(3),atol=1e-6) and np.linalg.det(args[3])>.99999
    assert np.all(args[4][:2]>.02) and args[4][2]>0
    original=_independent_xy(*args,direction,.010)
    def compare(expected,got,path):
        if isinstance(expected,dict):
            assert isinstance(got,dict),path
            for k,v in expected.items():assert k in got,(path,k);compare(v,got[k],path+'.'+k)
        elif isinstance(expected,(str,bool)) or expected is None:assert type(got) is type(expected) and got==expected,path
        else:np.testing.assert_allclose(got,expected,atol=2e-7,rtol=0,err_msg=path)
    if not early_enabled or side=='left':
        assert 'early_edge' not in observed;compare(original,observed,'original');return dict(passed=True,candidate_selected=False)
    candidate=_independent_xy(*args,direction,.020);selected=candidate if candidate['override'] else original
    compare(selected,observed,'selected');compare(dict(version='rear_box_early20_preserve_parent10_v1',candidate_selected=bool(candidate['override']),parent_result=original,candidate_result=candidate,fallback=None if candidate['override'] else 'complete_original_joint_XY_result',warning_inset_m=.020,original_inset_m=.010,physics_verified=False),observed.get('early_edge'),'early_edge')
    return dict(passed=True,candidate_selected=bool(candidate['override']))
