"""Descriptive first hard rear-box comparison; full-run audits still pending.
Phase attribution uses recorded pre-action trace[t+1]-trace[t], only t1..1198.
Original full1200-frame quality supplies terminal metrics. No admission/causality.
"""
from pathlib import Path
import hashlib,json,datetime,collections
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[];sources={str(Path(__file__)):sha(__file__)}
for run in ['front_corridor_midpoint_physical_r1','rear_waypoint_physical_r2']:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';files=[ep/n for n in ['raw.npz','trace.npz','quality.json','frontal_bypass.json','self_clearance.json']];before={str(p):sha(p) for p in files};q=json.loads((ep/'quality.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];sc=json.loads((ep/'self_clearance.json').read_text());assert q['frames']==sc['recorded_frames']==sc['requested_frames']==1200 and len(fr)==1199
 with np.load(ep/'trace.npz') as z:box=z['box'].astype(float)
 assert len(box)==1200
 modes=collections.Counter(r['mode'] for r in fr);exits=collections.Counter(r['last_recontact_reason'] for previous,r in zip(fr,fr[1:]) if previous['mode']=='top_push' and r['mode']!='top_push');phase={}
 for mode in modes:
  tt=[r['step'] for r in fr if r['mode']==mode and r['step']<1199];dy=np.asarray([-(box[t+1,1]-box[t,1])*1000 for t in tt]);phase[mode]=dict(intervals=len(tt),signed_y_progress_mm=float(dy.sum()),mean_signed_y_mm_per_control_interval=float(dy.mean()) if len(dy) else None)
 result=dict(run=run,quality_passed=q['passed'],final_progress_mm=q['metrics']['target_final_progress_m']*1000,non_target_max_xy_mm=q['metrics']['mailer_max_xy_m']*1000,mode_frames=dict(modes),push_exit_reasons=dict(exits),phase_motion=phase,full_audit_and_actual_visual_status='pending_for_new_run')
 if run=='rear_waypoint_physical_r2':
  p=ep/'rear_waypoint_reconciliation.json';data=json.loads(p.read_text());result['reconciliation_keys']=list(data);result['reconciliation_rows']=len(data['rows']);result['applied_events']=sum(x.get('applied') is True for x in data['rows']);before[str(p)]=sha(p)
 for name,h in before.items():assert sha(name)==h
 sources.update(before);rows.append(result)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,conclusion='Candidate first hard rear box fails and progresses less despite more top_push frames and fewer tilt exits. Reducing exit frequency is not task success.',source_sha256=sources,training_ready=False,full_run_complete=False)
with (W/'rear_waypoint_physical_r2/FIRST_REAR_BOX_FAILURE_COMPARISON.json').open('x') as f:json.dump(out,f,indent=2)
for r in rows:print(json.dumps(r))
