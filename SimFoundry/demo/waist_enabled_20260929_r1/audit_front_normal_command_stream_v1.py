"""Verify transport and final normal records against one actual emitted history.
Intermediate transport commands are verified but never become next-frame history.
Caller must independently bind source, scene, selection and loaded-Z math to raw.
This module alone does not certify a physical rollout or training admission.
"""
import copy
import numpy as np
from audit_effective_height_transport_records_v1 import JointRecordAudit,exact
from audit_front_normal_command_record_v1 import NormalCommandAuditor

class FinalCommandStreamAudit:
 def __init__(self,root,stage,guard,*,enabled,effective_quarter_height):
  assert type(enabled) is bool
  self.enabled=enabled;self.guard=guard
  self.transport=JointRecordAudit(root,stage,guard,effective_quarter_height=effective_quarter_height)
  self.normal=NormalCommandAuditor(guard,root,stage)
  self.rows=[];self.last_q=None;self.last_u=None
 def observe(self,transport_record,normal_record,*,step,selected,side,row,coordinate,scene,current,previous_q,previous_command,parent_command,executed_command,decay):
  assert type(step) is int and step==len(self.rows),'missing, repeated, or reordered step'
  if step:
   exact(previous_q,self.last_q)
   assert np.array_equal(previous_command,self.last_u),'previous_command_is_not_last_emitted_command'
  else:
   assert previous_q is None
   exact(previous_command,np.zeros(11));exact(current,np.zeros(11));exact(executed_command,np.zeros(11))
  intermediate=transport_record['output_command'];parent_coord=coordinate
  if self.enabled:
   assert normal_record is not None
   if coordinate is not None:
    assert coordinate['front_normal_nondegradation']==normal_record,'normal coordination mismatch'
   if normal_record['applied']:
    assert coordinate is not None
    exact(coordinate['waist_target_rad'],float(np.asarray(executed_command)[0]))
    old_waist=coordinate['normal_planning_unexecuted_parent_waist_target_rad']
    assert abs(old_waist-intermediate[0])<=1e-7,'wrong unexecuted waist target'
    parent_coord=copy.deepcopy(coordinate);parent_coord['waist_target_rad']=old_waist
   elif coordinate is not None:
    assert 'normal_planning_unexecuted_parent_waist_target_rad' not in coordinate
  else:
   assert normal_record is None
   if coordinate is not None:
    assert 'front_normal_nondegradation' not in coordinate
    assert 'normal_planning_unexecuted_parent_waist_target_rad' not in coordinate
  old=self.transport.verify(transport_record,step=step,selected=selected,side=side,row=row,coordinate=parent_coord,scene=None if scene is None else scene.record(),current=current,previous_q=previous_q,previous_command=previous_command,parent_command=parent_command,final_command=intermediate,decay=decay)
  if self.enabled:
   new=self.normal.verify(normal_record,step=step,enabled=True,selected=selected,side=side,row=row,coordinate=coordinate,scene=scene,current=current,previous_q=previous_q,previous_command=previous_command,parent_command=intermediate,executed_command=executed_command,decay=decay)
  else:
   exact(executed_command,intermediate);new=dict(passed=True,applied=False,requires_recovery=False)
  assert self.guard.command(executed_command,current,previous_command,first=step==0)['accepted']
  result=dict(step=step,passed=True,transport_applied=old['applied'],normal_applied=new['applied'],requires_recovery=new.get('requires_recovery',False),final_guard_passed=True,training_ready=False)
  # Atomic history update: no rejected record can advance the stream.
  self.last_q=np.asarray(current).copy();self.last_u=np.asarray(executed_command).copy();self.rows.append(result)
  return result
 def finish(self,expected_frames):
  assert type(expected_frames) is int and expected_frames>0 and expected_frames==len(self.rows)
  return dict(passed=True,frames=len(self.rows),transport_applied=sum(r['transport_applied'] for r in self.rows),normal_applied=sum(r['normal_applied'] for r in self.rows),recovery_requests=sum(r['requires_recovery'] for r in self.rows),actual_final_history_preserved=True,rows=self.rows,training_ready=False)
