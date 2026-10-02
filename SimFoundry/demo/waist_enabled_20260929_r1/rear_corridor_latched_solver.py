"""Default-off isolated loaded rear-corridor recovery command solver.
No simulator writes. Solves a +X reference step from current measured FK while
holding nominal Y, with original load-mode priority, joint/slew, bilateral elbow
and near-core-edge constraints. Failure returns no command and requests a separate
verified recontact; callers must never emit an unverified side-push fallback.
Nominal FK is not a physical object-motion prediction. Not collector-connected.
"""
import numpy as np
from scipy.optimize import minimize, Bounds


def solve(*, enabled=False, guard=None, row=None, coordinate=None, current=None,
          previous=None, parent_command=None, target_xyz=None, obstacle_xyz=None,
          target_rotation=None, obstacle_rotation=None, target_size=None,
          obstacle_size=None, core_size=None, recovery_active=False):
    def vector(v,n,name):
        a=np.asarray(v,dtype=float)
        if a.shape!=(n,) or not np.isfinite(a).all():raise ValueError('Invalid '+name)
        return a.copy()
    parent=vector(parent_command,11,'parent command')
    if type(enabled) is not bool:raise ValueError('enabled must be bool')
    if not enabled:return parent,dict(applied=False,reason='disabled')
    if type(recovery_active) is not bool:raise ValueError('recovery_active must be bool')
    if row['mode']!='top_push' or row.get('route_stop_reason') or row.get('release_reason') or coordinate.get('region_joint_override') or coordinate.get('terminal_joint_hold'):
        return parent,dict(applied=False,reason='original_mode_guard')
    if not row.get('rear_cop_centering',{}).get('override'):
        return parent,dict(applied=False,reason='original_contact_or_first_load_guard')
    q=vector(current,11,'current');prev=vector(previous,11,'previous');target=vector(target_xyz,3,'target');other=vector(obstacle_xyz,3,'obstacle');size=vector(target_size,3,'target size');osize=vector(obstacle_size,3,'obstacle size');core=vector(core_size,3,'core')
    if (size<=0).any() or (osize<=0).any() or (core<=.02).any():raise ValueError('Invalid geometry size')
    R,OR=(np.asarray(v,float) for v in [target_rotation,obstacle_rotation])
    for rot in [R,OR]:
        if rot.shape!=(3,3) or not np.isfinite(rot).all() or not np.allclose(rot.T@rot,np.eye(3),atol=1e-6) or np.linalg.det(rot)<.99999:raise ValueError('Invalid rotation')
    side=coordinate['active_side']
    if side not in ['left','right']:raise ValueError('Invalid side')
    direction=-1 if side=='right' else 1;rad=abs(R)@size/2;orad=abs(OR)@osize/2
    needed=other[0]+orad[0]+rad[0]+.020;deficit=needed-target[0]
    # Up to1mm extra recovery reserve avoids falsely forbidding the unchanged
    # right-hand0.5mm inward edge requirement when corridor deficit is smaller.
    exit_reserve=.002 if recovery_active else 0.
    effective_deficit=deficit+exit_reserve
    requested=min(.002,max(.001,float(effective_deficit)))
    pending=direction*(target[1]-other[1])<=rad[1]+orad[1]+.020
    if not pending or effective_deficit<=0:return parent,dict(applied=False,reason='no_rear_corridor_deficit')
    base=dict(applied=False,requires_recontact=True,rear_deficit_m=float(deficit),required_target_x=float(needed),original_planning_margin_m=.020,recovery_active=recovery_active,exit_reserve_m=exit_reserve,effective_deficit_m=float(effective_deficit))
    table=min(target[0]-rad[0]-.28,.88-target[0]-rad[0],target[1]-rad[1]+.75,.75-target[1]-rad[1])
    if table<.005 or max(needed+exit_reserve,target[0]+requested)+rad[0]>.875:return None,dict(base,reason='table_route_infeasible')
    inp=coordinate['task_inputs'];J=np.asarray(inp['jacobian'],float);e=vector(inp['error'],9,'task error');d=vector(inp['damping'],11,'damping')
    if J.shape!=(9,11) or not np.isfinite(J).all() or (d<=0).any():raise ValueError('Invalid task matrix')
    if not np.array_equal(q,np.asarray(coordinate['upper_q'],float)) or not np.array_equal(q,np.asarray(inp['current'],float)) or not np.array_equal(prev,np.asarray(inp['previous'],float)):raise ValueError('Causal current/previous mismatch')
    if np.any(np.asarray(inp['preferred_step'])!=0):raise ValueError('Expected original zero-prior task')
    offset=vector(row['control_offset_local'],3,'control offset')
    def point(x):
        T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@offset;a,b,c=v;skew=np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
        return T[:3,3]+v,jl-skew@jw
    origin,_=point(q)
    if np.max(abs(origin-vector(row['observed_support_xyz'],3,'observed reference')))>2e-6:raise ValueError('Measured FK reference mismatch')
    cop=R.T@(vector(row['rear_cop_centering']['cop_world'],3,'measured COP')-target)
    axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.010]
    normals=np.array([-np.sign(cop[k])*R[:,k] for k in axes]).reshape(-1,3)
    inward=.0005 if side=='right' else 0.
    # A request is a bounded reference displacement, not predicted parcel motion.
    minimum=min(.0001,requested)
    active=3 if side=='right' else 0;old_error=e.copy();e[active]=.72*requested;e[active+1]=0.
    low=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);high=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055])
    if (low>=high).any():return None,dict(base,reason='empty_original_joint_bounds')
    def objective(x):
        dq=x-q;v=J@dq-e
        return 5000*float(v@v+sum((d*dq)**2)),10000*(J.T@v+d*d*dq)
    def inequality(x):
        p,j=point(x);motion=p-origin
        return np.r_[normals@motion-inward,motion[0]-minimum,requested-motion[0],guard.geometry.constraints(x)-.005],np.vstack([normals@j,j[0],-j[0],guard.geometry.jacobian(x)])
    def equality(x):
        p,j=point(x);return np.array([p[1]-origin[1]]),j[1:2]
    attempts=[]
    for name,seed in [('current',q),('parent',parent)]:
        fit=minimize(objective,np.clip(seed,low,high),jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=lambda x:inequality(x)[0],jac=lambda x:inequality(x)[1]),dict(type='eq',fun=lambda x:equality(x)[0],jac=lambda x:equality(x)[1])],method='SLSQP',options=dict(maxiter=300,ftol=1e-11))
        cmd=fit.x.astype(np.float32).astype(float);safe=guard.command(cmd,q,prev);iv,_=inequality(cmd);ev,_=equality(cmd)
        accepted=bool(fit.success and safe['accepted'] and min(iv)>=-1e-7 and max(abs(ev))<=1e-7)
        attempts.append(dict(seed=name,status=int(fit.status),iterations=int(fit.nit),solver_success=bool(fit.success),command=cmd.tolist(),accepted=accepted,original_final_guard=safe,inequality_residual_m=iv.tolist(),equality_residual_m=ev.tolist()))
        if accepted:
            motion=point(cmd)[0]-origin
            return cmd,dict(base,applied=True,requires_recontact=False,reason='nominal_rear_corridor_recovery',reference_delta_xyz_m=motion.tolist(),requested_x_m=requested,minimum_x_m=minimum,near_core_axes=axes,inward_requirement_m=inward,original_error=old_error.tolist(),recovery_error=e.tolist(),attempts=attempts)
    return None,dict(base,reason='no_verified_loaded_recovery',requested_x_m=requested,minimum_x_m=minimum,near_core_axes=axes,inward_requirement_m=inward,attempts=attempts)
