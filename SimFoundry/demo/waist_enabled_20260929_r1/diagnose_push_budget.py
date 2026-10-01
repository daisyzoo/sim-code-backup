"""Actual frame/motion allocation; loaded means observed last-substep vertical load.
Progress assigned to a command phase is descriptive, not force integration or
proof of that phase causing motion. Original1200 budget and all gates unchanged.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();episodes=[]
for run in ['precise_interior_groups_r1','parent_seed_groups_r1']:
 r=w/run;protocol=json.loads((r/'PROTOCOL.json').read_text())
 for item in protocol['commands']:
  if item['wait']:continue
  for task in item['tasks']:
   ep=r/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
   if not (ep/'quality.json').exists():continue
   quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
   fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};ex={x['step']:x for x in json.loads((ep/'expert_control.json').read_text())};events=json.loads((ep/'recontact_pose.json').read_text())['rows'];recovery={x['step'] for x in events if x['kind'] in ['command','handover']};first=min(t for t,f in fs.items() if f['mode']=='top_push');key='box' if 'push_box' in task else 'mailer';direction=-1 if key=='box' else 1
   with np.load(ep/'trace.npz') as z:y=direction*z[key][:,1].astype(float)
   assert sorted(ex)==list(range(1200));assert all(f['mode']==ex[t]['mode'] for t,f in fs.items());buckets=collections.defaultdict(lambda:dict(frames=0,observed_signed_motion_mm=0.,forward_motion_mm=0.,backward_motion_mm=0.))
   for t in range(1200):
    if t<first:label='before_first_push'
    elif t in recovery:label='verified_unloaded_recovery'
    elif fs[t]['mode']=='top_push':label='push_observed_loaded' if fs[t]['contact_load']['observed_vertical_load_n']>=.3 else 'push_observed_low_load'
    else:label='other_'+fs[t]['mode']
    b=buckets[label];b['frames']+=1
    if t<1199:
     dy=(y[t+1]-y[t])*1000;b['observed_signed_motion_mm']+=dy;b['forward_motion_mm']+=max(0.,dy);b['backward_motion_mm']+=max(0.,-dy)
   total=(y[-1]-y[0])*1000;assert abs(sum(b['observed_signed_motion_mm'] for b in buckets.values())-total)<1e-7;assert sum(b['frames'] for b in buckets.values())==1200
   row=dict(run=run,episode=ep.name,first_push_step=first,original_passed=quality['passed'],signed_initial_y_mm=y[0]*1000,required_progress_mm=max(150.,200.-y[0]*1000),observed_signed_progress_mm=total,remaining_position_deficit_mm=max(0.,200.-y[-1]*1000),buckets=dict(buckets),source_sha256={n:sha(ep/n) for n in ['trace.npz','quality.json','frontal_bypass.json','expert_control.json','recontact_pose.json']});episodes.append(row);print(run,ep.name,round(total,3),{k:v['frames'] for k,v in buckets.items()},flush=True)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=episodes,source_sha256={str(Path(__file__)):sha(Path(__file__))},training_ready=False);(w/'PUSH_BUDGET_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2))
