"""Pure nominal unloading step after an unverified loaded corridor recovery.
No simulator writes or physical load prediction. Caller must transition the
original controller into recontact/lift, reset pressure per its original method,
and confirm measured unloading before planning/handover. No unsafe fallback.
"""
import numpy as np
from scipy.optimize import minimize,Bounds


def solve_lift(*,guard,row,coordinate,current,previous,parent_command,recovery_result):
    if recovery_result.get('requires_recontact') is not True or recovery_result.get('applied') is not False:raise ValueError('Unverified recovery required')
    if recovery_result.get('reason')!='no_verified_loaded_recovery':raise ValueError('Route/bounds rejection requires separate handling')
    if row['mode']!='top_push' or row.get('route_stop_reason') or row.get('release_reason') or coordinate.get('region_joint_override') or coordinate.get('terminal_joint_hold'):raise ValueError('Original guard priority')
    def vector(v,n):
        a=np.asarray(v,float)
        if a.shape!=(n,) or not np.isfinite(a).all():raise ValueError('Invalid finite vector')
        return a.copy()
    q=vector(current,11);prev=vector(previous,11);parent=vector(parent_command,11);inp=coordinate['task_inputs'];J=np.asarray(inp['jacobian'],float);e=vector(inp['error'],9);d=vector(inp['damping'],11)
    if J.shape!=(9,11) or not np.isfinite(J).all() or (d<=0).any():raise ValueError('Invalid task objective')
    if not np.array_equal(q,np.asarray(coordinate['upper_q'])) or not np.array_equal(q,np.asarray(inp['current'])) or not np.array_equal(prev,np.asarray(inp['previous'])):raise ValueError('Causal input mismatch')
    side=coordinate['active_side']
    if side not in ['left','right']:raise ValueError('Invalid side')
    offset=vector(row['control_offset_local'],3)
    def point(x):
        T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@offset;a,b,c=v;skew=np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
        return T[:3,3]+v,jl-skew@jw
    def lowest(x):
        T,jl,jw=guard.model.fk(side,x);vertices=guard.model.vertices[side];world=vertices@T[:3,:3].T+T[:3,3];i=int(world[:,2].argmin());v=T[:3,:3]@vertices[i];a,b,c=v;skew=np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
        return float(world[i,2]),(jl-skew@jw)[2]
    initial_low,_=lowest(q)
    origin,_=point(q)
    if max(abs(origin-vector(row['observed_support_xyz'],3)))>2e-6:raise ValueError('Observed support mismatch')
    active=3 if side=='right' else 0;e[active:active+3]=[0.,0.,.72*.003]
    lo=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);hi=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055])
    if np.any(lo>=hi):return None,dict(applied=False,reason='empty_original_bounds',requires_stop=True)
    def objective(x):
        dq=x-q;res=J@dq-e;return 5000*float(res@res+sum((d*dq)**2)),10000*(J.T@res+d*d*dq)
    def inequality(x):
        p,j=point(x);move=p-origin
        height,height_j=lowest(x)
        return np.r_[move[2]-.0005,.003-move[2],height-initial_low-.0005,guard.geometry.constraints(x)-.005],np.vstack([j[2],-j[2],height_j,guard.geometry.jacobian(x)])
    def equality(x):
        p,j=point(x);return (p-origin)[:2],j[:2]
    attempts=[]
    for name,seed in [('current',q),('parent',parent)]:
        fit=minimize(objective,np.clip(seed,lo,hi),jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=lambda x:inequality(x)[0],jac=lambda x:inequality(x)[1]),dict(type='eq',fun=lambda x:equality(x)[0],jac=lambda x:equality(x)[1])],method='SLSQP',options=dict(maxiter=300,ftol=1e-11))
        cmd=fit.x.astype(np.float32).astype(float);safe=guard.command(cmd,q,prev);iv,_=inequality(cmd);ev,_=equality(cmd);accepted=bool(fit.success and safe['accepted'] and min(iv)>=-1e-7 and max(abs(ev))<=1e-7)
        attempts.append(dict(seed=name,solver_status=int(fit.status),accepted=accepted,command=cmd.tolist(),original_guard=safe,inequality_residual_m=iv.tolist(),equality_residual_m=ev.tolist()))
        if accepted:return cmd,dict(applied=True,reason='nominal_vertical_unload',reference_delta_xyz_m=(point(cmd)[0]-origin).tolist(),attempts=attempts,requires_measured_unloaded=True)
    return None,dict(applied=False,reason='no_verified_unload_step',attempts=attempts,requires_stop=True)
