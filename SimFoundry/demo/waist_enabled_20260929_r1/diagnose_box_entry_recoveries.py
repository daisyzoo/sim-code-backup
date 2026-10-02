"""Descriptive complete-episode recovery/time allocation, no causal or training claim.
Reads actual recorded states/events; loaded is recorded last-substep normal load,
not integrated force. All complete and guarded-short failures remain visible.
"""
from pathlib import Path
import json,sys,hashlib,collections,datetime
import numpy as np
w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
quality=json.loads((ep/'quality.json').read_text());clear=json.loads((ep/'self_clearance.json').read_text());n=quality['frames'];assert n==clear['recorded_frames'] and n<=clear['requested_frames']
fr=json.loads((ep/'frontal_bypass.json').read_text());fs={r['step']:r for r in fr['rows']};ev=json.loads((ep/'recontact_pose.json').read_text())['rows'];es={r['step']:r for r in ev};assert len(fs)==n-1 and len(es)==len(ev);assert sorted(fs)==list(range(1,n))
key='box' if 'push_box' in ep.name else 'mailer';direction=-1 if key=='box' else 1
with np.load(ep/'trace.npz') as z:y=direction*z[key][:,1].astype(float)
assert len(y)==n
buckets=collections.defaultdict(lambda:dict(frames=0,signed_motion_mm=0.));recoveries=collections.defaultdict(list)
for t in range(n):
 f=fs.get(t,dict(mode='initial'));e=es.get(t,{});mode=f['mode']
 if e.get('entry_lift_phase'):label='entry_lift'
 elif e.get('kind') in ['command','handover']:label='original_recontact_path'
 elif mode=='top_push':label='loaded_push' if f['contact_load']['observed_vertical_load_n']>=.3 else 'low_load_push'
 else:label=mode
 buckets[label]['frames']+=1
 if t<n-1:buckets[label]['signed_motion_mm']+=(y[t+1]-y[t])*1000
 if f.get('recontacts',0)>0:recoveries[f['recontacts']].append(t)
assert sum(v['frames'] for v in buckets.values())==n
assert abs(sum(v['signed_motion_mm'] for v in buckets.values())-(y[-1]-y[0])*1000)<1e-7
rows=[]
for k,steps in recoveries.items():
 events=[es[t] for t in steps if t in es];plans=[e for e in events if e.get('planning') is not None];commands=[e for e in events if e.get('kind') in ['command','handover']];lift=[e for e in events if e.get('entry_lift_phase')];handovers=[e['step'] for e in events if e.get('kind')=='handover'];push=[t for t in steps if fs[t]['mode']=='top_push'];blocked=[e for e in events if e.get('reason')=='initial_hand_below_unloaded_planning_height']
 rows.append(dict(recontact=k,start=steps[0],end=steps[-1],entry_lift_frames=len(lift),entry_ready_steps=[e['step'] for e in lift if e['entry_lift_phase']=='lift_ready'],planning=[dict(step=e['step'],entry_lift=bool(e.get('entry_lift_phase')),accepted=e['planning']['accepted']) for e in plans],command_frames=len(commands),handovers=handovers,height_blocked_frames=len(blocked),rejected_entry_attempts=sum('rejected_entry_lift_attempt' in e for e in events),loaded_push_frames=sum(fs[t]['contact_load']['observed_vertical_load_n']>=.3 for t in push),observed_signed_motion_mm=float((y[min(n-1,steps[-1]+1)]-y[steps[0]])*1000),stop_reasons=[e.get('reason') for e in events if e.get('kind')=='stop'],last_event_kind=events[-1]['kind'] if events else None))
files=['raw.npz','trace.npz','quality.json','self_clearance.json','frontal_bypass.json','recontact_pose.json'];out=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=ep.name,frames=n,requested_frames=clear['requested_frames'],quality_passed=quality['passed'],quality_reasons=quality['reasons'],clearance_failure=clear['failure'],progress_mm=float((y[-1]-y[0])*1000),final10_signed_y_min_mm=float(min(y[-10:])*1000),buckets=dict(buckets),recoveries=rows,source_sha256={name:sha(ep/name) for name in files},diagnoser_sha256=sha(__file__),training_ready=False)
(ep/'ENTRY_RECOVERY_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
