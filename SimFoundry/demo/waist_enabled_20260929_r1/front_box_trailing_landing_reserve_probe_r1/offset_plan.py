"""Unwired first-front landing planner using current geometry only.
A physical lowest hull vertex is centered, not the virtual support reference.
Nominal sampled paths do not certify actual tracking, contact COP or task success.
"""
import numpy as np
from scipy.optimize import minimize, Bounds
from articulated_hand_geometry import skew
from minimum_motion_recontact import interpolate


def checked_scene(scene, q):
    result = scene.check(q)
    details = scene.details(q)
    result = dict(result, inactive_lowest_z_m=float(details['inactive_z']))
    result['accepted'] = bool(result['accepted'] and result['elbow_gap_m'] >= .005-2e-7
                              and details['inactive_z'] >= .84-2e-7)
    return result


def plan(scene, current, *, step, offset_local_xy=(0.,0.), planning_xy_reserve_m=0.):
    q = np.asarray(current, float)
    if q.shape != (11,) or not np.isfinite(q).all() or type(step) is not int or step < 1:
        raise ValueError('Invalid current planning observation')
    offset=np.asarray(offset_local_xy,float)
    if offset.shape!=(2,) or not np.isfinite(offset).all() or np.linalg.norm(offset)>.0200000001 or np.any(abs(offset)>scene.core[:2]/2-.012):
        raise ValueError("Invalid bounded interior landing preference")
    if np.any(offset) and scene.side!="right":raise ValueError("Offset only for front box diagnostic")
    if not np.isfinite(planning_xy_reserve_m) or not 0.<=planning_xy_reserve_m<=.001:
        raise ValueError("Invalid planning-only XY reserve")
    tolerance=.002-float(planning_xy_reserve_m)
    guard = scene.guard
    metadata = dict(step=step, start=q.tolist(), scene=scene.record(), attempts=[],
                    scope=__doc__, training_ready=False)
    metadata["landing_preference_local_xy"]=offset.tolist()
    metadata["planning_xy_reserve_m"]=float(planning_xy_reserve_m)
    if not checked_scene(scene, q)['accepted']:
        return dict(metadata, accepted=False, reason='current_unloaded_geometry_rejected')
    axis = np.linalg.eigh(np.cov(guard.model.vertices[scene.side].T))[1][:, 0]
    normal = scene.rotation[:, 2]

    def alignment(x):
        pose, jl, jw = guard.model.fk(scene.side, x)
        vector = pose[:3, :3] @ axis
        return float(normal @ vector), normal @ (-skew(vector) @ jw)

    def objective(x):
        delta = x-q
        return float(delta @ delta), 2*delta

    def constraints(x):
        g = scene.details(x)
        p, jac = g['point'], g['jacobian']
        a, da = alignment(x)
        return (np.r_[a*a-.8**2, tolerance-(p[:2]-offset), tolerance+(p[:2]-offset),
                      p[2]-scene.core[2]/2-.006, scene.core[2]/2+.007-p[2],
                      g['inactive_z']-.84, guard.geometry.constraints(x)-.005],
                np.vstack([2*a*da, -jac[:2], jac[:2], jac[2], -jac[2],
                           g['inactive_z_jacobian'], guard.geometry.jacobian(x)]))

    seeds = [('actual_unloaded', q)] + [(f'neutral_waist_{y}', np.r_[y, np.zeros(10)])
                                      for y in [-.5, 0., .5]]
    usable = []
    for label, seed in seeds:
        fit = minimize(objective, np.clip(seed, guard.lower, guard.upper), jac=True,
                       bounds=Bounds(guard.lower, guard.upper), constraints=[
                           dict(type='ineq', fun=lambda x: constraints(x)[0],
                                jac=lambda x: constraints(x)[1]),
                           dict(type='ineq', fun=lambda x: np.array(list(scene.details(x)['gaps'].values()))-.01)],
                       method='SLSQP', options=dict(maxiter=220, ftol=1e-12))
        x = np.asarray(fit.x, float)
        finite = bool(np.isfinite(x).all())
        minimum = float(min(constraints(x)[0])) if finite else None
        endpoint_ok = bool(fit.success and finite and minimum >= -2e-7
                           and checked_scene(scene, x)['accepted']
                           and np.all(x >= guard.lower-2e-7) and np.all(x <= guard.upper+2e-7))
        path = interpolate(scene, [q, x]) if endpoint_ok else None
        if path is not None:
            path['checks'] = [checked_scene(scene, v) for v in path['waypoints']]
            path['accepted'] = bool(path['waypoints'] and all(v['accepted'] for v in path['checks']))
        attempt = dict(seed=label, status=int(fit.status), iterations=int(fit.nit),
                       endpoint_accepted=endpoint_ok, minimum_constraint_m=minimum,
                       endpoint=x.tolist() if finite else None,
                       objective=float(fit.fun) if np.isfinite(fit.fun) else None,
                       nominal_path=path)
        metadata['attempts'].append(attempt)
        if endpoint_ok and path['accepted']:
            usable.append(attempt)
    if not usable:
        return dict(metadata, accepted=False, reason='no_verified_center_endpoint_and_path')
    selected = min(usable, key=lambda v: v['objective'])
    path = selected['nominal_path']
    return dict(metadata, accepted=True, reason='center_endpoint_and_sampled_path',
                endpoint=selected['endpoint'], waypoints=path['waypoints'],
                selected_seed=selected['seed'], thin_axis_local=axis.tolist(),
                nominal_path_nodes=len(path['waypoints']),
                budget_note='Runtime remains 240 ticks; node count is not physical completion proof.')
