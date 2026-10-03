"""Independent recovery stream binding to actual frames, counters and commands.
No candidate planner/runtime imports. Native-file entry requires full original
horizon and source binding; stream fixtures alone are not physical evidence.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
from audit_front_recontact_center_events import RecoveryEventAudit
from audit_front_initial_center_planning_v2 import SelectionAudit
from audit_unloaded_wrist_prior_live import near
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class RecoveryStreamAudit:
 def __init__(self,repo,stage):
  self.repo=repo;self.stage=stage;self.counter=0;self.last_step=0;self.audit=None
  self.selection=SelectionAudit(repo,stage);self.attempted=False;self.finished=False
  self.center=None;self.normal=None;self.anchor=None;self.rows=[];self.preflights=[];self.handovers=[]
 def observe(self,event,row,coordinate,*,step,current,previous_q,previous_command,final_command,scene,decay,observed_load_n,filtered_load_n):
  assert type(step) is int and step==self.last_step+1
  count=row.get('recontacts',self.counter);assert type(count) is int and count in (self.counter,self.counter+1)
  if count!=self.counter:
   assert self.audit is None or not self.audit.active,'counter changed while active'
   self.counter=count;self.audit=RecoveryEventAudit(self.repo,self.stage);self.attempted=self.finished=False
  self.last_step=step
  assert event['real_recontact_index']==count and event['kind'] in ('unchanged','command','handover')
  guard=bool(row.get('route_stop_reason') or row.get('release_reason'));has_load='contact_load' in row
  context=event.get('context');planning=event.get('planning');active=bool(self.audit and self.audit.active)
  if context is not None:
   assert context['step']==step and context['scene']==scene and context['selected'] is True and context['recontacts']==count
   assert context['guard_stop'] is False and not guard
   for k,v in [('current',current),('previous_q',previous_q),('previous_command',previous_command),('decay',decay)]:near(context[k],v,1e-7)
   near(context['observed_load_n'],observed_load_n,1e-12);near(context['filtered_load_n'],filtered_load_n,1e-12)
   near(context['observed_hand_pose'],self.selection.hand.fk(current,'left'),1e-4);near(context['observed_inactive_hand_pose'],self.selection.hand.fk(current,'right'),1e-4)
  if planning is not None:
   assert count>0 and not self.attempted and not self.finished and not active and not guard and has_load
   assert context is not None and context['parent_mode'] in ('top_cross','top_descend')
   assert observed_load_n==0 and 0<=filtered_load_n<=.05
   self.attempted=True
   result=self.selection.verify_selection(planning,current=current,previous_q=previous_q,previous_command=previous_command,decay=decay,scene=scene,step=step)
   self.preflights.append(dict(step=step,recontacts=count,**result))
  kind=event['kind']
  if kind in ('command','handover'):
   assert count>0 and not self.finished and has_load and not guard
   assert coordinate['controller_kind']=='verified_unloaded_front_recontact_joint_path' and coordinate['front_recontact_center_override']==event
   assert coordinate.get('front_initial_center_override') is None and coordinate.get('recontact_pose_override') is None and not coordinate.get('terminal_joint_hold')
   out=self.audit.verify(event,step=step,current=current,previous_q=previous_q,previous_command=previous_command,final_command=final_command,scene=scene,decay=decay,selected=True,parent_mode=context['parent_mode'],recontacts=count,guard_stop=guard,observed_load_n=observed_load_n,filtered_load_n=filtered_load_n)
   assert coordinate['active_side']=='left' and coordinate['bounded_solver'] is True
   near(coordinate['upper_q'],current,1e-7)
   for key in ['task_inputs','contact_normal_tracking','contact_bout_yaw_tracking']:assert coordinate[key] is None
   assert not coordinate.get('region_joint_override') and not coordinate.get('joint_edge_refinement',{}).get('override') and not coordinate.get('front_loaded_z_priority',{}).get('applied')
   assert row['mode']==('top_press' if kind=='handover' else 'top_cross')
   assert row['front_recontact_center_phase']==('measured_handover' if kind=='handover' else 'tracking')
   assert row['contact_load']['applied_z_bias_m']==row['contact_load']['stored_z_bias_m']==0
   self.rows.append(dict(recontacts=count,**out))
   if kind=='handover':
    self.finished=True;self.center=list(event['captured_center_local']);self.normal=list(event['captured_normal_local_up']);self.anchor=list(event['captured_inactive_anchor_world']);self.handovers.append(dict(step=step,recontacts=count))
  else:
   assert not active,'missing command in active recovery'
   assert coordinate.get('front_recontact_center_override') is None and coordinate.get('controller_kind')!='verified_unloaded_front_recontact_joint_path'
   reason=event['reason']
   if count==0:assert reason=='first_contact_remains_original' and planning is None
   elif guard:assert reason=='parent_guard_has_precedence' and planning is None
   elif not has_load:assert reason=='no_measured_load_record' and planning is None
   elif self.finished:assert reason=='recovery_handover_already_complete' and planning is None
   elif row['mode'] not in ('top_cross','top_descend'):assert reason=='not_initial_front_unloaded_phase' and planning is None
   elif planning is not None:assert planning['accepted'] is False and reason=='no_verified_initial_plan'
   elif self.attempted or observed_load_n!=0 or not 0<=filtered_load_n<=.05:assert reason=='no_new_unloaded_initial_attempt'
   else:
    assert reason=='waiting_for_original_unloaded_geometry' and context is not None
    geometry,_=self.selection.geometry(current,scene);assert geometry['accepted'] is False
  if self.center is None:
   assert event['center_local_after'] is None and 'front_recontact_captured_center_local' not in row
  else:
   near(event['center_local_after'],self.center,0);near(row['front_recontact_captured_center_local'],self.center,0)
   near(coordinate['inactive_anchor'],self.anchor,1e-9)
   pose=self.selection.hand.fk(current,'left');R=pose[:3,:3];normal=Rotation.from_quat(scene['target_quat']).as_matrix()[:,2];nl=R.T@normal;verts=self.selection.hand.vertices['left'];center=np.array(self.center);ref=center+nl*(min(verts@nl)-center@nl)
   near(row['projected_support_reference']['center_local'],center,0);near(row['projected_support_reference']['reference_local'],ref,2e-6);near(row['control_offset_local'],ref,2e-6)
   if row['mode'] in ('top_lift','top_cross','top_descend','top_press','top_push') and kind=='unchanged':
    assert coordinate['contact_normal_tracking'] is not None;near(coordinate['contact_normal_tracking']['target_local_up'],self.normal,2e-6)
  return True
 def finish(self):
  assert self.audit is None or not self.audit.active,'unfinished front recovery path'
  return dict(passed=True,verified_commands=len(self.rows),handovers=len(self.handovers),rows=self.rows,preflights=self.preflights,recovery_handovers=self.handovers,training_ready=False)

def unique(rows):
 d={r['step']:r for r in rows};assert len(d)==len(rows);return d

def verify_files(ep):
 ep=Path(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
 assert task in ('wait_no_package','push_box_to_bin','nudge_mailer_to_bin');n=70 if task=='wait_no_package' else 1200
 assert q.shape==u.shape==(n,11) and np.isfinite(q).all() and np.isfinite(u).all() and max(abs(q[0]))==max(abs(u[0]))==0
 data=json.loads((ep/'front_recontact_center.json').read_text());events=unique(data['rows'])
 if task=='wait_no_package':
  assert data['selected'] is False and not events
  return dict(passed=True,wait=True,selected=False,verified_commands=0,handovers=0,rows=[],training_ready=False)
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows=unique(fr['rows']);coords=unique(json.loads((ep/'coordination.json').read_text()));experts=unique(json.loads((ep/'expert_control.json').read_text()))
 assert sorted(rows)==sorted(coords)==list(range(1,n)) and sorted(experts)==list(range(n))
 selected=bool(task=='nudge_mailer_to_bin' and fr['plan'].get('front_route_selected'));assert data['selected'] is selected
 if not selected:
  assert not events and all(c.get('controller_kind')!='verified_unloaded_front_recontact_joint_path' and c.get('front_recontact_center_override') is None for c in coords.values())
  return dict(passed=True,wait=False,selected=False,verified_commands=0,handovers=0,rows=[],training_ready=False)
 assert sorted(events)==list(range(1,n));clear=json.loads((ep/'self_clearance.json').read_text());assert clear['failure'] is None and clear['recorded_frames']==clear['requested_frames']==n
 with np.load(ep/'trace.npz') as z:target=z['mailer'].astype(float);other=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'].astype(float);oq=z['box'].astype(float)
 for x,size in [(target,3),(other,3),(tq,4),(oq,4)]:assert x.shape==(n,size) and np.isfinite(x).all()
 core=fr['plan']['front_initial_center_landing']['actual_core']['collision_core_size_xyz'];decay=json.loads((S/'causal_response_parameters.json').read_text())['tasks'][task]['decay']
 packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];p={x['after_action_step']:x for x in packets};assert len(p)==len(packets) and sorted(p)==list(range(n))
 checker=RecoveryStreamAudit(ROOT,S);filtered=0.
 for t in range(1,n):
  row=rows[t];coordinate=coords[t];event={k:v for k,v in events[t].items() if k!='step'}
  measured=sum(abs(float(c['force_world_N'][2])) for c in p[t-1]['parcel_contacts'] if any('left_wrist_roll' in name for name in c['shapes']) and any('/mailer/' in name for name in c['shapes']))
  if 'contact_load' in row:
   filtered=.25*measured+.75*filtered;near(row['contact_load']['observed_vertical_load_n'],measured,1e-10);near(row['contact_load']['filtered_vertical_load_n'],filtered,1e-10)
  scene=dict(side='left',target_xyz=target[t].tolist(),target_quat=tq[t].tolist(),core_size=core,other_xyz=other[t].tolist(),other_quat=oq[t].tolist(),other_size=[.14,.09,.045])
  checker.observe(event,row,coordinate,step=t,current=q[t],previous_q=q[t-1],previous_command=u[t-1],final_command=u[t],scene=scene,decay=decay,observed_load_n=measured,filtered_load_n=filtered)
  near(experts[t]['target_xyz'],row['target_xyz'],2e-6);assert experts[t]['mode']==row['mode']
 return dict(checker.finish(),selected=True,wait=False)

def audit(ep):
 from front_recontact_stage_source_binding import verify_observation_binding
 ep=Path(ep).resolve();binding=verify_observation_binding(ep);out=verify_files(ep)
 names=['raw.npz','front_recontact_center.json','frontal_bypass.json','coordination.json','expert_control.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','self_clearance.json']
 out.update(source_binding=binding,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),*[ep/n for n in names if (ep/n).exists()],W/'audit_front_recontact_center_events.py',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_preflight.py']})
 return out
if __name__=='__main__':
 ep=Path(sys.argv[1]);out=audit(ep)
 with (ep/'FRONT_RECONTACT_STREAM_AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
 print(dict(passed=out['passed'],commands=out['verified_commands'],handovers=out['handovers']))
