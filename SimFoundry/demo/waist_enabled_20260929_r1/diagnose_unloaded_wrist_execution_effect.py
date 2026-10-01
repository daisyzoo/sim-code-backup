"""Observed wrist-prior executions plus fixed-state original-command comparison.
Counterfactual baseline solves do not predict a trajectory. Record actual next q,
contact modes and pre-first-application repeatability; do not sum one-step gains
into a claimed episode-level causal effect.
"""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_unloaded_wrist_prior';sys.path[:0]=[str(stage),str(repo)]
from task_ik import solve
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);out=[]
for ep in sorted((w/'unloaded_wrist_prior_groups_r1').glob('case_*/layout_*')):
 if 'wait' in ep.name or not (ep/'quality.json').exists():continue
 qual=json.loads((ep/'quality.json').read_text());assert qual['frames']==1200
 cs=json.loads((ep/'coordination.json').read_text());fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};wi=10 if 'push_box' in ep.name else 5
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 rows=[];excluded=collections.Counter();fallback=collections.Counter()
 for c in cs:
  t=c['step'];r=c['self_clearance_task'].get('unloaded_wrist_prior')
  if r is None:continue
  if not r['eligible']:
   for k,v in r['gates'].items():
    if not v:excluded[k]+=1
   continue
  if not r['applied']:fallback[r['fallback_reason']]+=1;continue
  inp=c['task_inputs'];prior=np.array(inp['preferred_step']);prior[wi]=0.;baseline,meta=solve(enabled=True,geometry=guard.geometry,**dict(inp,preferred_step=prior.tolist()));assert not c.get('region_joint_override') and not c.get('terminal_joint_hold')
  candidate=np.array(r['attempted_command']);assert np.max(abs(candidate-u[t]))<2e-7
  rows.append(dict(step=t,mode=fr[t]['mode'],measured_min_z_m=r['context']['min_hand_z_m'],requested_wrist_step=r['prior_wrist_step_rad'],original_command_available=baseline is not None,wrist_reduction_vs_original_command_rad=None if baseline is None else float(abs(baseline[wi])-abs(candidate[wi])),actual_command_wrist_reduction_rad=float(abs(q[t,wi])-abs(u[t,wi])),actual_next_state_wrist_reduction_rad=float(abs(q[t,wi])-abs(q[t+1,wi])) if t+1<len(q) else None,actual_pre_wrist_rad=float(q[t,wi]),actual_next_wrist_rad=float(q[t+1,wi]) if t+1<len(q) else None))
 old=w/'rear_short_recovery_groups_r1'/ep.parent.name/ep.name;repeat=None
 if rows:
  with np.load(old/'raw.npz') as z:oldq=z['q'][:,12:23].astype(float)
  first=min(r['step'] for r in rows);delta=np.max(abs(q[:first]-oldq[:first]),axis=1);repeat=dict(first_applied_step=first,first_pre_application_q_difference_step=next((i for i,x in enumerate(delta) if x>1e-8),None),max_pre_application_q_difference_rad=float(max(delta)))
 valid=[x for x in rows if x['original_command_available']];summary=dict(applied_frames=len(rows),fallback_counts=dict(fallback),excluded_gate_counts=dict(excluded),median_wrist_reduction_vs_original_command_rad=float(np.median([x['wrist_reduction_vs_original_command_rad'] for x in valid])) if valid else None,actual_next_wrist_reducing_frames=sum(x['actual_next_state_wrist_reduction_rad'] is not None and x['actual_next_state_wrist_reduction_rad']>0 for x in rows),actual_next_wrist_increasing_frames=sum(x['actual_next_state_wrist_reduction_rad'] is not None and x['actual_next_state_wrist_reduction_rad']<0 for x in rows),median_actual_next_state_wrist_reduction_rad=float(np.median([x['actual_next_state_wrist_reduction_rad'] for x in rows if x['actual_next_state_wrist_reduction_rad'] is not None])) if rows else None,original_quality_passed=qual['passed'],progress_mm=qual['metrics']['target_final_progress_m']*1000)
 item=dict(episode=ep.name,summary=summary,pre_application_repeatability=repeat,rows=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json','quality.json']},parent_raw_sha256=sha(old/'raw.npz'));out.append(item);print(ep.name,json.dumps(summary),json.dumps(repeat),flush=True)
(w/'UNLOADED_WRIST_EXECUTION_EFFECT.json').write_text(json.dumps(dict(scope=__doc__,episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'task_ik.py',stage/'clearance_runtime.py',stage/'unloaded_wrist_task.py']},training_ready=False),indent=2))
