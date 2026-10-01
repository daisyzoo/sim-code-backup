# OFFLINE ONLY. Soft center preference; all original endpoint/path gates retained.
"""Causal unloaded pose preference, not physical contact certification.
Current scene/q and original causal planner endpoint are the only seeds.
Every selected nominal path retains original scene checks and joint spacing.
PCA alignment is a heuristic; original runtime guards/handover remain required.
"""
import numpy as np
from scipy.optimize import minimize,Bounds
from articulated_hand_geometry import skew


def interpolate(scene,nodes):
    guard=scene.guard;waypoints=[]
    for a,b in zip(nodes,nodes[1:]):
        count=max(1,int(np.ceil(max(abs(b-a)/(guard.limits*.25)))))
        waypoints.extend([np.clip(a+(b-a)*i/count,guard.lower,guard.upper).tolist() for i in range(1,count+1)])
    checks=[scene.check(x) for x in waypoints]
    return dict(accepted=bool(waypoints and all(g['accepted'] for g in checks)),waypoints=waypoints,checks=checks)


def lift_endpoint(scene,reference,height):
    guard=scene.guard;xy=scene.details(reference)['point'][:2].copy()
    def cost(x):
        d=x-reference;return float(d@d),2*d
    def cons(x):
        g=scene.details(x);p=g['point'];J=g['jacobian'];h=p[2]-scene.core[2]/2
        return np.r_[.002-(p[:2]-xy),.002+(p[:2]-xy),h-height,height+.001-h,g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
    fit=minimize(cost,np.clip(reference,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12))
    x=np.asarray(fit.x,float);finite=bool(np.isfinite(x).all());minimum=float(min(cons(x)[0])) if finite else None
    good=bool(fit.success and finite and minimum>=-2e-7 and scene.check(x)['accepted'] and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7))
    return dict(accepted=good,status=int(fit.status),iterations=int(fit.nit),reference=reference.tolist(),height_m=float(height),xy_tolerance_m=.002,height_tolerance_m=.001,candidate=x.tolist() if finite else None,minimum_constraint_m=minimum)


def plan(scene,q,*,step,parent_plan):
    q=np.asarray(q,float);guard=scene.guard
    if q.shape!=(11,) or not np.isfinite(q).all() or type(step) is not int or step<1:raise ValueError('Invalid planning state')
    if not isinstance(parent_plan,dict) or type(parent_plan.get('accepted')) is not bool:raise ValueError('Invalid parent plan')
    if parent_plan['accepted']:
        if parent_plan['step']!=step or parent_plan['scene']!=scene.record() or not np.array_equal(parent_plan['start'],q):raise ValueError('Parent plan does not match current observation')
    metadata=dict(offline_center_penalty=True,center_weight_per_m2=400.,parent_is_same_observation_minimum_motion=True,enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],endpoint_attempts=[],lift_attempts=[],selected='original_fallback',parent_plan=parent_plan,not_physical_contact_proof=True)
    def fallback(reason):return dict(parent_plan,minimum_motion_pose=dict(metadata,fallback_reason=reason))
    if not scene.check(q)['accepted']:return fallback('current_scene_rejected')
    _,vectors=np.linalg.eigh(np.cov(guard.model.vertices[scene.side].T));axis=vectors[:,0];normal=scene.rotation[:,2];half=scene.core[:2]/2-.020
    def alignment(x):
        T,jl,jw=guard.model.fk(scene.side,x);v=T[:3,:3]@axis;return float(normal@v),normal@(-skew(v)@jw)
    def cost(x):
        d=x-q;g=scene.details(x);p=g['point'][:2];J=g['jacobian'][:2]
        return float(d@d+400.*(p@p)),2*d+800.*(J.T@p)
    def cons(x):
        g=scene.details(x);p=g['point'];J=g['jacobian'];a,da=alignment(x)
        return np.r_[a*a-.8**2,half-p[:2],half+p[:2],p[2]-scene.core[2]/2-.006,scene.core[2]/2+.007-p[2],g['inactive_z']-.84,guard.geometry.constraints(x)-.005],np.vstack([2*a*da,-J[:2],J[:2],J[2],-J[2],g['inactive_z_jacobian'],guard.geometry.jacobian(x)])
    original=np.asarray(parent_plan['endpoint'],float) if parent_plan['accepted'] else q.copy()
    attempts=[]
    for label,seed in [('original_endpoint',original),('current_observed',q.copy())]:
        fit=minimize(cost,np.clip(seed,guard.lower,guard.upper),jac=True,bounds=Bounds(guard.lower,guard.upper),constraints=[dict(type='ineq',fun=lambda x:cons(x)[0],jac=lambda x:cons(x)[1]),dict(type='ineq',fun=lambda x:np.array(list(scene.details(x)['gaps'].values()))-.01)],method='SLSQP',options=dict(maxiter=220,ftol=1e-12))
        x=np.asarray(fit.x,float);finite=bool(np.isfinite(x).all());minimum=float(min(cons(x)[0])) if finite else None
        accepted=bool(fit.success and finite and minimum>=-2e-7 and min(scene.details(x)['gaps'].values())>=.01-2e-7 and np.all(x>=guard.lower-2e-7) and np.all(x<=guard.upper+2e-7))
        path=interpolate(scene,[q,x]) if accepted else None
        attempts.append(dict(seed=label,status=int(fit.status),iterations=int(fit.nit),accepted=accepted,objective=float(fit.fun) if np.isfinite(fit.fun) else None,thin_axis_alignment_abs=abs(alignment(x)[0]) if finite else None,minimum_constraint_m=minimum,candidate=x.tolist() if finite else None,path=path))
    metadata['endpoint_attempts']=attempts;usable=[a for a in attempts if a['accepted'] and a['path']['accepted']]
    if usable:
        best=min(usable,key=lambda a:a['objective']);path=best['path'];nodes=[q.tolist(),best['candidate']];route='straight'
    else:
        feasible=[a for a in attempts if a['accepted']]
        if not feasible:return fallback('no_verified_endpoint')
        best=min(feasible,key=lambda a:a['objective']);end=np.asarray(best['candidate'])
        for height in [.015,.030,.060]:
            first=lift_endpoint(scene,q,max(height,scene.details(q)['point'][2]-scene.core[2]/2));last=lift_endpoint(scene,end,height);nodes=[q.tolist(),first['candidate'],last['candidate'],end.tolist()]
            path=interpolate(scene,list(map(np.asarray,nodes))) if first['accepted'] and last['accepted'] else None
            metadata['lift_attempts'].append(dict(height_m=height,start_lift=first,end_lift=last,nodes=nodes,path=path,accepted=bool(path and path['accepted'])))
        valid=[a for a in metadata['lift_attempts'] if a['accepted']]
        if not valid:return fallback('no_verified_nominal_path')
        chosen=min(valid,key=lambda a:len(a['path']['waypoints']));path=chosen['path'];nodes=chosen['nodes'];route='raised'
    metadata.update(selected='candidate',fallback_reason=None,route=route,nodes=nodes,nominal_waypoints=len(path['waypoints']),thin_axis_local=axis.tolist(),selected_path_checks=path['checks'])
    return dict(accepted=True,reason='minimum_motion_endpoint_and_sampled_path',step=step,start=q.tolist(),endpoint=best['candidate'],waypoints=path['waypoints'],best={k:v for k,v in best.items() if k!='path'},attempts=[{k:v for k,v in a.items() if k!='path'} for a in attempts],scene=scene.record(),minimum_motion_pose=metadata,scope=__doc__)
