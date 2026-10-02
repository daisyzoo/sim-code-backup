"""Nominal +X mobility check for an unloaded recontact endpoint.
Uses no invented contact force/COP. A passed geometric witness does not establish
loaded traction; runtime measured handover and loaded checks remain mandatory.
No simulator or object writes. Failed witness cannot authorize a parent fallback.
"""
import numpy as np
from scipy.optimize import minimize,Bounds


def witness(scene,endpoint,*,retry_feasible=False):
    if type(retry_feasible) is not bool:raise ValueError("Explicit retry option required")
    q=np.asarray(endpoint,float);guard=scene.guard
    if q.shape!=(11,) or not np.isfinite(q).all():raise ValueError('Invalid endpoint')
    if not scene.check(q)['accepted']:return dict(accepted=False,reason='endpoint_scene_rejected')
    geometry=scene.details(q);offset=np.asarray(geometry['vertex_local'],float);side=scene.side
    def point(x):
        T,jl,jw=guard.model.fk(side,x);v=T[:3,:3]@offset;a,b,c=v;skew=np.array([[0.,-c,b],[c,0.,-a],[-b,a,0.]])
        return T[:3,3]+v,jl-skew@jw
    origin,_=point(q);low=np.maximum(guard.lower,q-guard.limits);high=np.minimum(guard.upper,q+guard.limits)
    if (low>=high).any():return dict(accepted=False,reason='empty_original_bounds')
    def objective(x):
        d=x-q;return float(d@d),2*d
    def inequality(x):
        p,J=point(x);g=scene.details(x);local=scene.rotation.T@(p-scene.target);half=scene.core[:2]/2-.010;L=scene.rotation.T@J
        return np.r_[p[0]-origin[0]-.001,.002-(p[0]-origin[0]),half-local[:2],half+local[:2],g['point'][2]-scene.core[2]/2-.004,g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([J[0],-J[0],-L[:2],L[:2],g['jacobian'][2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
    def equality(x):
        p,J=point(x);return (p-origin)[1:],J[1:]
    def solve(seed):
        return minimize(objective,np.clip(seed,low,high),jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=lambda x:inequality(x)[0],jac=lambda x:inequality(x)[1]),dict(type='eq',fun=lambda x:equality(x)[0],jac=lambda x:equality(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12))
    fit=solve(q)
    prior_attempt=None
    if retry_feasible and fit.status==9 and np.isfinite(fit.x).all():
        seed=fit.x.astype(np.float32).astype(float);iv0,_=inequality(seed);ev0,_=equality(seed)
        if guard.command(seed,q,q)["accepted"] and min(iv0)>=-1e-7 and max(abs(ev0))<=1e-7 and scene.check(seed)["accepted"]:
            prior_attempt=dict(solver_status=int(fit.status),solver_success=bool(fit.success),iterations=int(fit.nit),candidate=seed.tolist(),inequality_residual_m=iv0.tolist(),equality_residual_m=ev0.tolist(),accepted=False)
            fit=solve(seed)
    cmd=fit.x.astype(np.float32).astype(float);iv,_=inequality(cmd);ev,_=equality(cmd);safe=guard.command(cmd,q,q);okay=bool(fit.success and safe['accepted'] and min(iv)>=-1e-7 and max(abs(ev))<=1e-7 and scene.check(cmd)['accepted']);path=[]
    if okay:
        count=max(1,int(np.ceil(max(abs(cmd-q)/(guard.limits*.25)))))
        for i in range(1,count+1):
            x=q+(cmd-q)*i/count;check=scene.check(x);final=guard.command(x,q,q);path.append(dict(command=x.tolist(),scene_check=check,final_guard=final))
        okay=bool(all(v['scene_check']['accepted'] and v['final_guard']['accepted'] for v in path))
    result=dict(accepted=okay,reason='nominal_unloaded_transport_witness' if okay else 'no_verified_transport_witness',endpoint=q.tolist(),candidate=cmd.tolist(),reference_offset_local=offset.tolist(),reference_delta_xyz_m=(point(cmd)[0]-origin).tolist(),minimum_x_step_m=.001,maximum_x_step_m=.002,inequality_residual_m=iv.tolist(),equality_residual_m=ev.tolist(),solver_status=int(fit.status),solver_success=bool(fit.success),final_guard=safe,path=path,not_loaded_contact_proof=True)
    if retry_feasible:result["feasible_endpoint_retry"]=dict(enabled=True,attempted=prior_attempt is not None,original_attempt=prior_attempt,maximum_extra_retries=1,original_ftol=1e-12,original_maxiter=220,original_problem_unchanged=True)
    return result


def filter_plan(scene,current,step,parent_plan,*,enabled=False):
    if type(enabled) is not bool:raise ValueError('enabled must be bool')
    if not enabled:return parent_plan
    if type(parent_plan.get('accepted')) is not bool:raise ValueError('Invalid parent plan')
    if not parent_plan['accepted']:return parent_plan
    if parent_plan['step']!=step or parent_plan['scene']!=scene.record() or not np.array_equal(parent_plan['start'],np.asarray(current,float)):raise ValueError('Parent plan must match current observation')
    result=witness(scene,parent_plan['endpoint'])
    if not result['accepted']:return dict(accepted=False,reason='rear_transport_endpoint_unverified',step=step,start=list(current),scene=scene.record(),parent_plan=parent_plan,rear_transport_witness=result)
    return dict(parent_plan,rear_transport_witness=result)
