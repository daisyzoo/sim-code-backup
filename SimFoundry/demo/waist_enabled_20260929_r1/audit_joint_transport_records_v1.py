"""Independent joint11 record and contiguous emitted-command verification.
No solver/runtime invocation. Caller must bind original source, measured scene,
capture and loaded-Z parent to actual native files. Not training admission.
"""
from pathlib import Path
import importlib.util
import numpy as np

def exact(a,b):
 a,b=np.asarray(a),np.asarray(b)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.array_equal(a,b)

class JointRecordAudit:
 def __init__(self,root,stage,guard):
  self.root=Path(root);self.stage=Path(stage);self.guard=guard
  def get(name):
   spec=importlib.util.spec_from_file_location('independent_'+name,self.stage/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
  self.constraints=get('joint_transport_certificate');self.paths=get('joint_transport_paths').JointTransportPaths(root,stage)
 def verify(self,record,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,final_command,decay):
  assert type(step) is int and step>=0 and type(selected) is bool and side in ('left','right')
  q,prev,parent,final=[np.asarray(v,float) for v in [current,previous_command,parent_command,final_command]]
  for x in [q,prev,parent,final]:assert x.shape==(11,) and np.isfinite(x).all()
  for x in [prev,parent,final]:exact(x,x.astype(np.float32))
  assert record['version']=='joint_transport_clearance_v1' and record['step']==step and type(record['step']) is int
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
   assert coordinate['joint_transport_clearance']==record
   if any(coordinate.get(k) is not None for k in ['front_recontact_center_override','front_initial_center_override','recontact_pose_override']):reason='original_joint_path_has_precedence'
   elif coordinate.get('terminal_joint_hold'):reason='terminal_hold_has_precedence'
   elif row.get('route_stop_reason') or row.get('hand_guard_saturated'):reason='parent_stop_or_guard'
   elif row.get('mode') not in ['top_press','top_push','top_lift','top_cross','top_descend']:reason='not_transport_mode'
   elif coordinate.get('task_inputs') is None or coordinate.get('contact_normal_tracking') is None:reason='missing_original_task_or_normal'
  if reason is None:
   qp,a=np.asarray(previous_q,float),np.asarray(decay,float)
   assert qp.shape==a.shape==(11,) and np.isfinite(qp).all() and np.isfinite(a).all() and np.all(a>=0) and np.all(a<=.95)
   task=coordinate['task_inputs'];assert np.allclose(task['current'],q,atol=1e-7,rtol=0) and np.allclose(task['previous'],prev,atol=1e-7,rtol=0)
   exact(coordinate['front_loaded_z_priority']['output_command'],parent)
   bias=q-prev-a*(qp-prev);pred=(1-a)*parent+a*q+bias;measured=self.paths.margins(q,scene)
   if min(measured)<-2e-7:
    reason='already_below_original_measured_geometry';exact(record['measured_margins_m'],measured)
   elif not self.guard.command(parent,q,prev)['accepted']:reason='parent_original_guard_rejected'
   else:
    def adequate(z):
     margins=self.paths.margins(z,scene);margins[0]-=.0015
     return min(margins)>=0 and np.all(z>=self.guard.lower) and np.all(z<=self.guard.upper)
    if adequate(parent) and adequate(pred):reason='original_predicted_geometry_available'
  if reason is not None:
   assert not record['applied'] and record['reason']==reason;exact(parent,final)
   assert not any(k in record for k in ['proposal','certificate','paths'])
  else:
   assert record['reason'] in ['verified_joint_transport_proposal','no_verified_proposal','independent_constraints_rejected','static_path_rejected']
   p=record['proposal'];assert p['side']==side and p['step']==step and p['scene']==scene
   for k,v in [('current',q),('previous_q',qp),('previous_command',prev),('parent_command',parent),('decay',a),('causal_bias',bias)]:exact(p[k],v)
   u=np.array(p['command']);exact(u,u.astype(np.float32));expected=(1-a)*u+a*q+bias;exact(p['predicted_q'],expected)
   assert p['physical_command_issued'] is False and p['training_ready'] is False
   assert p['initialization']=='actual_same_step_parent_command_only' and p['objective_scale']==1.0
   if record['applied']:
    assert record['reason']=='verified_joint_transport_proposal' and record['full_dynamic_or_task_success'] is False and p['preliminary_passed'] is True and p['solver_success'] is True and p['solver_status']==0
    exact(final,u)
    certificate=self.constraints.verify(p,task,coordinate,guard=self.guard)
    assert certificate['passed'] and record['certificate']==certificate
    for name,end in [('nominal',final),('predicted',expected)]:
     path=self.paths.certify(q,end,scene);assert path['passed'] and record['paths'][name]==path
    assert coordinate['waist_target_rad']==float(final[0])
    assert abs(coordinate['joint_transport_unexecuted_parent_waist_target_rad']-parent[0])<=1e-7
   else:
    exact(parent,final)
    if record['reason']=='no_verified_proposal':assert not p['preliminary_passed']
    elif record['reason']=='independent_constraints_rejected':
     certificate=self.constraints.verify(p,task,coordinate,guard=self.guard);assert not certificate['passed'] and record['certificate']==certificate
    elif record['reason']=='static_path_rejected':
     certificate=self.constraints.verify(p,task,coordinate,guard=self.guard);assert certificate['passed'] and record['certificate']==certificate
     paths={name:self.paths.certify(q,end,scene) for name,end in [('nominal',u),('predicted',expected)]};assert not all(v['passed'] for v in paths.values()) and record['paths']==paths
    else:raise AssertionError('Applied reason with unapplied command')
  final_guard=self.guard.command(final,q,prev,first=step==0);assert final_guard['accepted']
  return dict(step=step,applied=record['applied'],reason=record['reason'],final_guard_passed=True,geometry_certified=record['applied'],training_ready=False)

class JointStreamAudit:
 def __init__(self,record_audit):self.record_audit=record_audit;self.rows=[];self.last_q=None;self.last_u=None
 def observe(self,record,**context):
  assert context['step']==len(self.rows),'missing, repeated, or reordered step'
  if self.rows:
   exact(context['previous_q'],self.last_q);exact(context['previous_command'],self.last_u)
  else:assert context['previous_q'] is None
  result=self.record_audit.verify(record,**context)
  self.rows.append(result);self.last_q=np.array(context['current']).copy();self.last_u=np.array(context['final_command']).copy();return result
 def finish(self,expected_frames):
  assert type(expected_frames) is int and expected_frames>0 and len(self.rows)==expected_frames
  return dict(passed=True,frames=len(self.rows),applied=sum(r['applied'] for r in self.rows),rows=self.rows,scope=__doc__,training_ready=False)
