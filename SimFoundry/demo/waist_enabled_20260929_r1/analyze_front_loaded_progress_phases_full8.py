"""Allocate measured signed target displacement to logged action intervals.
An increment trace[t+1]-trace[t] is assigned to the command phase logged at t.
This is temporal accounting, not proof of contact or force causality. The final
command has no following observation and is not given fabricated displacement.
"""
from pathlib import Path
import json,hashlib,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;C=W/'front_initial_physical_r1';OUT=W/'FRONT_LOADED_PROGRESS_PHASE_FULL8_DIAGNOSTIC.json';assert not OUT.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source={str(Path(__file__)):sha(__file__)};results=[]
for p in sorted(C.glob('case_*/layout_*/FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json')):
 ep=p.parent;tracking=json.loads(p.read_text());fr=json.loads((ep/'frontal_bypass.json').read_text());by={r['step']:r for r in fr['rows']};direction=fr['plan']['direction'];key='box' if direction==-1 else 'mailer';review=json.loads((ep/'FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json').read_text())
 with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
 dy=direction*np.diff(obj[:,1])*1000;phase=collections.defaultdict(list)
 for t,inc in enumerate(dy):phase[by.get(t,{}).get('mode','no_frontal_row')].append(float(inc))
 total=float(direction*(obj[-1,1]-obj[0,1])*1000);assert abs(sum(sum(v) for v in phase.values())-total)<1e-8
 bouts=[]
 for b in tracking['bouts']:
  first=b['start'];after=min(b['end']+1,len(obj)-1);next_bout=next((x['start'] for x in tracking['bouts'] if x['bout']==b['bout']+1),len(obj)-1)
  bouts.append(dict(bout=b['bout'],start=first,end=b['end'],next_start=next_bout,exit=b['exit_reason'],push_interval_signed_progress_mm=float(direction*(obj[after,1]-obj[first,1])*1000),following_nonpush_signed_progress_mm=float(direction*(obj[next_bout,1]-obj[after,1])*1000),cumulative_progress_at_start_mm=float(direction*(obj[first,1]-obj[0,1])*1000),cumulative_progress_after_push_mm=float(direction*(obj[after,1]-obj[0,1])*1000),load24_mean_N=b['per_action24_load_mean_N']['mean']))
 r=dict(episode=ep.name,task_and_pose_passed=review['original_task_and_pose_passed'],signed_total_mm=total,quality_progress_mm=review['progress_mm'],phase_accounting={k:dict(intervals=len(v),signed_progress_mm=sum(v),positive_mm=sum(x for x in v if x>0),negative_mm=sum(x for x in v if x<0)) for k,v in phase.items()},bouts=bouts)
 results.append(r)
 for f in [p,ep/'frontal_bypass.json',ep/'trace.npz',ep/'FRONT_INITIAL_STAGE_NUMERIC_REVIEW.json']:source[str(f)]=sha(f)
 print(json.dumps(dict(episode=ep.name,passed=r['task_and_pose_passed'],total_mm=total,phase_progress={k:round(v['signed_progress_mm'],3) for k,v in r['phase_accounting'].items()},bouts=[{k:round(v,3) if isinstance(v,float) else v for k,v in b.items() if k in ['bout','push_interval_signed_progress_mm','following_nonpush_signed_progress_mm']} for b in bouts])))
OUT.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=results,source_sha256=source,coverage='8/8 available native-audited pushes; same-run observational comparison only',quality_gates_changed=False,training_ready=False),indent=2))
