"""Initial audit parent parity and recovery-normal recapture fixture checks.
Native parent records prove old-path parity only. Affine fixtures and constructed
post-capture normal tasks check bookkeeping/math, not new physical performance.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_recenter_v3';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_recontact_headroom_normal_rows import verify_normal_rows as old_normal
from audit_front_box_recenter_a2_normal_rows import verify_normal_rows as new_normal
sys.path.insert(0,str(D))
from audit_front_box_recenter_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};parents=[];fixtures=[];negative=[];hand=RecoveryEventAudit(ROOT,W/'staged_front_recontact_headroom').hand
bound=json.loads((S/'INDEPENDENT_STREAM_CHECK.json').read_text());assert bound['passed']
for p,h in bound['source_sha256'].items():assert sha(p)==h,p
for side,case,task in [('left',840023,'nudge_mailer_to_bin'),('right',840020,'push_box_to_bin')]:
 ep=W/'front_corridor_midpoint_physical_r1'/f'case_{case}'/f'layout_{case}_{task}'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 co=json.loads((ep/'coordination.json').read_text());ex={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());stream=json.loads((ep/'front_initial_center.json').read_text());ev={r['step']:{k:v for k,v in r.items() if k!='step'} for r in stream['rows'] if r['kind'] in ('command','handover')};top={r['step'] for r in fr['rows']}
 a=old_normal(q,co,ex,top,{},hand,side,verified_front_events=ev);b=new_normal(q,co,ex,top,{},hand,side,verified_front_events=ev);assert a==b
 parents.append(dict(episode=ep.name,side=side,frames=len(co),native_normal_exact=True));print('parent native exact',ep.name,flush=True)
 for p in [ep/'raw.npz',ep/'coordination.json',ep/'expert_control.json',ep/'frontal_bypass.json',ep/'front_initial_center.json']:sources[str(p)]=sha(p)
base=json.loads((D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json').read_text())
for f in [r for r in base['records'] if r['counter'] in (2,6,12)]:
 events=copy.deepcopy(f['events']);end=events[-1]['context']['step'];n=end+22;q=np.zeros((n,11));coordinates=[];experts={t:dict(mode='top_lift') for t in range(n)};ev={};last=events[-1]
 for e in events:
  t=e['context']['step'];q[t]=e['context']['current'];e['real_recontact_index']=f['counter'];e['front_box_recenter_version']='front_box_recenter_v1';ev[t]=e
 for t in range(1,n):
  if t in ev:
   e=ev[t];experts[t]['mode']='top_press' if e['kind']=='handover' else 'top_cross';row=dict(step=t,controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=e,contact_normal_tracking=None,task_inputs=None)
  elif t>end:
   q[t]=q[end];experts[t]['mode']='top_push';current=hand.fk(q[t],'right')[2,:3];anchor=np.array(last['captured_normal_local_up']);h=1e-6;J=np.empty((3,11))
   for j in range(11):
    delta=np.zeros(11);delta[j]=h;J[:,j]=.15*(hand.fk(q[t]+delta,'right')[2,:3]-hand.fk(q[t]-delta,'right')[2,:3])/(2*h)
   row=dict(step=t,contact_normal_tracking=dict(current_local_up=current.tolist(),target_local_up=anchor.tolist(),error=(.15*np.clip(.72*(anchor-current),-.1,.1)).tolist(),angle_error_rad=float(np.arccos(np.clip(current@anchor,-1,1))),weight_m=.15,jacobian=J.tolist()))
  else:row=dict(step=t,contact_normal_tracking=None)
  coordinates.append(row)
 out=new_normal(q,coordinates,experts,set(range(1,n)),{},hand,'right',verified_front_recovery_events=ev);assert out['measured_recapture_steps']==[end] and out['normal_frames']==21 and out['jacobian_samples']>=1
 fixtures.append(dict(run='front_corridor_midpoint_physical_r1',recontacts=f['counter'],unloaded_commands=len(events),post_capture_normal_frames=out['normal_frames'],jacobian_samples=out['jacobian_samples']))
 if len(fixtures)==1:
  for label in ['missing_admitted_event','stale_normal_anchor','competing_initial_path','false_counter','wrong_side','missing_right_marker','fake_controller','bad_jacobian']:
   cc=copy.deepcopy(coordinates);ee=copy.deepcopy(ev);side='right'
   if label=='missing_admitted_event':ee.pop(next(iter(ee)))
   elif label=='stale_normal_anchor':cc[end]['contact_normal_tracking']['target_local_up'][0]+=.001
   elif label=='competing_initial_path':cc[events[0]['context']['step']-1]['front_initial_center_override']={}
   elif label=='false_counter':ee[next(iter(ee))]['real_recontact_index']+=1
   elif label=='wrong_side':side='left'
   elif label=='missing_right_marker':
    for e in ee.values():e.pop('front_box_recenter_version')
   elif label=='fake_controller':cc[events[0]['context']['step']-1]['controller_kind']='fake'
   elif label=='bad_jacobian':cc[next(t for t in range(end+1,n) if t%20==0)-1]['contact_normal_tracking']['jacobian'][0][0]+=.001
   try:new_normal(q,cc,experts,set(range(1,n)),{},hand,side,verified_front_recovery_events=ee)
   except (AssertionError,ValueError,KeyError):negative.append(label)
   else:raise AssertionError('bad normal stream accepted '+label)
for p in [W/'audit_front_box_recenter_a2_normal_rows.py',W/'audit_front_recontact_headroom_normal_rows.py',S/'INDEPENDENT_STREAM_CHECK.json',Path(__file__),S/'AUDIT_FAMILY_V2_PREPARATION.json',D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,native_parent_parity=parents,affine_normal_fixtures=fixtures,negative_cases=negative,source_sha256=sources,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'NORMAL_CAPTURE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parent_frames=sum(r['frames'] for r in parents),normal_fixture_count=len(fixtures),negative=len(negative))))
