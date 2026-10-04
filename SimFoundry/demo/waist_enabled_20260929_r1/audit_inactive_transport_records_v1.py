"""Independent inactive-transport record and contiguous command-stream verification.
Caller must separately bind actual source, capture selection, scene, raw state and
verified parent intermediate output. No optimizer/runtime/proposer invocation.
This module alone is not a native-file source contract or admission audit.
"""
from pathlib import Path
import numpy as np
from audit_front_recontact_center_events import RecoveryEventAudit

def exact(a,b):
 a,b=np.asarray(a),np.asarray(b)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.array_equal(a,b)

class TransportRecordAudit:
 def __init__(self,root,stage,guard):
  self.root=Path(root);self.stage=Path(stage);self.guard=guard;self.geometry=RecoveryEventAudit(root,stage)
  # Both verifiers reconstruct geometry independently of the candidate solver.
  import importlib.util
  def get(name):
   spec=importlib.util.spec_from_file_location('independent_'+name,self.stage/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
  self.constraints=get('transport_constraint_certificate');self.paths=get('transport_path_certificate')
 def verify(self,record,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,final_command,decay):
  assert type(step) is int and step>=0 and type(selected) is bool and side in ('left','right')
  q,prev,parent,final=[np.asarray(v,float) for v in [current,previous_command,parent_command,final_command]]
  for x in [q,prev,parent,final]:assert x.shape==(11,) and np.isfinite(x).all()
  for x in [prev,parent,final]:exact(x,x.astype(np.float32))
  assert record['version']=='inactive_transport_clearance_bilateral_v1' and record['step']==step and type(record['step']) is int
  assert record['selected'] is selected and type(record['applied']) is bool and record['training_ready'] is False
  exact(record['parent_command'],parent);exact(record['output_command'],final)
  c=record['collector_context'];assert c['side']==side and c['scene']==scene and c['decay']==decay
  exact(c['current'],q);exact(c['previous_command'],prev)
  if previous_q is None:assert step==0 and c['previous_q'] is None
  else:exact(c['previous_q'],previous_q)
  reason=None
  if not selected or step==0:reason='not_captured_front_transport'
  else:
   assert row['step']==coordinate['step']==step and scene['side']==side
   assert coordinate['inactive_transport_clearance']==record
   if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):reason='original_joint_path_has_precedence'
   elif coordinate.get('terminal_joint_hold'):reason='terminal_hold_has_precedence'
   elif row.get('route_stop_reason') or row.get('hand_guard_saturated'):reason='parent_stop_or_guard'
   elif row.get('mode') not in ['top_press','top_push','top_lift','top_cross','top_descend']:reason='not_transport_mode'
   elif coordinate.get('task_inputs') is None or coordinate.get('contact_normal_tracking') is None:reason='missing_original_task_or_normal'
  if reason is not None:
   assert not record['applied'] and record['reason']==reason;exact(parent,final)
  else:
   qp,a=np.asarray(previous_q,float),np.asarray(decay,float)
   assert qp.shape==a.shape==(11,) and np.isfinite(qp).all() and np.isfinite(a).all() and np.all(a>=0) and np.all(a<=.95)
   task=coordinate['task_inputs'];assert np.allclose(task['current'],q,atol=1e-7,rtol=0) and np.allclose(task['previous'],prev,atol=1e-7,rtol=0)
   bias=q-prev-a*(qp-prev);pred=(1-a)*parent+a*q+bias;inactive='right' if side=='left' else 'left'
   minimum=min(self.geometry.hand.minz(z,inactive) for z in [q,parent,pred])
   if minimum>=.8415:
    assert not record['applied'] and record['reason']=='headroom_already_available';exact(parent,final)
   elif record['applied']:
    assert record['reason']=='verified_inactive_only_transport_proposal' and record['full_dynamic_or_task_success'] is False
    assert self.geometry.hand.minz(q,inactive)>=.84-2e-7
    p=record['proposal'];assert p['applied'] is True and p['scene']==scene
    for k,v in [('current',q),('previous_q',qp),('previous_command',prev),('parent_command',parent),('command',final),('decay',a),('causal_bias',bias)]:exact(p[k],v)
    fixed=np.r_[0:6] if side=='left' else np.r_[0,6:11];exact(final[fixed],parent[fixed])
    certificate=self.constraints.verify(p,task,root=self.root,stage=self.stage,guard=self.guard)
    assert certificate['passed'] and record['certificate']==certificate
    for name,end in [('nominal',final),('predicted',np.asarray(p['predicted_q']))]:
     path=self.paths.certify(q,end,scene,model=self.guard.model,audit=self.geometry);assert path['passed'] and record['paths'][name]==path
   else:
    assert record['reason'] in ['no_verified_proposal','independent_constraints_rejected','static_path_rejected'];exact(parent,final)
    # Failed search is not mathematical infeasibility and cannot certify headroom.
    assert isinstance(record.get('proposal'),dict)
    if record['reason']=='independent_constraints_rejected':assert record['certificate']['passed'] is False
    if record['reason']=='static_path_rejected':assert not all(v['passed'] for v in record['paths'].values())
  final_guard=self.guard.command(final,q,prev,first=step==0);assert final_guard['accepted']
  return dict(step=step,applied=record['applied'],reason=record['reason'],final_guard_passed=True,headroom_certified=record['applied'],training_ready=False)

class TransportStreamAudit:
 def __init__(self,record_audit):self.record_audit=record_audit;self.rows=[];self.last_q=None;self.last_u=None
 def observe(self,record,**context):
  assert context['step']==len(self.rows),'missing, repeated, or reordered step'
  if self.rows:
   exact(context['previous_q'],self.last_q);exact(context['previous_command'],self.last_u)
  else:assert context['previous_q'] is None
  result=self.record_audit.verify(record,**context)
  self.rows.append(result);self.last_q=np.array(context['current']).copy();self.last_u=np.array(context['final_command']).copy()
  return result
 def finish(self,expected_frames):
  assert type(expected_frames) is int and expected_frames>0 and len(self.rows)==expected_frames
  return dict(passed=True,frames=len(self.rows),applied=sum(r['applied'] for r in self.rows),rows=self.rows,scope=__doc__,training_ready=False)
