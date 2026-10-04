"""Joint11 proposal with original full9 objective and parent contact constraints.
No state mutation, capture, physical rollout or training admission. Default-off
selection and original control precedence are enforced by the runtime caller.
"""
import numpy as np
from functools import lru_cache
from joint_transport_margin_values_v1 import scene_margins
from scipy.optimize import minimize,Bounds
from loaded_z_priority_solver import up_and_jacobian
from loaded_z_priority_checks import NativeCertificateGeometry,check

def propose(*,step,side,scene,current,previous_q,previous_command,parent_command,decay,coordinate,elbow_reserve_m,quarter_enabled=False):
 G=scene.guard
 if elbow_reserve_m not in (0.,.0015):raise ValueError('Explicit frozen reserve required')
 zr=2 if side=='left' else 5;active_rows=slice(0,3) if side=='left' else slice(3,6)
 q,qp,prev,parent,a=[np.array(v,float) for v in [current,previous_q,previous_command,parent_command,decay]]
 for v in [q,qp,prev,parent,a]:
  if v.shape!=(11,) or not np.isfinite(v).all():raise ValueError('Invalid finite11 context')
 if type(step) is not int or step<1 or side not in ('left','right') or scene.side!=side:raise ValueError('Invalid selected context')
 if np.any(a<0) or np.any(a>.95) or not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Invalid response or parent rounding')
 for key,expected in [('lower',G.lower),('upper',G.upper),('step_limits',G.limits)]:
  if not np.array_equal(coordinate['task_inputs'][key],expected):raise ValueError('Changed original bounds')
 z=scene.record();task=coordinate['task_inputs'];J=np.array(task['jacobian']);e=np.array(task['error']);dam=np.array(task['damping']);prior=np.array(task['preferred_step']);assert J.shape==(9,11)
 np.testing.assert_allclose(task['current'],q,atol=1e-7,rtol=0);np.testing.assert_allclose(task['previous'],prev,atol=1e-7,rtol=0)
 loaded_z_applied=bool(coordinate['front_loaded_z_priority']['applied']);assert z['side']==side
 normal_target=np.array(coordinate['contact_normal_tracking']['target_local_up']);normal_target/=np.linalg.norm(normal_target)
 parent_linear_normal=float(np.linalg.norm(J[6:]@(parent-q)-e[6:]));parent_up,_=up_and_jacobian(G.model,parent,side);parent_exact_normal=float(np.linalg.norm(parent_up-normal_target))
 def contact_margins(u):
  up,_=up_and_jacobian(G.model,u,side)
  return np.array([parent_linear_normal-np.linalg.norm(J[6:]@(u-q)-e[6:]),parent_exact_normal-np.linalg.norm(up-normal_target)])
 def contact_height(u):return float(J[zr]@(u-parent))*1000
 bias=q-prev-a*(qp-prev);low=np.maximum.reduce([G.lower,q-G.limits,prev-.055]);high=np.minimum.reduce([G.upper,q+G.limits,prev+.055])
 def pred(u):return (1-a)*u+a*q+bias
 def objective(u):
  d=u-q;err=J@d-e;reg=d-prior
  return float(err@err+np.sum(dam*dam*reg*reg)),2*(J.T@err+dam*dam*reg)
 def margins(state,floor,elbow_floor=.005):
  return scene_margins(scene,state,floor,elbow_floor)
 def uncached_constraints(u):
  v=pred(u);parts=[margins(u,.8415,.005+elbow_reserve_m),margins(v,.8415,.005+elbow_reserve_m),v-G.lower,G.upper-v,contact_margins(u)]
  for end in [u,v]:
   for alpha in [.25,.5,.75]:parts.append(margins(q+alpha*(end-q),.84))
  return np.concatenate(parts)*1000
 @lru_cache(maxsize=256)
 def cached_constraints(key):
  # Exact float64 bytes only: no rounding, interpolation or cross-call reuse.
  return uncached_constraints(np.frombuffer(key,dtype=np.float64))
 def constraints(u):
  # Local to this immutable proposal context; give every caller its own array.
  return cached_constraints(np.asarray(u,dtype=np.float64).tobytes()).copy()
 seed=parent.copy();initialization='actual_same_step_parent_command_only'
 seed=np.clip(seed,low,high)
 def scaled_objective(u):
  value,gradient=objective(u);return value*1000.,gradient*1000.
 fit=minimize(scaled_objective,seed,jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints),dict(type='eq',fun=contact_height,jac=lambda u:J[zr]*1000)],method='SLSQP',options=dict(maxiter=240,ftol=1e-10))
 u=fit.x.astype(np.float32).astype(float);v=pred(u);guard=G.command(u,q,prev);vals=constraints(u)/1000;pathrows=[]
 for name,end in [('nominal',u),('predicted',v)]:
  for alpha in np.linspace(0,1,17):
   state=q+alpha*(end-q);ms=margins(state,.84);pathrows.append(dict(path=name,alpha=float(alpha),minimum_margin_m=float(ms.min()),passed=bool(ms.min()>=-2e-7)))
 active0=scene.details(parent);active1=scene.details(u);physicalq=scene.details(q);er0=J@(parent-q)-e;er1=J@(u-q)-e
 result=dict(step=step,side=side,original_loaded_z_applied=loaded_z_applied,solver_success=bool(fit.success),solver_status=int(fit.status),iterations=int(fit.nit),message=str(fit.message),rounded_constraints_passed=bool(vals.min()>=-2e-7),min_constraint_margin_m=float(vals.min()),original_command_guard=guard,all_sampled_paths_passed=all(z['passed'] for z in pathrows),sampled_paths=pathrows,original_objective_parent=objective(parent)[0],original_objective_proposal=objective(u)[0],parent_task_error=er0.tolist(),proposal_task_error=er1.tolist(),active_position_error_norm_parent=float(np.linalg.norm(er0[active_rows])),active_position_error_norm_proposal=float(np.linalg.norm(er1[active_rows])),normal_error_norm_parent=float(np.linalg.norm(er0[6:9])),normal_error_norm_proposal=float(np.linalg.norm(er1[6:9])),active_contact_local_point_change_m=(active1['point']-active0['point']).tolist(),active_world_normal_change=(active1['normal_local_up']-active0['normal_local_up']).tolist(),max_command_delta_from_parent_rad=float(abs(u-parent).max()),waist_delta_from_parent_rad=float(u[0]-parent[0]),command=u.tolist(),parent_command=parent.tolist(),current=q.tolist(),previous_command=prev.tolist(),predicted_q=v.tolist(),predicted_elbow_gaps_mm=(G.geometry.constraints(v)*1000).tolist(),predicted_inactive_height_mm=scene.details(v)['inactive_z']*1000,scene=scene.record(),independent_stationarity_certificate=False,continuous_path_certificate=False,physical_command_issued=False,training_ready=False)
 from effective_loaded_contact_task_v1 import resolve
 contact_task,binding=resolve(coordinate,side=side,current=q,parent_command=parent,quarter_enabled=quarter_enabled)
 contact_check=check(G,NativeCertificateGeometry(G),contact_task,coordinate,parent,u,side)
 result['effective_loaded_contact_binding']=binding
 result['elbow_reserve_m']=float(elbow_reserve_m)
 result['nominal_predicted_elbow_floor_m']=.005+elbow_reserve_m
 result['solver_maxiter']=240
 result['solver_ftol']=1e-10
 result['objective_scale']=1000.0
 result['initialization']=initialization
 result['original_loaded_contact_check']=contact_check if loaded_z_applied else None
 result['parent_height_task_preserved']=bool(abs(contact_height(u))<=.0002)
 result['original_contact_primal_preserved']=bool((not loaded_z_applied or abs(contact_check['z_error_mm'])<=.0002) and result['parent_height_task_preserved'] and contact_check['exact_attitude_delta']<=1e-6 and contact_check['linear_attitude_delta_mm']<=.0002 and min(contact_check['nominal_table_margins_m'])>=0)
 result['contact_height_equality_residual_m']=contact_height(u)/1000
 result['contact_margins']=contact_margins(u).tolist()
 result.update(previous_q=qp.tolist(),decay=a.tolist(),causal_bias=bias.tolist())
 result['preliminary_passed']=bool(result['solver_success'] and result['rounded_constraints_passed'] and result['original_command_guard']['accepted'] and result['all_sampled_paths_passed'] and result['original_contact_primal_preserved'])
 return (u if result['preliminary_passed'] else None),result
