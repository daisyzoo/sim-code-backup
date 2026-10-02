"""Independent full event-stream audit on all fixed rear histories.
Original events remain unchanged. Enabled fixtures attach only previously saved
witnesses, with no pose/action/force edits; they test the auxiliary requirement
on historical paths, not new physics or proof of future recovery success.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_closed_peak_trial_lift_events import EventAudit as OriginalAudit
from audit_rear_corridor_transport_events import EventAudit
from audit_closed_peak_trial_pose_live import loads
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_TRANSPORT_EVENT_CHECK.json';assert not dest.exists();source=W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json';history=json.loads(source.read_text());lookup={(r['episode'],r['step']):r for r in history['rows']};episodes=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text())['episodes'];rows=[];negative=[];sources={};unexecuted=[]
frozen={str(p):sha(p) for p in [Path(__file__),W/'audit_rear_corridor_transport_events.py',W/'audit_rear_transport_witness.py',W/'audit_closed_peak_trial_lift_events.py',W/'audit_closed_peak_trial_pose_live.py',source]}
def save(status,**extra):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,unexecuted_events=unexecuted,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**extra),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in episodes:
  name=item['episode'];ep=W/name;fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};regions={r['step']:r for r in json.loads((ep/'region_approach.json').read_text())['rows']};events=json.loads((ep/'recontact_pose.json').read_text())['rows'];side='right' if 'push_box' in name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];observed=loads(fr['rows'],packets,side,actor)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:pos={k:z[k].astype(float) for k in ['box','mailer']}
  with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].astype(float) for k in ['box','mailer']}
  old=OriginalAudit(ROOT,S);off=EventAudit(ROOT,S);on=EventAudit(ROOT,S);ec=0
  for raw in events:
   t=raw['step']
   if t>=len(q):
    failure=json.loads((ep/'self_clearance.json').read_text())['failure'];assert failure is not None and failure['step']==t;unexecuted.append(dict(episode=name,step=t,kind=raw['kind'],failure=failure['reason']));continue
   if raw['kind'] not in ['command','handover']:
    assert not old.active and not off.active and not on.active
    continue
   event={k:v for k,v in raw.items() if k!='step'};ctx=event['context'];f=fs[t];reg=regions[t];scene=dict(side=side,target_xyz=pos[key][t].tolist(),target_quat=quat[key][t].tolist(),core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],other_xyz=pos[other][t].tolist(),other_quat=quat[other][t].tolist(),other_size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045]);args=dict(step=t,current=q[t],previous_q=q[t-1],previous_command=u[t-1],final_command=u[t],scene=scene,decay=fr['plan']['region_causal_response']['decay'],selected=bool(fr['plan']['rear_joint_xy_progress']['enabled'] and reg['center_local'] is not None),parent_mode=ctx['parent_mode'],recontacts=f['recontacts'],guard_stop=bool(f.get('route_stop_reason') or f.get('release_reason') or reg['abort_reason']),observed_load_n=observed[t][0],filtered_load_n=observed[t][1])
   parent=old.verify(event,**args);disabled=off.verify(event,**args);assert disabled==parent
   modified=copy.deepcopy(event);item=lookup.get((name,t));has_plan=modified.get('planning') is not None and not modified.get('entry_lift_phase')
   if has_plan:assert item and item['planning_witness'];modified['planning']['rear_transport_witness']=item['planning_witness']
   if modified['kind']=='handover':assert item and item['measured_witness'];modified['rear_transport_handover_witness']=item['measured_witness']
   enabled=on.verify(modified,require_rear_transport=True,**args);assert {k:v for k,v in enabled.items() if k not in ['requires_transport','independent_transport']}==parent
   rows.append(dict(episode=name,step=t,kind=event['kind'],entry_lift=bool(event.get('entry_lift_phase')),default_off_exact_equal=True,independent_parent_event=parent,transport=enabled['independent_transport']));ec+=1
   # Check missing mandatory evidence before the parent mutates its path state.
   if has_plan and 'missing_planned_witness' not in negative:
    bad=copy.deepcopy(modified);bad['planning'].pop('rear_transport_witness');fresh=EventAudit(ROOT,S)
    try:fresh.verify(bad,require_rear_transport=True,**args)
    except AssertionError:negative.append('missing_planned_witness')
    else:raise AssertionError('Missing planned witness admitted')
   if modified['kind']=='handover' and 'missing_measured_witness' not in negative:
    bad=copy.deepcopy(modified);bad.pop('rear_transport_handover_witness');fresh=EventAudit(ROOT,S)
    try:fresh.verify(bad,require_rear_transport=True,**args)
    except AssertionError:negative.append('missing_measured_witness')
    else:raise AssertionError('Missing measured witness admitted')
   if len(rows)%100==0:save('running');print('events',len(rows),flush=True)
  assert not old.active and not off.active and not on.active
  for n in ['raw.npz','frontal_bypass.json','region_approach.json','recontact_pose.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz','self_clearance.json']:sources[str(ep/n)]=sha(ep/n)
  save('running');print('episode',name,'events',ec,flush=True)
 assert sum(r['kind']=='handover' for r in rows)==45
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,executed_events=len(rows),measured_handovers=45,planned_direction_witnesses=sum('planned_transport' in r['transport'] for r in rows),measured_direction_witnesses=sum('measured_transport' in r['transport'] for r in rows))
except BaseException as e:save('check_failed',error=repr(e));raise
