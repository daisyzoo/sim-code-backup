"""Replay fixed recorded geometry, not a closed-loop or physical outcome."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/tmp')
from front_clearance_hysteresis_candidate import FrontClearanceProgress
p=Path(sys.argv[1]);d=json.loads((p/'frontal_bypass.json').read_text());rows=d['rows'];first_y=d['plan']['initial_target_xyz'][1];clear=d['plan']['front_route_live_guards']['clearance_before_lateral_m'];result=[]
for band in (0.,.0005,.001):
 state=FrontClearanceProgress(clear,first_y,confirm_nominal_clearance=True,recovery_hysteresis_m=band);front=0;front_push=0;changes=0;last=None;mismatch=[]
 for r in rows:
  if r.get('route_stop_reason'):break
  v=state.update(r['measured_front_gap_m'],r['observed_target'][1]);front+=v['route_stage']=='front_x';front_push+=v['route_stage']=='front_x' and r['mode']=='top_push'
  if v['route_stage']!=last:changes+=1;last=v['route_stage']
  if band==0 and (v['route_stage']!=r['route_stage'] or v['clearance_recovery_count']!=r['clearance_progress']['clearance_recovery_count']):mismatch.append(r['step'])
 assert not mismatch,mismatch
 result.append(dict(hysteresis_m=band,recover_threshold_m=clear-band,recoveries=state.recoveries,front_frames_on_fixed_geometry=front,front_push_frames_on_fixed_geometry=front_push,stage_changes=changes))
out=dict(results=result,candidate_sha256=hashlib.sha256(Path('/tmp/front_clearance_hysteresis_candidate.py').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),scope='Frozen recorded geometry/loads; no updated physics or action rollout. Baseline stage/count must match exactly. Fewer replay switches does NOT predict actual safety, progress, visibility or task success. Proposed1mm hysteresis recovers below11mm, original10mm emergency remains unchanged in future controller integration; not wired.',training_ready=False)
(p/'RECOVERY_HYSTERESIS_SHADOW.json').write_text(json.dumps(out,indent=2));print(json.dumps(result,indent=2))
