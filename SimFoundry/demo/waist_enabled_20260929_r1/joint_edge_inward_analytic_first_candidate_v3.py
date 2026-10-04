"""Uninstalled explicit analytic-first experiment. Original ftol/maxiter/gates unchanged; independent stationarity still required."""
"""ISOLATED OFFLINE PROBE, not collector-connected. Shift existing nominal edge constraint by0/0.5/1mm; retains original task/limits/forward requirement. No claim about actual relative contact.
"""
"""Unwired optional rear command refinement; no simulator or file access.

Acts only after original rear/first-load/transition protection produced a valid
joint-XY override. Constrains a frozen-offset virtual hand reference under
nominal FK, not future COP or physical dynamics. Original command is retained
on numeric/infeasible solve; every such fallback is explicit in returned trace.
"""
import numpy as np
from scipy.optimize import linprog, minimize, Bounds, nnls


def _refine_rear_command(*, enabled=False, mode=None, selected=False,
                        current=None, previous=None, parent_command=None,
                        jacobian=None, error=None, damping=None,
                        lower=None, upper=None, step_limits=None,
                        object_rotation=None, cop_local=None, core_size=None,
                        direction=None, active_rows=None, point_fn=None,
                        analytic_retry=False, point_jacobian_fn=None, parent_seed_retry=False, inward_step_m=0., analytic_first=False):
    if type(analytic_first) is not bool:raise ValueError('Explicit analytic-first flag required')
    if not np.isfinite(inward_step_m) or not 0<=inward_step_m<=.001:raise ValueError('Invalid diagnostic inward step')
    if type(enabled) is not bool or type(selected) is not bool or type(analytic_retry) is not bool:
        raise ValueError('Flags must be bool')
    if type(parent_seed_retry) is not bool:
        raise ValueError('parent_seed_retry must be bool')
    if parent_seed_retry and not analytic_retry:
        raise ValueError('Parent-seed retry requires original analytic retry')
    no=lambda reason,**extra:dict(override=False,reason=reason,**extra)
    if not enabled:return no('disabled')
    if mode!='top_push':return no('original_mode_guard')
    if not selected:return no('original_rear_not_overridden')
    if analytic_first and not callable(point_jacobian_fn):raise ValueError('Analytic-first needs actual point Jacobian')
    def vector(value,n,name):
        a=np.asarray(value,dtype=float)
        if a.shape!=(n,) or not np.isfinite(a).all():raise ValueError('Invalid '+name)
        return a.copy()
    q=vector(current,11,'current');prev=vector(previous,11,'previous');parent=vector(parent_command,11,'parent')
    lo=vector(lower,11,'lower');hi=vector(upper,11,'upper');limits=vector(step_limits,11,'step_limits');damp=vector(damping,11,'damping')
    J=np.asarray(jacobian,dtype=float);e=vector(error,9,'error');R=np.asarray(object_rotation,dtype=float);cop=vector(cop_local,3,'cop');core=vector(core_size,3,'core')
    if J.shape!=(9,11) or not np.isfinite(J).all():raise ValueError('Invalid Jacobian')
    if R.shape!=(3,3) or not np.isfinite(R).all() or not np.allclose(R.T@R,np.eye(3),atol=1e-6) or np.linalg.det(R)<.99999:raise ValueError('Invalid rotation')
    if active_rows not in ([0,1,2],[3,4,5]) or direction not in (-1,1) or type(direction) is bool:raise ValueError('Invalid side/direction')
    if direction!=(-1 if active_rows==[3,4,5] else 1):raise ValueError('Inconsistent side/direction')
    if (lo>=hi).any() or (limits<=0).any() or (damp<=0).any() or (core<=.02).any():raise ValueError('Invalid bounds/geometry')
    if not callable(point_fn):raise ValueError('Missing FK point function')
    if analytic_retry and not callable(point_jacobian_fn):raise ValueError('Missing analytic FK Jacobian')
    axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.01]
    if not axes:return no('no_threatened_core_edge')
    normals=np.asarray([-np.sign(cop[k])*R[:,k] for k in axes])
    origin=vector(point_fn(q),3,'current FK reference')
    def motion(cmd):return vector(point_fn(cmd),3,'command FK reference')-origin
    def constraints(dq):
        v=motion(q+dq)
        return np.r_[normals@v-inward_step_m,direction*v[1]]
    parent_direction=constraints(parent-q)
    trace=dict(threatened_axes=axes,parent_nominal_edge_inward_m=parent_direction[:-1].tolist(),parent_nominal_forward_m=float(parent_direction[-1]))
    # Already-valid parent commands are preserved byte-for-byte by the caller.
    if parent_direction.min()>=-1e-7:return no('parent_direction_valid',**trace)
    low=np.maximum.reduce([lo-q,-limits,prev-.055-q]);high=np.minimum.reduce([hi-q,limits,prev+.055-q])
    if (low>=high).any():return no('empty_original_bound_intersection',**trace)
    A=np.vstack([normals@J[active_rows],direction*J[active_rows][1]])
    feasible=linprog(np.zeros(11),A_ub=-A,b_ub=-np.r_[np.full(len(normals),inward_step_m),0.],bounds=list(zip(low,high)),method='highs')
    if not feasible.success:return no('linear_initialization_infeasible' if feasible.status==2 else 'linear_initialization_failed',solver_status=int(feasible.status),**trace)
    design=np.vstack([J,np.diag(damp)]);rhs=np.r_[e,np.zeros(11)];H=design.T@design;g=design.T@rhs
    fun=lambda x:5000*float(x@H@x-2*g@x)
    grad=lambda x:10000*(H@x-g)
    first_constraint={'type':'ineq','fun':constraints}
    if analytic_first:
        def first_jacobian(dq):
            jp=np.asarray(point_jacobian_fn(q+dq),dtype=float)
            if jp.shape!=(3,11) or not np.isfinite(jp).all():raise ValueError('Invalid initial analytic point Jacobian')
            return np.vstack([normals@jp,direction*jp[1]])
        first_constraint['jac']=first_jacobian
        trace['analytic_first']=dict(enabled=True,original_objective_and_constraints=True)
    solve=minimize(fun,feasible.x,jac=grad,bounds=Bounds(low,high),constraints=[first_constraint],method='SLSQP',options={'ftol':1e-11,'maxiter':300})
    if analytic_retry and solve.status==8 and np.isfinite(solve.x).all():
        initial_status=int(solve.status);initial_iterations=int(solve.nit)
        def constraint_jacobian(dq):
            jp=np.asarray(point_jacobian_fn(q+dq),dtype=float)
            if jp.shape!=(3,11) or not np.isfinite(jp).all():raise ValueError('Invalid analytic FK Jacobian')
            return np.vstack([normals@jp,direction*jp[1]])
        solve=minimize(fun,feasible.x,jac=grad,bounds=Bounds(low,high),constraints=[{'type':'ineq','fun':constraints,'jac':constraint_jacobian}],method='SLSQP',options={'ftol':1e-11,'maxiter':300})
        trace['analytic_retry']=dict(attempted=True,initial_solver_status=initial_status,initial_iterations=initial_iterations,retry_solver_status=int(solve.status),retry_iterations=int(solve.nit),initializer='original_linear_feasible_point')
    if parent_seed_retry and analytic_retry and 'analytic_retry' in trace and solve.status == 8 and np.isfinite(solve.x).all():
        prior_status = int(solve.status)
        prior_iterations = int(solve.nit)
        initial = np.clip(parent - q, low, high)
        solve = minimize(fun, initial, jac=grad, bounds=Bounds(low, high),
                         constraints=[{'type': 'ineq', 'fun': constraints, 'jac': constraint_jacobian}],
                         method='SLSQP', options={'ftol': 1e-11, 'maxiter': 300})
        trace['parent_seed_retry'] = dict(attempted=True, prior_solver_status=prior_status,
            prior_iterations=prior_iterations, initializer='bounded_parent_delta',
            retry_solver_status=int(solve.status), retry_iterations=int(solve.nit),
            maximum_extra_retries=1)
    if not solve.success or not np.isfinite(solve.x).all():return no('nonlinear_solver_failed',solver_status=int(solve.status),**trace)
    cmd=(q+solve.x).astype(np.float32);dq=cmd.astype(float)-q;actual=constraints(dq)
    if np.min(actual)<-1e-7 or np.min(dq-low)<-2e-7 or np.min(high-dq)<-2e-7:return no('final_float32_constraint_violation',**trace)
    if not np.isfinite(cmd).all():return no('nonfinite_output',**trace)
    if analytic_first:
        # Same unscaled first-order stationarity contract as the independent
        # auditor, checked on the actual emitted float32 candidate.
        derivatives=first_jacobian(dq)
        active_grad=[derivatives[i] for i in range(len(actual)) if actual[i]<=1e-6]
        for i in range(11):
            if dq[i]-low[i]<=2e-6:active_grad.append(np.eye(11)[i])
            if high[i]-dq[i]<=2e-6:active_grad.append(-np.eye(11)[i])
        objective_gradient=J.T@(J@dq-e)+damp*damp*dq
        if active_grad:
            normals_kkt=np.asarray(active_grad);length=np.linalg.norm(normals_kkt,axis=1)
            normals_kkt=normals_kkt[length>1e-12]/length[length>1e-12,None]
            _,residual=nnls(normals_kkt.T,objective_gradient,maxiter=1000)
        else:residual=float(np.linalg.norm(objective_gradient))
        trace['emitted_stationarity']=dict(residual=float(residual),threshold=1e-6,accepted=bool(residual<=1e-6),constraint_active_tolerance=1e-6,bound_active_tolerance=2e-6)
        if residual>1e-6:
            return no('final_stationarity_violation',rejected_command=cmd.tolist(),solver_status=int(solve.status),solver_iterations=int(solve.nit),solver_success=bool(solve.success),**trace)
    return dict(override=True,reason='nonlinear_joint_direction',command=cmd.tolist(),nominal_edge_inward_m=actual[:-1].tolist(),nominal_forward_m=float(actual[-1]),iterations=int(solve.nit),**trace)


def refine_rear_command(**kwargs):
    """Fixed requirement for explicitly selected right-rear diagnostic adapter."""
    if 'inward_step_m' in kwargs:raise ValueError('Diagnostic requirement is fixed')
    out=_refine_rear_command(**kwargs,inward_step_m=.0005)
    out['nominal_inward_requirement_m']=.0005
    out['physical_motion_prediction']=False
    for key,residual in [('parent_nominal_edge_inward_m','parent_edge_constraint_residual_m'),('nominal_edge_inward_m','edge_constraint_residual_m')]:
        if key in out:
            out[residual]=out[key]
            out[key]=[x+.0005 for x in out[key]]
    return out
