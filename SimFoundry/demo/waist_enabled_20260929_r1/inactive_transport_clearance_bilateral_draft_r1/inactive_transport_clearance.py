"""Bilateral inactive-five version; active side is taken from the verified scene.
Unwired inactive-five-only correction of a recorded parent transport command.
Keeps waist and active left5 commands bit-identical. The response estimate is a
hypothesis, not a physical certificate. Original measured floor and joint/elbow/
parcel guards remain. A rejected correction never certifies its parent as safe.
"""
import numpy as np
from scipy.optimize import minimize,Bounds

def propose(*,enabled=False,selected=False,mode,guard_stop,scene,current,previous_q,
            previous_command,parent_command,decay,task_inputs):
 if type(enabled) is not bool or type(selected) is not bool:raise ValueError('Boolean selection required')
 if not enabled:return None,dict(applied=False,reason='disabled')
 if not selected or scene.side not in ('left','right') or mode not in ('top_press','top_push','top_lift','top_cross','top_descend') or guard_stop:return None,dict(applied=False,reason='not_selected_transport')
 q,qp,prev,parent,a=[np.asarray(v,float) for v in [current,previous_q,previous_command,parent_command,decay]]
 if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,qp,prev,parent,a]) or np.any(a<0) or np.any(a>.95):raise ValueError('Invalid original state or response')
 if not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Parent must be actual float32 command')
 g=scene.guard;inactive_indices=np.arange(6,11) if scene.side=='left' else np.arange(1,6);fixed_indices=np.setdiff1d(np.arange(11),inactive_indices);measured=scene.details(q)
 if measured['inactive_z']<.84-2e-7:return None,dict(applied=False,reason='already_below_original_measured_floor')
 original=g.command(parent,q,prev)
 if not original['accepted']:return None,dict(applied=False,reason='parent_original_guard_rejected')
 low=np.maximum.reduce([g.lower,q-g.limits,prev-.055]);high=np.minimum.reduce([g.upper,q+g.limits,prev+.055]);bias=q-prev-a*(qp-prev)
 J=np.array(task_inputs['jacobian']);e=np.array(task_inputs['error']);dam=np.array(task_inputs['damping']);prior=np.array(task_inputs['preferred_step'])
 if J.shape!=(9,11) or e.shape!=(9,) or dam.shape!=(11,) or prior.shape!=(11,) or not all(np.isfinite(v).all() for v in [J,e,dam,prior]):raise ValueError('Invalid original IK task')
 if not np.allclose(task_inputs['current'],q,rtol=0,atol=1e-7) or not np.allclose(task_inputs['previous'],prev,rtol=0,atol=1e-7):raise ValueError('Stale task input')
 def cmd(x):
  out=parent.copy();out[inactive_indices]=x;return out
 def predict(u):return (1-a)*u+a*q+bias
 def objective(x):
  delta=cmd(x)-q;err=J@delta-e;reg=delta-prior
  return float(1e6*(err@err+np.sum(dam*dam*reg*reg))),2e6*(J.T@err+dam*dam*reg)[inactive_indices]
 def margins(z):
  v=scene.details(z)
  return np.r_[v['inactive_z']-.8415,v['gaps']['inactive_target']-.01,v['gaps']['inactive_other']-.01,g.geometry.constraints(z)-.005]
 def constraints(x):
  u=cmd(x);return np.r_[margins(u),margins(predict(u))]*1000
 fit=minimize(objective,parent[inactive_indices].copy(),jac=True,bounds=Bounds(low[inactive_indices],high[inactive_indices]),constraints=[dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(maxiter=120,ftol=1e-11))
 u=cmd(fit.x).astype(np.float32).astype(float);pred=predict(u);guard=g.command(u,q,prev);checks=dict(solver_success=bool(fit.success),original_command_guard=guard['accepted'],waist_and_active_command_identical=bool(np.array_equal(u[fixed_indices],parent[fixed_indices])),nominal_and_predicted_margin=bool(np.min(np.r_[margins(u),margins(pred)])>=-2e-7))
 paths=[]
 for kind,end in [('nominal',u),('predicted',pred)]:
  for alpha in np.linspace(0,1,5):
   state=q+(end-q)*alpha;v=scene.details(state);passed=bool(v['inactive_z']>=.84-2e-7 and min(v['gaps']['inactive_target'],v['gaps']['inactive_other'])>=.01-2e-7 and min(g.geometry.constraints(state))>=.005-2e-7)
   paths.append(dict(kind=kind,alpha=float(alpha),q=state.tolist(),passed=passed,inactive_lowest_z_m=v['inactive_z']))
 checks['sampled_original_geometry']=all(p['passed'] for p in paths);accepted=all(checks.values())
 return (u if accepted else None),dict(applied=accepted,reason='unissued_local_correction' if accepted else 'no_verified_local_correction',checks=checks,solver_status=int(fit.status),solver_message=str(fit.message),iterations=int(fit.nit),command=u.tolist(),predicted_q=pred.tolist(),parent_command=parent.tolist(),current=q.tolist(),previous_q=qp.tolist(),previous_command=prev.tolist(),causal_bias=bias.tolist(),decay=a.tolist(),scene=scene.record(),nominal_inactive_lowest_z_m=scene.details(u)['inactive_z'],predicted_inactive_lowest_z_m=scene.details(pred)['inactive_z'],sampled_paths=paths,continuous_path_certified=False,physical_success=False,training_ready=False)
