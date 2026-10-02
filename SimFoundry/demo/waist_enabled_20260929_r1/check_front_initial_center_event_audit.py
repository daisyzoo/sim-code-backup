"""Independent event audit against explicit causal affine fixture paths.
Initial real observations are source-bound; subsequent q are synthetic, never
physical demonstration or training data. All8 scenes remain in the report.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,copy
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S)
fixture=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';data=json.loads(fixture.read_text());assert data['status']=='complete'
prep=json.loads((S/'PREPARATION.json').read_text());assert json.loads((S/'CHECK.json').read_text())['passed']
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
out=W/'FRONT_INITIAL_CENTER_EVENT_AUDIT_CHECK.json';assert not out.exists();report=dict(status='running',pid=os.getpid(),scope=__doc__,records=[],negative_cases=[],source_sha256={str(p):sha(p) for p in [Path(__file__),W/'audit_front_initial_center_events.py',fixture,S/'PREPARATION.json',S/'CHECK.json']},simulation_started=False,training_ready=False)
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
negative_sample=None
try:
 save()
 for original in data['records']:
  p=original['plan'];z=p['scene'];ctx=original['live_first_event']['context'];q=np.array(ctx['current']);qp=np.array(ctx['previous_q']);prev=np.array(ctx['previous_command']);decay=np.array(ctx['decay']);t=ctx['step'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);life=FrontInitialCenterLifecycle(enabled=True);auditor=EventAudit(ROOT,S)
  checks=[];record=dict(episode=original['episode'],selected=p['accepted'],original_task_passed=original['original_task_passed'],checks=checks);report['records'].append(record);save()
  for j in range(241):
   inp=dict(step=t+j,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=decay,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
   with patch('front_initial_center_lifecycle_v3.plan',return_value=copy.deepcopy(p)):event=life.update(**inp)
   if not p['accepted']:
    assert event['kind']=='unchanged' and not life.active and life.ready==0;record.update(outcome='original_parent_before_any_override',events=0);break
   assert event['kind'] in ('command','handover'),event
   params=dict(step=t+j,current=q,previous_q=qp,previous_command=prev,final_command=np.array(event['command']),scene=z,decay=decay,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.)
   before=copy.deepcopy(auditor) if event['kind']=='handover' and negative_sample is None else None
   checked=auditor.verify(event,**params);checks.append(checked)
   if event['kind']=='handover':
    if negative_sample is None:negative_sample=(before,copy.deepcopy(event),copy.deepcopy(params))
    record.update(outcome='affine_fixture_handover',events=len(checks));break
   command=np.array(event['command']);bias=q-prev-decay*(qp-prev);nq=(1-decay)*command+decay*q+bias;qp,q,prev=q,nq,command
  assert record.get('outcome');print(original['episode'],record['outcome'],record['events'],flush=True);save()
 for label in ['fake_counter','loaded','wrong_actual_current','wrong_final_command','premature_ready','wrong_vertex','wrong_surface','wrong_inactive_anchor','wrong_normal','missing_consecutive_frame']:
  audit,event,params=negative_sample;audit=copy.deepcopy(audit);event=copy.deepcopy(event);params=copy.deepcopy(params)
  if label=='fake_counter':event['context']['recontacts']=1
  if label=='loaded':event['context']['observed_load_n']=.1
  if label=='wrong_actual_current':params['current'][0]+=.001
  if label=='wrong_final_command':params['final_command'][0]+=.001
  if label=='premature_ready':event['measured_ready_count']=2
  if label=='wrong_vertex':event['captured_center_local'][0]+=.001
  if label=='wrong_surface':event['selected_surface_local_xy'][0]+=.001
  if label=='wrong_inactive_anchor':event['captured_inactive_anchor_world'][0]+=.001
  if label=='wrong_normal':event['captured_normal_local_up'][0]+=.001
  if label=='missing_consecutive_frame':params['step']+=1;event['context']['step']+=1
  rejected=False
  try:audit.verify(event,**params)
  except (AssertionError,ValueError):rejected=True
  assert rejected,label;report['negative_cases'].append(dict(case=label,rejected=True))
 report.update(status='complete',passed=True,events=sum(r['events'] for r in report['records']),handover_fixtures=sum(r['outcome']=='affine_fixture_handover' for r in report['records']),parent_fallback=sum(not r['selected'] for r in report['records']));save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
