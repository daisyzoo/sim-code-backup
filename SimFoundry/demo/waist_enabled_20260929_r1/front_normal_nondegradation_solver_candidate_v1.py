"""Uninstalled explicit exact-support-normal planning with original full9 objective.
No state mutation, capture, physical rollout or training admission. Default-off
selection and original control precedence are enforced by the runtime caller.
"""
import numpy as np
from scipy.optimize import minimize,Bounds
from loaded_z_priority_solver import up_and_jacobian
from loaded_z_priority_checks import NativeCertificateGeometry,check

def _propose_constrained(*,step,side,scene,current,previous_q,previous_command,parent_command,decay,coordinate,elbow_reserve_m,quarter_enabled=False):
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
  g=scene.details(state)
  return np.r_[g['inactive_z']-floor,g['gaps']['inactive_target']-.01,g['gaps']['inactive_other']-.01,g['gaps']['active_other']-.01,G.geometry.constraints(state)-elbow_floor]
 from loaded_z_priority_checks import support_point
 center=np.array(coordinate['active_support_reference']['center_local']);normal=np.array(scene.record()['target_quat'])
 from scipy.spatial.transform import Rotation
 normal=Rotation.from_quat(normal).as_matrix()[:,2]
 reference=support_point(G.model,q,side,normal,center)
 xr=0 if side=='left' else 3;direction=float(np.sign(e[xr]))
 if direction==0:raise ValueError('No original transverse correction requested')
 def cross_margin(u):return direction*(support_point(G.model,u,side,normal,center)[0]-reference[0])
 yr=1 if side=='left' else 4;forward_direction=float(np.sign(e[yr]))
 if forward_direction==0:raise ValueError('No original main direction request')
 def forward_margin(u):return forward_direction*(support_point(G.model,u,side,normal,center)[1]-reference[1])
 def base_constraints(u):
  v=pred(u);parts=[margins(u,.8415,.005+elbow_reserve_m),margins(v,.8415,.005+elbow_reserve_m),v-G.lower,G.upper-v,contact_margins(u)]
  for end in [u,v]:
   for alpha in [.25,.5,.75]:parts.append(margins(q+alpha*(end-q),.84))
  return np.r_[np.concatenate(parts),cross_margin(u),forward_margin(u)]*1000
 # Preserve the diagnostic arithmetic order for its added response constraints.
 def response(u):return (1-a)*u+a*q+q-prev-a*(qp-prev)
 def displacement(u):return support_point(G.model,u,side,normal,center)-reference
 old=coordinate['joint_transport_clearance'];tc=old['collector_context']
 for key,value in [('current',q),('previous_q',qp),('previous_command',prev),('decay',a)]:
  if not np.array_equal(tc[key],value):raise ValueError('Stale collector context: '+key)
 if tc['scene']!=scene.record() or old['parent_command']!=parent.tolist() or coordinate['front_loaded_z_priority']['output_command']!=parent.tolist():raise ValueError('Unbound parent or scene')
 final=np.asarray(old['output_command'],float)
 if final.shape!=(11,) or not np.isfinite(final).all() or not np.array_equal(final,final.astype(np.float32)):raise ValueError('Invalid original final command')
 load=float(coordinate['front_loaded_z_priority']['context']['observed_vertical_load_n'])
 if not np.isfinite(load):raise ValueError('Nonfinite observed force')
 lower_normal=float(normal@displacement(parent))
 if load<.3 or lower_normal>=0:
  return None,dict(step=step,side=side,selected=False,reason='requires_loaded_original_inward_parent',observed_vertical_load_n=load,parent_normal_delta_m=lower_normal,requires_recovery=True,command=None,training_ready=False,physical_command_issued=False)
 forecast_limit=float(normal@displacement(response(final)))
 def constraints(u):
  nominal=displacement(u);forecast=displacement(response(u))
  return np.r_[base_constraints(u),np.array([direction,forward_direction])*forecast[:2]*1000,(float(normal@nominal)-lower_normal)*1000,-float(normal@nominal)*1000,(forecast_limit-float(normal@forecast))*1000]
 seed=parent.copy();initialization='actual_same_step_parent_command_only'
 seed=np.clip(seed,low,high)
 def scaled_objective(u):
  value,gradient=objective(u);return value*1000.,gradient*1000.
 fit=minimize(scaled_objective,seed,jac=True,bounds=Bounds(low,high),constraints=[dict(type='ineq',fun=constraints)],method='SLSQP',options=dict(maxiter=240,ftol=1e-10))
 u=fit.x.astype(np.float32).astype(float);v=pred(u);guard=G.command(u,q,prev);vals=constraints(u)/1000;pathrows=[]
 for name,end in [('nominal',u),('predicted',v)]:
  for alpha in np.linspace(0,1,17):
   state=q+alpha*(end-q);ms=margins(state,.84);pathrows.append(dict(path=name,alpha=float(alpha),minimum_margin_m=float(ms.min()),passed=bool(ms.min()>=-2e-7)))
 active0=scene.details(parent);active1=scene.details(u);physicalq=scene.details(q);er0=J@(parent-q)-e;er1=J@(u-q)-e
 result=dict(step=step,side=side,original_loaded_z_applied=loaded_z_applied,solver_success=bool(fit.success),solver_status=int(fit.status),iterations=int(fit.nit),message=str(fit.message),rounded_constraints_passed=bool(vals.min()>=-2e-7),min_constraint_margin_m=float(vals.min()),original_command_guard=guard,all_sampled_paths_passed=all(z['passed'] for z in pathrows),sampled_paths=pathrows,original_objective_parent=objective(parent)[0],original_objective_proposal=objective(u)[0],parent_task_error=er0.tolist(),proposal_task_error=er1.tolist(),active_position_error_norm_parent=float(np.linalg.norm(er0[active_rows])),active_position_error_norm_proposal=float(np.linalg.norm(er1[active_rows])),normal_error_norm_parent=float(np.linalg.norm(er0[6:9])),normal_error_norm_proposal=float(np.linalg.norm(er1[6:9])),active_contact_local_point_change_m=(active1['point']-active0['point']).tolist(),active_world_normal_change=(active1['normal_local_up']-active0['normal_local_up']).tolist(),max_command_delta_from_parent_rad=float(abs(u-parent).max()),waist_delta_from_parent_rad=float(u[0]-parent[0]),command=u.tolist(),parent_command=parent.tolist(),current=q.tolist(),previous_command=prev.tolist(),predicted_q=v.tolist(),predicted_elbow_gaps_mm=(G.geometry.constraints(v)*1000).tolist(),predicted_inactive_height_mm=scene.details(v)['inactive_z']*1000,scene=scene.record(),independent_stationarity_certificate=False,continuous_path_certificate=False,physical_command_issued=False,training_ready=False)
 result.update(previous_q=qp.tolist(),decay=a.tolist(),causal_bias=bias.tolist(),selected=True,requires_recovery=False,elbow_reserve_m=float(elbow_reserve_m),nominal_predicted_elbow_floor_m=.005+elbow_reserve_m,solver_maxiter=240,solver_ftol=1e-10,objective_scale=1000.,initialization=initialization,original_final_command=final.tolist())
 result['planning_policy']='exact_normal_parent_to_zero_and_original_forecast_nondegradation_v1'
 result['old_height_equality_preserved']=bool(abs(contact_height(u))<=.0002)
 result['old_height_equality_residual_m']=contact_height(u)/1000
 result['observed_vertical_load_n']=load
 result['parent_normal_delta_m']=lower_normal
 result['original_predicted_normal_delta_m']=forecast_limit
 result['nominal_normal_delta_m']=float(normal@displacement(u))
 result['predicted_normal_delta_m']=float(normal@displacement(response(u)))
 result['signed_nominal_xy_m']=(np.array([direction,forward_direction])*displacement(u)[:2]).tolist()
 result['signed_predicted_xy_m']=(np.array([direction,forward_direction])*displacement(response(u))[:2]).tolist()
 result['preliminary_passed']=bool(result['solver_success'] and result['rounded_constraints_passed'] and result['original_command_guard']['accepted'] and result['all_sampled_paths_passed'])
 result['reason']='preliminary_proposal' if result['preliminary_passed'] else 'solver_or_primal_rejected'

 return (u if result['preliminary_passed'] else None),result


def propose(*,normal_nondegradation=False,route_stage=None,**kwargs):
 if type(normal_nondegradation) is not bool:raise ValueError('Explicit bool required')
 if not normal_nondegradation:
  from joint_transport_effective_height_solver_v1 import propose as original
  return original(**kwargs)
 if route_stage!='lateral_y':raise ValueError('Only explicit lateral_y context')
 if kwargs['coordinate']['front_loaded_z_priority']['context']['mode']!='top_push':raise ValueError('Only actual top_push context')
 if kwargs['elbow_reserve_m']!=.0015 or kwargs['quarter_enabled'] is not True:raise ValueError('Only original selected reserve/effective quarter context')
 return _propose_constrained(**kwargs)
