"""Compare recorded first-chunk predictions to zero-start expert timelines."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'demo/recovery_protocol_20260928_r1'
rows=json.loads((out/'failure_onset.json').read_text());result=[]
for r in rows:
 p=ROOT/r['path'];d=np.load(p/'raw.npz');a=d['action'][:,13:23];q=d['q'][:,13:23]
 chunk=json.loads((p/'policy_inferences.json').read_text())[0];pred=np.asarray(chunk['actions'])[:10,:10]
 entry={k:r[k] for k in ('variant','task','passed','path','onset_frame')}
 entry.update(first_action_max_rad=float(abs(a[0]).max()),first_chunk_max_rad=float(abs(pred).max()),first_chunk_q_max_rad=float(abs(q[:10]).max()))
 if r['task']=='wait_no_package':
  entry.update(predicted_first10_joint_means_rad=pred.mean(0).tolist(),first_wait_gate_violation_frame=r['first_wait_gate_violation_frame'])
 result.append(entry)
(out/'startup_analysis.json').write_text(json.dumps(result,indent=2))
for v in ('b','c4'):
 for task in sorted({r['task'] for r in result}):
  rs=[r for r in result if r['variant']==v and r['task']==task]
  print(v,task,'first action max range',min(r['first_action_max_rad'] for r in rs),max(r['first_action_max_rad'] for r in rs))
  if task=='wait_no_package':
   for r in rs:print(' wait',r['first_wait_gate_violation_frame'],'mean action',np.round(r['predicted_first10_joint_means_rad'],4).tolist())
