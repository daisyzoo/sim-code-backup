"""Default-off joint11 transport refinement. Original path/stop precedence.
No object, contact anchor or state mutation. Rejection returns the parent without
certifying that parent as safe; original final guard remains authoritative.
"""
import numpy as np
from joint_transport_solver import propose
from joint_transport_certificate import verify
from joint_transport_paths import JointTransportPaths
from functools import partial
from joint_transport_effective_height_solver_v1 import propose as effective_propose
from joint_transport_effective_height_certificate_v1 import verify as effective_verify
SPEC=dict(version='joint_transport_clearance_reserve_v1',enabled=True,measured_inactive_floor_m=.84,nominal_predicted_floor_m=.8415,hand_parcel_gap_m=.01,elbow_gap_m=.005,nominal_predicted_elbow_gap_m=.0065,elbow_reserve_m=.0015,solver_objective_scale=1000.,solver_maxiter=240,solver_ftol=1e-10,stationarity_max=1e-6,parent_active_linear_height_preserved=True,original_normal_non_degradation=True,original_joint_path_priority=True,static_path_not_dynamic_certificate=True,training_ready=False)
class JointTransportRuntime:
 def __init__(self,guard,root,stage,*,enabled=False,effective_quarter_height=False):
  if type(enabled) is not bool or type(effective_quarter_height) is not bool:raise ValueError('Explicit booleans required')
  if effective_quarter_height and not enabled:raise ValueError('Effective target requires enabled transport')
  self.effective_quarter_height=effective_quarter_height
  self._propose=partial(effective_propose,quarter_enabled=True) if effective_quarter_height else propose
  self._verify=partial(effective_verify,quarter_enabled=True) if effective_quarter_height else verify
  self.guard=guard;self.enabled=enabled;self.paths=JointTransportPaths(root,stage) if enabled else None
 def refine(self,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,decay):
  parent=np.asarray(parent_command,float)
  if parent.shape!=(11,) or not np.isfinite(parent).all() or not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Invalid emitted parent')
  if type(step) is not int or step<0 or type(selected) is not bool:raise ValueError('Invalid step or selection')
  meta=dict(step=step,selected=selected,applied=False,version=SPEC['version'],parent_command=parent.tolist(),output_command=parent.tolist(),training_ready=False)
  if self.effective_quarter_height:meta.update(version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True)
  def original(reason,**kw):return parent.copy(),dict(meta,reason=reason,**kw)
  if not self.enabled:return original('disabled')
  if not selected or side not in ('left','right') or step==0:return original('not_captured_front_transport')
  if not isinstance(row,dict) or not isinstance(coordinate,dict) or row.get('step')!=step or coordinate.get('step')!=step:raise ValueError('Missing current records')
  if scene.side!=side:raise ValueError('Scene side mismatch')
  if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):return original('original_joint_path_has_precedence')
  if coordinate.get('terminal_joint_hold'):return original('terminal_hold_has_precedence')
  if row.get('route_stop_reason') or row.get('hand_guard_saturated'):return original('parent_stop_or_guard')
  if row.get('mode') not in ['top_press','top_push','top_lift','top_cross','top_descend']:return original('not_transport_mode')
  task=coordinate.get('task_inputs')
  if task is None or coordinate.get('contact_normal_tracking') is None:return original('missing_original_task_or_normal')
  q,qp,prev,a=[np.asarray(v,float) for v in [current,previous_q,previous_command,decay]]
  if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,qp,prev,a]) or np.any(a<0) or np.any(a>.95):raise ValueError('Invalid actual context')
  if not np.allclose(task['current'],q,atol=1e-7,rtol=0) or not np.allclose(task['previous'],prev,atol=1e-7,rtol=0):raise ValueError('Original task is stale')
  if coordinate.get('front_loaded_z_priority',{}).get('output_command')!=parent.tolist():raise ValueError('Unbound loaded-Z parent')
  measured=self.paths.margins(q,scene.record())
  if min(measured)<-2e-7:return original('already_below_original_measured_geometry',measured_margins_m=measured.tolist())
  if not self.guard.command(parent,q,prev)['accepted']:return original('parent_original_guard_rejected')
  bias=q-prev-a*(qp-prev);pred=(1-a)*parent+a*q+bias
  def adequate(z):
   data=scene.details(z)
   return data['inactive_z']>=.8415 and min(data['gaps'][k] for k in ['inactive_target','inactive_other','active_other'])>=.01 and min(self.guard.geometry.constraints(z))>=.0065 and np.all(z>=self.guard.lower) and np.all(z<=self.guard.upper)
  if adequate(parent) and adequate(pred):return original('original_predicted_geometry_available')
  command,proposal=self._propose(step=step,side=side,scene=scene,current=q,previous_q=qp,previous_command=prev,parent_command=parent,decay=a,coordinate=coordinate,elbow_reserve_m=.0015)
  if command is None:return original('no_verified_proposal',proposal=proposal)
  certificate=self._verify(proposal,task,coordinate,guard=self.guard,elbow_reserve_m=.0015)
  if not certificate['passed']:return original('independent_constraints_rejected',proposal=proposal,certificate=certificate)
  paths={name:self.paths.certify(q,end,scene.record()) for name,end in [('nominal',command),('predicted',np.array(proposal['predicted_q']))]}
  if not all(p['passed'] for p in paths.values()):return original('static_path_rejected',proposal=proposal,certificate=certificate,paths=paths)
  return command,dict(meta,applied=True,reason='verified_joint_transport_proposal',proposal=proposal,certificate=certificate,paths=paths,output_command=command.tolist(),full_dynamic_or_task_success=False)
