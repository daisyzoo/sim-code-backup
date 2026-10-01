"""Actual object retreat and loaded yaw demand for current moving-slice trial."""
from pathlib import Path
import json,hashlib,numpy as np
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['rear_core_slice_groups_r1','rear_core_slice_motion_groups_r1']:
 for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
  ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if 'push_box' in task else 'mailer'
  with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  rows=[r for r in fr['rows'] if r.get('rear_cop_centering',{}).get('override')];first=rows[0]['step'];ts=np.array([r['step'] for r in rows]);f=[r['rear_cop_centering'] for r in rows]
  item=dict(run=run,episode=ep.name,actual_overrides=len(rows),first_override=first,object_x_start_m=float(xyz[0,0]),object_x_first_override_m=float(xyz[first,0]),object_x_final_m=float(xyz[-1,0]),post_first_override_object_x_drift_mm=float((xyz[-1,0]-xyz[first,0])*1000),loaded_waist_max_abs_state_rad=float(np.max(abs(q[ts,0]))),loaded_waist_command_at_planning_bound_count=int(np.sum(abs(u[ts,0])>=.98-1e-6)),x_step_at_2mm_bound_count=sum(abs(a['command_delta_x_m'])>=.002-1e-9 for a in f),requested_feed_median_mm=float(np.median([a['feed_x_m'] for a in f])*1000),requested_feed_p95_abs_mm=float(np.percentile(abs(np.array([a['feed_x_m'] for a in f])),95)*1000),source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','frontal_bypass.json']});reports.append(item);print(json.dumps({k:v for k,v in item.items() if k!='source_sha256'}),flush=True)
p=w/'rear_core_slice_motion_groups_r1/REAR_MOTION_DRIFT_DIAGNOSIS.json';assert not p.exists();p.write_text(json.dumps(dict(rows=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual first-to-last post-COP-control objectX and yaw demand. Counts use actual override steps, not all push frames. No proof that feedforward alone caused drift or that every alternate allocation is infeasible; box histories already differed before first override.'),indent=2))
