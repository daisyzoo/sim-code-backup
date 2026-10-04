"""Default-off, currently unwired, inactive-right5 transport refinement.
Call only after original parent refinements and before original final command
guard. No joint-path takeover, capture/reset, object or anchor writes. Failed
refinement returns the original command without certifying it as successful.
"""
import numpy as np
from inactive_transport_clearance import propose
from transport_constraint_certificate import verify
from transport_path_certificate import certify
from audit_front_recontact_center_events import RecoveryEventAudit

class InactiveTransportRuntime:
 def __init__(self,guard,root,stage,*,enabled=False):
  if type(enabled) is not bool:raise ValueError('Explicit boolean required')
  self.guard=guard;self.root=root;self.stage=stage;self.enabled=enabled
  self.audit=RecoveryEventAudit(root,stage) if enabled else None
 def refine(self,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,decay):
  parent=np.asarray(parent_command,float)
  if parent.shape!=(11,) or not np.isfinite(parent).all() or not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Invalid emitted parent')
  if type(step) is not int or step<0 or type(selected) is not bool:raise ValueError('Invalid step or selection')
  meta=dict(step=step,selected=selected,applied=False,version='inactive_transport_clearance_v1',parent_command=parent.tolist(),output_command=parent.tolist(),training_ready=False)
  def original(reason,**kw):return parent.copy(),dict(meta,reason=reason,**kw)
  if not self.enabled:return original('disabled')
  if not selected or side!='left' or step==0:return original('not_captured_front_bag')
  if not isinstance(row,dict) or not isinstance(coordinate,dict) or row.get('step')!=step or coordinate.get('step')!=step:raise ValueError('Missing current records')
  if scene.side!=side:raise ValueError('Scene side mismatch')
  if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):return original('original_joint_path_has_precedence')
  if coordinate.get('terminal_joint_hold'):return original('terminal_hold_has_precedence')
  if row.get('route_stop_reason') or row.get('hand_guard_saturated'):return original('parent_stop_or_guard')
  if row.get('mode') not in ['top_press','top_push','top_lift','top_cross','top_descend']:return original('not_transport_mode')
  task=coordinate.get('task_inputs')
  if task is None or coordinate.get('contact_normal_tracking') is None:return original('missing_original_task_or_normal')
  q,qp,prev,a=[np.asarray(v,float) for v in [current,previous_q,previous_command,decay]]
  if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,qp,prev,a]):raise ValueError('Invalid actual context')
  if not np.allclose(task['current'],q,atol=1e-7,rtol=0) or not np.allclose(task['previous'],prev,atol=1e-7,rtol=0):raise ValueError('Original task is stale')
  # Early unchanged is only a decision not to refine, never an admission pass.
  bias=q-prev-a*(qp-prev);pred=(1-a)*parent+a*q+bias
  if min(self.audit.hand.minz(z,'right') for z in [q,parent,pred])>=.8415:return original('headroom_already_available')
  command,proposal=propose(enabled=True,selected=True,mode=row['mode'],guard_stop=False,scene=scene,current=q,previous_q=qp,previous_command=prev,parent_command=parent,decay=a,task_inputs=task)
  if command is None:return original('no_verified_proposal',proposal=proposal)
  certificate=verify(proposal,task,root=self.root,stage=self.stage,guard=self.guard)
  if not certificate['passed']:return original('independent_constraints_rejected',proposal=proposal,certificate=certificate)
  paths={name:certify(q,end,scene.record(),model=self.guard.model,audit=self.audit) for name,end in [('nominal',command),('predicted',np.array(proposal['predicted_q']))]}
  if not all(p['passed'] for p in paths.values()):return original('static_path_rejected',proposal=proposal,certificate=certificate,paths=paths)
  assert np.array_equal(command[:6],parent[:6])
  return command,dict(meta,applied=True,reason='verified_inactive_only_transport_proposal',proposal=proposal,certificate=certificate,paths=paths,output_command=command.tolist(),full_dynamic_or_task_success=False)
