"""Initial audit parent parity and recovery-normal recapture fixture checks.
Native parent records prove old-path parity only. Affine fixtures and constructed
post-capture normal tasks check bookkeeping/math, not new physical performance.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';D=W/'front_bag_recontact_center_draft_r4';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_drive_1mm_v2_initial_live import verify_files as old_initial
from audit_front_recontact_initial_live import verify_files as new_initial
from audit_front_initial_center_normal import verify_normal_rows as old_normal
from audit_front_recontact_normal_rows import verify_normal_rows as new_normal
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'CAPTURE_AUDIT_PREPARATION.json').read_text());sources={};parents=[];fixtures=[];negative=[];hand=RecoveryEventAudit(ROOT,S).hand
for r in prep['records']:
 p=Path(r['parent']);t=Path(r['target']);assert sha(p)==r['parent_sha256'] and sha(t)==r['target_sha256'];back=t.read_text()
 for e in reversed(r['changes']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'],1)
 assert back==p.read_text();sources[str(p)]=sha(p);sources[str(t)]=sha(t)
for run in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';old=old_initial(ep);new=new_initial(ep,verified_recovery_events={});assert old==new
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 co=json.loads((ep/'coordination.json').read_text());ex={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());stream=json.loads((ep/'front_initial_center.json').read_text());ev={r['step']:{k:v for k,v in r.items() if k!='step'} for r in stream['rows'] if r['kind'] in ('command','handover')};top={r['step'] for r in fr['rows']}
 a=old_normal(q,co,ex,top,{},hand,'left',verified_front_events=ev);b=new_normal(q,co,ex,top,{},hand,'left',verified_front_events=ev);assert a==b
 parents.append(dict(run=run,frames=len(co),native_initial_exact=True,native_normal_exact=True));print('parent native exact',run,flush=True)
 for p in [ep/'raw.npz',ep/'coordination.json',ep/'expert_control.json',ep/'frontal_bypass.json',ep/'front_initial_center.json']:sources[str(p)]=sha(p)
base=json.loads((D/'LIFECYCLE_CHECK.json').read_text())
for f in base['records']:
 events=copy.deepcopy(f['events']);end=events[-1]['context']['step'];n=end+22;q=np.zeros((n,11));coordinates=[];experts={t:dict(mode='top_lift') for t in range(n)};ev={};last=events[-1]
 for e in events:
  t=e['context']['step'];q[t]=e['context']['current'];e['real_recontact_index']=f['recontacts'];ev[t]=e
 for t in range(1,n):
  if t in ev:
   e=ev[t];experts[t]['mode']='top_press' if e['kind']=='handover' else 'top_cross';row=dict(step=t,controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=e,contact_normal_tracking=None,task_inputs=None)
  elif t>end:
   q[t]=q[end];experts[t]['mode']='top_push';current=hand.fk(q[t],'left')[2,:3];anchor=np.array(last['captured_normal_local_up']);h=1e-6;J=np.empty((3,11))
   for j in range(11):
    delta=np.zeros(11);delta[j]=h;J[:,j]=.15*(hand.fk(q[t]+delta,'left')[2,:3]-hand.fk(q[t]-delta,'left')[2,:3])/(2*h)
   row=dict(step=t,contact_normal_tracking=dict(current_local_up=current.tolist(),target_local_up=anchor.tolist(),error=(.15*np.clip(.72*(anchor-current),-.1,.1)).tolist(),angle_error_rad=float(np.arccos(np.clip(current@anchor,-1,1))),weight_m=.15,jacobian=J.tolist()))
  else:row=dict(step=t,contact_normal_tracking=None)
  coordinates.append(row)
 out=new_normal(q,coordinates,experts,set(range(1,n)),{},hand,'left',verified_front_recovery_events=ev);assert out['measured_recapture_steps']==[end] and out['normal_frames']==21 and out['jacobian_samples']>=1
 fixtures.append(dict(run=f['run'],recontacts=f['recontacts'],unloaded_commands=len(events),post_capture_normal_frames=out['normal_frames'],jacobian_samples=out['jacobian_samples']))
 if len(fixtures)==1:
  for label in ['missing_admitted_event','stale_normal_anchor','competing_initial_path','false_counter','right_side','fake_controller','bad_jacobian']:
   cc=copy.deepcopy(coordinates);ee=copy.deepcopy(ev);side='left'
   if label=='missing_admitted_event':ee.pop(next(iter(ee)))
   elif label=='stale_normal_anchor':cc[end]['contact_normal_tracking']['target_local_up'][0]+=.001
   elif label=='competing_initial_path':cc[events[0]['context']['step']-1]['front_initial_center_override']={}
   elif label=='false_counter':ee[next(iter(ee))]['real_recontact_index']+=1
   elif label=='right_side':side='right'
   elif label=='fake_controller':cc[events[0]['context']['step']-1]['controller_kind']='fake'
   elif label=='bad_jacobian':cc[next(t for t in range(end+1,n) if t%20==0)-1]['contact_normal_tracking']['jacobian'][0][0]+=.001
   try:new_normal(q,cc,experts,set(range(1,n)),{},hand,side,verified_front_recovery_events=ee)
   except (AssertionError,ValueError,KeyError):negative.append(label)
   else:raise AssertionError('bad normal stream accepted '+label)
for p in [Path(__file__),S/'CAPTURE_AUDIT_PREPARATION.json',D/'LIFECYCLE_CHECK.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,native_parent_parity=parents,affine_normal_fixtures=fixtures,negative_cases=negative,source_sha256=sources,full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'CAPTURE_AUDIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parent_frames=sum(r['frames'] for r in parents),normal_fixture_count=len(fixtures),negative=len(negative))))
