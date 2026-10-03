"""Six real prefixes, explicitly synthetic affine observation continuations.
Independent event audit checks every proposed command and readiness capture.
Actual original ineligible observations must wait without consuming the attempt.
No generated fixture is a physical demonstration or training sample.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,os
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';D=W/'front_bag_recontact_center_draft_r4';B=W/'front_bag_recontact_center_draft_r3';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from front_recontact_center_selection import select_planned
from independent_front_recontact_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();base=json.loads((B/'STATIC_CONTEXT_PROBE.json').read_text());earliest=json.loads((W/'front_bag_recontact_center_draft_r2/STATIC_CONTEXT_PROBE.json').read_text());guard=ClearanceGuard(ROOT,S);parameters=json.loads((S/'causal_response_parameters.json').read_text());a=np.asarray(parameters['tasks']['nudge_mailer_to_bin']['decay']);records=[];negatives=[];sources=dict(base['source_sha256'])
for n,h in sources.items():assert sha(n)==h,n
for p in [Path(__file__),*D.glob('*.py'),D/'COMPONENT_PREPARATION.json',D/'INDEPENDENT_AUDIT_PREPARATION.json',B/'STATIC_CONTEXT_PROBE.json',S/'causal_response_parameters.json']:sources[str(p)]=sha(p)
negative_sample=None;active_sample=None

def save(status,**kw):
 p=D/'LIFECYCLE_STATUS.tmp';p.write_text(json.dumps(dict(status=status,pid=os.getpid(),completed=len(records),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2));p.replace(D/'LIFECYCLE_STATUS.json')
def scene_from(z):return RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
def args(scene,q,qp,prev,t,counter):return dict(step=t,selected=True,parent_mode='top_cross',recontacts=counter,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=a,observed_hand_pose=guard.model.fk(scene.side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
try:
 for original in base['records']:
  t=original['step'];counter=original['recontacts'];q=np.asarray(original['actual_start']);qp=np.asarray(original['previous_q']);prev=np.asarray(original['previous_command']);z=original['planning']['scene'];scene=scene_from(z);save('running',run=original['run'],recontacts=counter)
  p=select_planned(copy.deepcopy(original['planning']),scene,q,step=t,previous_q=qp,previous_command=prev,decay=a,recontact_index=counter);assert p['accepted'];life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=counter);assert life.ready==life.ticks==0 and not life.active
  early=next(r for r in earliest['records'] if r['run']==original['run'] and r['recontacts']==counter);es=scene_from(early['planning']['scene']);ei=args(es,np.asarray(early['actual_start']),np.asarray(early['previous_q']),np.asarray(early['previous_command']),early['step'],counter)
  with patch('front_recontact_center_lifecycle.plan',side_effect=AssertionError('planner called on rejected geometry')):wait=life.update(**ei)
  assert wait['kind']=='unchanged' and wait['reason']=='waiting_for_original_unloaded_geometry' and not life.attempted and not life.active and life.ready==0
  auditor=RecoveryEventAudit(ROOT,S);events=[];checks=[]
  for j in range(241):
   inp=args(scene,q,qp,prev,t+j,counter)
   with patch('front_recontact_center_lifecycle.plan',return_value=copy.deepcopy(p)):event=life.update(**inp)
   assert event['kind'] in ['command','handover'],event
   par=dict(step=t+j,current=q,previous_q=qp,previous_command=prev,final_command=np.asarray(event['command']),scene=z,decay=a,selected=True,parent_mode='top_cross',recontacts=counter,guard_stop=False,observed_load_n=0.,filtered_load_n=0.)
   before=copy.deepcopy(auditor) if event['kind']=='handover' and negative_sample is None else None
   checked=auditor.verify(event,**par);events.append(event);checks.append(checked)
   assert event['context']['recontacts']==counter
   if event['kind']=='handover':
    if negative_sample is None:negative_sample=(before,copy.deepcopy(event),copy.deepcopy(par))
    assert event['measured_ready_count']==3 and life.finished and not life.active
    done=life.update(**args(scene,q,qp,prev,t+j+1,counter));assert done['kind']=='unchanged' and done['reason']=='recovery_handover_already_complete';break
   command=np.asarray(event['command']);bias=q-prev-a*(qp-prev);nq=(1-a)*command+a*q+bias;qp,q,prev=q,nq,command
   if active_sample is None:active_sample=(copy.deepcopy(life),args(scene,q,qp,prev,t+j+1,counter))
  assert events[-1]['kind']=='handover'
  records.append(dict(run=original['run'],step=t,recontacts=counter,unmodified_actual_early_geometry_wait=wait['reason'],selected_plan=p,fixture_observation_scope='First input real; subsequent observations affine synthetic, explicitly not executed',events=events,independent_checks=checks));print(json.dumps(dict(run=original['run'],counter=counter,fixture_commands=len(events),independent_events=len(checks))),flush=True)
 # Mutate handover evidence independently of candidate to exercise rejection.
 for label in ['fake_counter','loaded','wrong_actual_current','wrong_final_command','premature_ready','wrong_vertex','wrong_surface','wrong_inactive_anchor','wrong_normal','missing_consecutive_frame']:
  au,event,par=negative_sample;au=copy.deepcopy(au);event=copy.deepcopy(event);par=copy.deepcopy(par)
  if label=='fake_counter':event['context']['recontacts']+=1
  if label=='loaded':event['context']['observed_load_n']=.1
  if label=='wrong_actual_current':par['current'][0]+=.001
  if label=='wrong_final_command':par['final_command'][0]+=.001
  if label=='premature_ready':event['measured_ready_count']=2
  if label=='wrong_vertex':event['captured_center_local'][0]+=.001
  if label=='wrong_surface':event['selected_surface_local_xy'][0]+=.001
  if label=='wrong_inactive_anchor':event['captured_inactive_anchor_world'][0]+=.001
  if label=='wrong_normal':event['captured_normal_local_up'][0]+=.001
  if label=='missing_consecutive_frame':par['step']+=1;event['context']['step']+=1
  try:au.verify(event,**par)
  except (AssertionError,ValueError):negatives.append(label)
  else:raise AssertionError('tampered event accepted '+label)
 for label in ['guard','loaded_active','counter_changed','mode_changed','observation_gap','budget','object_moved']:
  life,inp=active_sample;life=copy.deepcopy(life);inp=dict(inp)
  if label=='guard':inp['guard_stop']=True
  if label=='loaded_active':inp['observed_load_n']=.01
  if label=='counter_changed':inp['recontacts']+=1
  if label=='mode_changed':inp['parent_mode']='top_push'
  if label=='observation_gap':inp['step']+=1
  if label=='budget':life.ticks=240
  if label=='object_moved':
   zz=inp['scene'].record();zz['target_xyz'][0]+=.003;inp['scene']=scene_from(zz)
  out=life.update(**inp);assert out['kind']=='stop' and out['requires_stop'];negatives.append(label)
 for label,updates in [('disabled',{}),('not_selected',dict(selected=False)),('first_contact',dict(recontacts=0)),('wait_phase',dict(parent_mode='wait'))]:
  inp=dict(active_sample[1]);inp.update(updates);life=FrontRecontactCenterLifecycle(enabled=label!='disabled',recontact_index=inp['recontacts'] or 1);event=life.update(**inp);assert event['kind']=='unchanged' and not life.attempted and life.ready==0;negatives.append(label)
 for value in [0,-1,None,True]:
  try:FrontRecontactCenterLifecycle(recontact_index=value)
  except ValueError:negatives.append('invalid_constructor_'+str(value))
  else:raise AssertionError('invalid recovery accepted')
 assert len(records)==6 and len(negatives)==25
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,records=records,independent_events=sum(len(x['events']) for x in records),handover_fixtures=6,negative_cases=negatives,source_sha256=sources,collector_integrated=False,simulation_started=False,training_ready=False)
 with (D/'LIFECYCLE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
 save('complete',independent_events=out['independent_events'],negative_cases=len(negatives),report_sha256=sha(D/'LIFECYCLE_CHECK.json'))
except Exception as e:save('failed',error=repr(e));raise
