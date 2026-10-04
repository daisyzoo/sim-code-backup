"""Unwired, default-off, unloaded left-bag recovery clearance proposal.
Keep every original measured scene gate. Freeze predicted waist/active-arm q
under the existing causal response hypothesis; optimize inactive5 only to get
nominal and predicted lowest-hand height841.5mm. No state or scene writes.
Requires independent audit, lifecycle/timeout handling and actual measurement
before any recovery entry. It neither captures an anchor nor starts a path.
"""
import numpy as np
from scipy.optimize import minimize,Bounds
from front_initial_center_plan import checked_scene

def propose(*,enabled=False,selected=False,side,mode,counter,guard_stop,
            observed_load_n,filtered_load_n,current,previous_q,previous_command,
            decay,scene):
 if type(enabled) is not bool or type(selected) is not bool:raise ValueError('Explicit boolean required')
 if not enabled:return None,dict(applied=False,reason='disabled')
 if not selected or side!='left' or scene.side!='left' or mode not in ('top_cross','top_descend') or type(counter) is not int or counter<1:return None,dict(applied=False,reason='not_selected_unloaded_front_bag_recovery')
 if guard_stop:return None,dict(applied=False,reason='parent_guard')
 if not np.isfinite([observed_load_n,filtered_load_n]).all():raise ValueError('Nonfinite load')
 if observed_load_n!=0. or not 0<=filtered_load_n<=.05:return None,dict(applied=False,reason='not_measured_unloaded')
 q,qp,prev,a=[np.asarray(x,float) for x in [current,previous_q,previous_command,decay]]
 if any(x.shape!=(11,) or not np.isfinite(x).all() for x in [q,qp,prev,a]) or np.any(a<0) or np.any(a>.95):raise ValueError('Invalid original upper11 context')
 measured=checked_scene(scene,q)
 if not measured['accepted']:return None,dict(applied=False,reason='original_measured_geometry_rejected',measured=measured)
 if measured['inactive_lowest_z_m']>=.841:return None,dict(applied=False,reason='original_recovery_entry_already_has_headroom')
 g=scene.guard;low=np.maximum.reduce([g.lower,q-g.limits,prev-.055]);high=np.minimum.reduce([g.upper,q+g.limits,prev+.055])
 if np.any(low>high):return None,dict(applied=False,reason='empty_original_bounds')
 bias=q-prev-a*(qp-prev);hold=(q-a*q-bias)/(1-a)
 if np.any(hold[:6]<low[:6]) or np.any(hold[:6]>high[:6]):return None,dict(applied=False,reason='active_hold_outside_original_bounds')
 def command(x):return np.r_[hold[:6],x]
 def predict(u):return (1-a)*u+a*q+bias
 def objective(x):v=x-q[6:];return float(v@v),2*v
 def constraints(x):
  u=command(x);pred=predict(u);vals=[]
  for z in [u,pred]:
   d=scene.details(z);vals.extend([d['inactive_z']-.8415,d['point'][2]-scene.core[2]/2-.004,*list(np.asarray(list(d['gaps'].values()))-.01),*list(g.geometry.constraints(z)-.005)])
  return np.asarray(vals)
 fit=minimize(objective,np.clip(q[6:],low[6:],high[6:]),jac=True,bounds=Bounds(low[6:],high[6:]),constraints=[dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(maxiter=120,ftol=1e-12))
 u=command(fit.x).astype(np.float32);pred=predict(u);check=g.command(u,q,prev);nominal=checked_scene(scene,u);predicted=checked_scene(scene,pred)
 # Sample original geometry along both one-step segments. This is explicitly
 # not a continuous full-robot collision certificate.
 paths={}
 for name,end in [('nominal',u),('predicted',pred)]:
  nodes=max(1,int(np.ceil(np.max(abs(end-q)/(g.limits*.25)))));states=[q+(end-q)*i/nodes for i in range(nodes+1)];proofs=[checked_scene(scene,z) for z in states];paths[name]=dict(states=[z.tolist() for z in states],checks=proofs,accepted=all(v['accepted'] for v in proofs))
 accepted=bool(fit.success and np.isfinite(u).all() and check['accepted'] and nominal['accepted'] and predicted['accepted'] and min(nominal['inactive_lowest_z_m'],predicted['inactive_lowest_z_m'])>=.8415-2e-7 and all(v['accepted'] for v in paths.values()))
 record=dict(applied=accepted,reason='unissued_verified_local_proposal' if accepted else 'proposal_rejected',optimizer_status=int(fit.status),optimizer_message=str(fit.message),iterations=int(fit.nit),current=q.tolist(),previous_q=qp.tolist(),previous_command=prev.tolist(),decay=a.tolist(),causal_bias=bias.tolist(),command=u.tolist(),predicted_q=pred.tolist(),measured=measured,nominal=nominal,predicted=predicted,original_command_check=check,sampled_paths=paths,predicted_active_hold_error=float(np.max(abs(pred[:6]-q[:6]))),scope=__doc__,physical_success=False,training_ready=False)
 return (u if accepted else None),record
