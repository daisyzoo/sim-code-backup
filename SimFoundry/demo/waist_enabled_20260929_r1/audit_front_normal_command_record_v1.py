"""Independent final normal-planning record consumer; never invokes optimizer.
Caller binds actual raw history, scene and preceding verified transport output.
Preserves independent original mathematical/continuous-path/final-command gates.
No full-body dynamics, task quality or training-admission claim.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation
from independent_cross_track_assets_v1 import independent_hand_model
from audit_front_exact_normal_planning_v1 import verify as verify_certificate
from joint_transport_paths import JointTransportPaths

def finite(x):
 if isinstance(x,dict):
  for v in x.values():finite(v)
 elif isinstance(x,(list,tuple)):
  for v in x:finite(v)
 elif isinstance(x,(float,np.floating)):assert math.isfinite(x),'nonfinite record'

def near(a,b,tol=1e-12):
 a=np.asarray(a,float);b=np.asarray(b,float);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=tol

class NormalCommandAuditor:
 def __init__(self,guard,root,stage):
  self.guard=guard;self.hand=independent_hand_model(guard);self.paths=JointTransportPaths(root,stage)
 def verify(self,r,*,step,enabled,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,executed_command,decay):
  finite(r);assert type(enabled) is bool and type(selected) is bool and type(step) is int
  assert type(r['step']) is int and r['step']==step and r['enabled'] is enabled and r['selected'] is selected
  assert r['training_ready'] is False and r['requires_stop'] is False
  for k in ['applied','requires_recovery']:assert type(r[k]) is bool
  q=np.asarray(current,float);u=np.asarray(executed_command,float);prev=np.asarray(previous_command,float);parent=np.asarray(parent_command,float)
  for v in [q,u,prev,parent]:assert v.shape==(11,) and np.isfinite(v).all()
  near(r['parent_command'],parent,0);near(r['output_command'],u,0);near(u,u.astype(np.float32),0)
  def unchanged(reason):
   assert r['reason']==reason and r['applied'] is False and r['requires_recovery'] is False
   assert 'recovery_transition' not in r and 'recovery_committed' not in r
   near(u,parent,0);return dict(passed=True,step=step,applied=False,reason=reason,training_ready=False)
  if not enabled:return unchanged('disabled')
  if not selected or step==0:return unchanged('not_captured_front')
  assert row['step']==coordinate['step']==step
  if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):return unchanged('original_joint_path_precedence')
  if coordinate.get('terminal_joint_hold'):return unchanged('terminal_precedence')
  if row.get('route_stop_reason') or row.get('hand_guard_saturated'):return unchanged('original_stop_precedence')
  if row['mode']!='top_push' or row.get('route_stage')!='lateral_y':return unchanged('outside_lateral_push')
  assert side in ('left','right') and scene.side==side
  old=coordinate['joint_transport_clearance'];z=coordinate['front_loaded_z_priority'];tc=old['collector_context'];task=coordinate['task_inputs']
  near(old['output_command'],parent,0);near(old['parent_command'],z['output_command'],0)
  assert tc['scene']==scene.record();near(tc['current'],q,0);near(tc['previous_q'],previous_q,0);near(tc['previous_command'],prev,0);near(tc['decay'],decay,0)
  requested=float(task['error'][0 if side=='left' else 3]);direction=float(np.sign(requested))
  if direction==0:return unchanged('zero_x_request')
  normal=Rotation.from_quat(tc['scene']['target_quat']).as_matrix()[:,2];center=np.asarray(coordinate['active_support_reference']['center_local'])
  def point(v):
   T=self.hand.fk(v,side);n=T[:3,:3].T@normal;off=center+n*(min(self.hand.vertices[side]@n)-center@n);return T[:3,3]+T[:3,:3]@off
  origin=point(q);dx=float(point(parent)[0]-origin[0]);signed=direction*dx
  obs=r['observation'];assert obs['axis']==0 and obs['rounding_tolerance_m']==2e-7
  for k,v in [('requested_direction',direction),('requested_dx_m',requested),('parent_nominal_dx_m',dx),('parent_signed_dx_m',signed)]:near(obs[k],v,2e-12)
  if signed>=-2e-7:return unchanged('already_nonreversing')
  assert r['applied'] is True and self.guard.command(parent,q,prev)['accepted']
  assert min(self.paths.margins(q,tc['scene']))>=-2e-7
  p=r['proposal'];assert p['step']==step and p['side']==side and p['training_ready'] is False and p['physical_command_issued'] is False
  load=z['context']['observed_vertical_load_n'];assert math.isfinite(load)
  inward=float(normal@(point(np.asarray(z['output_command']))-origin))
  a=np.asarray(decay,float);qp=np.asarray(previous_q,float);forecast=(1-a)*u+a*q+q-prev-a*(qp-prev)
  if r['requires_recovery']:
   assert load<.3 or inward>=0.,'unjustified recovery of valid loaded inward parent'
   assert p['requires_recovery'] is True and p['command'] is None
   near(p['observed_vertical_load_n'],load,0);near(p['parent_normal_delta_m'],inward,2e-12)
   assert r['reason']=='verified_hold_then_original_recontact' and r['recovery_committed'] is True
   near(u,q.astype(np.float32),0);near(r['predicted_q'],forecast)
   request=r['recovery_request'];event=r['recovery_transition']
   assert request['source_step']==event['step']==step and request['side']==side
   assert request['reason']==event['reason']=='front_nonreversing_contact_recovery'
   near(request['observed_support_xyz'],row['observed_support_xyz'],0);near(request['observed_support_xyz'],origin,2e-6);near(event['observed_support_xyz'],request['observed_support_xyz'],0)
   assert event['before']['top_mode']=='top_push' and event['before']['recontacts']==row['recontacts']
   assert event['after']==dict(top_mode='top_lift',recontacts=row['recontacts']+1,lost_contact_steps=0)
   proof=None
  else:
   assert load>=.3 and inward<0 and p['requires_recovery'] is False
   assert r['reason']=='verified_exact_normal_nondegrading_command' and 'recovery_transition' not in r and 'recovery_committed' not in r
   assert p['solver_success'] is True and type(p['solver_status']) is int and p['solver_status']==0
   assert type(p['iterations']) is int and 0<p['iterations']<=240
   assert p['solver_maxiter']==240 and p['solver_ftol']==1e-10 and p['objective_scale']==1000.
   assert p['planning_policy']=='exact_normal_parent_to_zero_and_original_forecast_nondegradation_v1' and p['old_height_equality_preserved'] is False
   for k,v in [('command',u),('current',q),('previous_q',qp),('previous_command',prev),('decay',a),('parent_command',z['output_command']),('original_final_command',parent)]:near(p[k],v,0)
   assert p['scene']==tc['scene'];near(p['predicted_q'],forecast)
   proof=verify_certificate(u,coordinate,guard=self.guard)
   assert proof['passed'] is True and r['certificate']['passed'] is True
   near(proof['certificate']['stationarity_residual'],r['certificate']['certificate']['stationarity_residual'],1e-12)
  paths={name:self.paths.certify(q,end,tc['scene']) for name,end in [('nominal',u),('predicted',forecast)]}
  assert all(v['passed'] for v in paths.values()) and all(r['paths'][k]['passed'] is True for k in paths)
  final=self.guard.command(u,q,prev);assert final['accepted']
  return dict(passed=True,step=step,applied=True,requires_recovery=r['requires_recovery'],certificate=proof,paths=paths,final_guard=final,training_ready=False)
