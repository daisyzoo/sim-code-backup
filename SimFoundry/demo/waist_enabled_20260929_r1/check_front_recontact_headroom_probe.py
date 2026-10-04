"""Probe six preselected1mm-headroom recorded prefixes with new isolated lifecycle.
Only first state/history/load are recorded; subsequent affine observations are
hypothetical, not a simulator rollout. Original independent event gates apply.
"""
from pathlib import Path
import datetime,hashlib,json,os,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';D=W/'front_bag_recontact_headroom_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from front_recontact_center_tracking import propose
from front_initial_center_plan import checked_scene
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());guard=ClearanceGuard(ROOT,S);decay=np.asarray(read(S/'causal_response_parameters.json')['tasks']['nudge_mailer_to_bin']['decay']);report=read(W/'front_recontact_physical_r1/FIRST_RECONTACT_STOP_DIAGNOSIS.json');bases=read(W/'front_bag_recontact_center_draft_r2/STATIC_CONTEXT_PROBE.json')['records'];records=[];sources={str(p):sha(p) for p in [Path(__file__),D/'PREPARATION.json',S/'causal_response_parameters.json',W/'front_recontact_physical_r1/FIRST_RECONTACT_STOP_DIAGNOSIS.json',*D.glob('*.py')]}
def sc(z):return RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
def args(scene,q,qp,prev,step,counter,mode='top_cross',filtered=0.):return dict(step=step,selected=True,parent_mode=mode,recontacts=counter,guard_stop=False,observed_load_n=0.,filtered_load_n=filtered,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=decay,observed_hand_pose=guard.model.fk('left',q)[0],observed_inactive_hand_pose=guard.model.fk('right',q)[0])
def save(status,**kw):
 p=D/'PROBE_STATUS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),completed=len(records),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2));tmp.replace(p)
try:
 actual=read(W/'front_recontact_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin/front_recontact_center.json');event=next(r for r in actual['rows'] if r['kind']=='command');c=event['context'];scene=sc(c['scene']);life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=1);wait=life.update(**args(scene,np.array(c['current']),np.array(c['previous_q']),np.array(c['previous_command']),c['step'],1,c['parent_mode'],c['filtered_load_n']));assert wait['reason']=='waiting_for_inactive_hand_planning_headroom' and not life.attempted and not life.active
 rejected,proof=propose(enabled=True,selected=True,mode='top_cross',recontacts=1,observed_load_n=0.,filtered_load_n=c['filtered_load_n'],current=np.array(c['current']),previous_q=np.array(c['previous_q']),previous_command=np.array(c['previous_command']),waypoint=event['proposal']['waypoint'],decay=decay,guard=guard,scene_check=lambda q:checked_scene(scene,q));assert rejected is None and not proof['applied'];np.testing.assert_array_equal(proof['candidate_command'],event['command'])
 for record in report['recorded_old_window_headroom']:
  counter=record['recontacts'];step=next(x['first_step'] for x in record['thresholds'] if x['additional_entry_headroom_mm']==1.);assert step is not None
  ep=W/record['run']/'case_840023/layout_840023_nudge_mailer_to_bin';fr=read(ep/'frontal_bypass.json');row=next(r for r in fr['rows'] if r['step']==step);assert row['recontacts']==counter and row['contact_load']['observed_vertical_load_n']==0
  with np.load(ep/'raw.npz') as z:q=z['q'][step,12:23].astype(float);qp=z['q'][step-1,12:23].astype(float);prev=z['action'][step-1,12:23].astype(float)
  z=dict(next(x for x in bases if x['run']==record['run'] and x['recontacts']==counter)['planning']['scene'])
  with np.load(ep/'trace.npz') as a:z.update(target_xyz=a['mailer'][step].tolist(),other_xyz=a['box'][step].tolist())
  with np.load(ep/'parcel_orientation.npz') as a:z.update(target_quat=a['mailer'][step].tolist(),other_quat=a['box'][step].tolist())
  scene=sc(z);initial=checked_scene(scene,q);assert initial['accepted'] and initial['inactive_lowest_z_m']>=.841;life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=counter);audit=RecoveryEventAudit(ROOT,S);events=[];checks=[];save('running',run=record['run'],counter=counter,step=step)
  for j in range(241):
   inp=args(scene,q,qp,prev,step+j,counter,row['mode'] if j==0 else 'top_cross',row['contact_load']['filtered_vertical_load_n'] if j==0 else 0.);e=life.update(**inp);events.append(e)
   if e['kind'] not in ('command','handover'):break
   cmd=np.asarray(e['command']);checked=audit.verify(e,step=step+j,current=q,previous_q=qp,previous_command=prev,final_command=cmd,scene=z,decay=decay,selected=True,parent_mode=inp['parent_mode'],recontacts=counter,guard_stop=False,observed_load_n=0.,filtered_load_n=inp['filtered_load_n']);checks.append(checked)
   assert e['proposal']['nominal_scene']['inactive_lowest_z_m']>=.8405 and e['proposal']['predicted_scene']['inactive_lowest_z_m']>=.8405
   if e['kind']=='handover':assert e['measured_ready_count']==3;break
   bias=q-prev-decay*(qp-prev);pred=(1-decay)*cmd+decay*q+bias;qp,q,prev=q,pred,cmd
  rec=dict(run=record['run'],counter=counter,preselected_first_step=step,initial_geometry=initial,outcome=events[-1]['kind'],reason=events[-1].get('reason'),events=events,independent_checks=checks,synthetic_future=True);records.append(rec);print(json.dumps({k:rec[k] for k in ['run','counter','preselected_first_step','outcome','reason']}),flush=True)
  for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']:sources[str(ep/n)]=sha(ep/n)
 passed=all(r['outcome']=='handover' for r in records);out=dict(passed=passed,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,failed_physical_entry_waits_without_attempt=True,failed_physical_first_command_now_rejected=True,records=records,independent_event_count=sum(len(r['independent_checks']) for r in records),source_sha256=sources,collector_integrated=False,simulation_started=False,training_ready=False)
 with (D/'PROBE_RESULT.json').open('x') as f:json.dump(out,f,indent=2)
 save('complete',passed=passed,affine_handovers=sum(r['outcome']=='handover' for r in records));print(json.dumps(dict(passed=passed,records=len(records),events=out['independent_event_count'])))
except Exception as e:save('failed',error=repr(e));raise
