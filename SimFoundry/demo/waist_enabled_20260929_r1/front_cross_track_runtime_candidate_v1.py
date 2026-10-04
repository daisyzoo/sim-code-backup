"""Uninstalled final front lateral correction, explicit None on unsafe fallback.
The original transport action is an input, not silently replaced history.
Caller must stop BEFORE emitting when output is None. Default off is identity.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from loaded_z_priority_checks import support_point
from joint_transport_paths import JointTransportPaths
from front_cross_track_nonreversal_solver_candidate_v1 import propose
from audit_front_cross_track_certificate_v2 import verify

class FrontCrossTrackNonreversal:
 def __init__(self,guard,root,stage,*,enabled=False):
  if type(enabled) is not bool:raise ValueError('Explicit enable boolean required')
  self.guard=guard;self.enabled=enabled;self.paths=JointTransportPaths(root,stage) if enabled else None
 def refine(self,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,decay):
  parent=np.asarray(parent_command,dtype=float)
  if parent.shape!=(11,) or not np.isfinite(parent).all() or not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Invalid float32 final parent')
  if type(step) is not int or step<0 or type(selected) is not bool:raise ValueError('Invalid step/selection')
  base=dict(step=step,selected=selected,enabled=self.enabled,applied=False,requires_stop=False,parent_command=parent.tolist(),output_command=parent.tolist(),training_ready=False)
  def same(reason,**extra):return parent.copy(),dict(base,reason=reason,**extra)
  def reject(reason,**extra):return None,dict(base,reason=reason,requires_stop=True,output_command=None,**extra)
  if not self.enabled:return same('disabled')
  if not selected or step==0:return same('not_captured_front')
  if not isinstance(row,dict) or not isinstance(coordinate,dict) or row.get('step')!=step or coordinate.get('step')!=step:raise ValueError('Missing current records')
  if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):return same('original_joint_path_precedence')
  if coordinate.get('terminal_joint_hold'):return same('terminal_precedence')
  if row.get('route_stop_reason') or row.get('hand_guard_saturated'):return same('original_stop_precedence')
  if row['mode']!='top_push' or row.get('route_stage')!='lateral_y':return same('outside_lateral_push')
  if side not in ['left','right'] or scene is None or scene.side!=side:raise ValueError('Invalid front side/scene')
  old=coordinate['joint_transport_clearance'];task=coordinate['task_inputs'];z=coordinate['front_loaded_z_priority'];tc=old['collector_context']
  if old['output_command']!=parent.tolist() or old['parent_command']!=z['output_command']:raise ValueError('Unbound original command chain')
  q=np.asarray(current,float);prev=np.asarray(previous_command,float)
  if not np.array_equal(q,tc['current']) or not np.array_equal(prev,tc['previous_command']) or not np.array_equal(previous_q,tc['previous_q']) or not np.array_equal(decay,tc['decay']) or scene.record()!=tc['scene']:raise ValueError('Stale original physical context')
  xr=0 if side=='left' else 3;request=float(task['error'][xr]);direction=float(np.sign(request))
  if direction==0:return same('zero_x_request')
  normal=Rotation.from_quat(scene.record()['target_quat']).as_matrix()[:,2];center=np.array(coordinate['active_support_reference']['center_local']);reference=support_point(self.guard.model,q,side,normal,center);dx=float(support_point(self.guard.model,parent,side,normal,center)[0]-reference[0]);signed=direction*dx
  observation=dict(axis=0,requested_direction=direction,requested_dx_m=request,parent_nominal_dx_m=dx,parent_signed_dx_m=signed,rounding_tolerance_m=2e-7)
  if signed>=-2e-7:return same('already_nonreversing',observation=observation)
  if min(self.paths.margins(q,scene.record())) < -2e-7:return reject('reversing_parent_measured_geometry_invalid',observation=observation)
  if not self.guard.command(parent,q,prev)['accepted']:return reject('reversing_parent_original_guard_rejected',observation=observation)
  command,proposal=propose(step=step,side=side,scene=scene,current=q,previous_q=previous_q,previous_command=prev,parent_command=np.array(z['output_command']),decay=decay,coordinate=coordinate,elbow_reserve_m=.0015,quarter_enabled=True,cross_track_nonreversal=True,route_stage='lateral_y')
  if command is None:return reject('no_verified_nonreversing_proposal',observation=observation,proposal=proposal)
  cert=verify(proposal,task,coordinate,guard=self.guard,elbow_reserve_m=.0015,quarter_enabled=True)
  if not cert['passed']:return reject('independent_nonreversal_certificate_rejected',observation=observation,proposal=proposal,certificate=cert)
  proofs={name:self.paths.certify(q,end,scene.record()) for name,end in [('nominal',command),('predicted',np.array(proposal['predicted_q']))]}
  if not all(p['passed'] for p in proofs.values()):return reject('nonreversing_static_path_rejected',observation=observation,proposal=proposal,certificate=cert,paths=proofs)
  if not self.guard.command(command,q,prev)['accepted']:return reject('nonreversing_final_guard_rejected',observation=observation,proposal=proposal,certificate=cert,paths=proofs)
  return command,dict(base,applied=True,reason='verified_nonreversing_command',output_command=command.tolist(),observation=observation,proposal=proposal,certificate=cert,paths=proofs)
