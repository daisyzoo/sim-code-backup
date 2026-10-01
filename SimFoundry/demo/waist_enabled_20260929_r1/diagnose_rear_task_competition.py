"""Diagnostic only: does holding the inactive palm compete with loaded rear tracking?
At recorded q compare original nine task rows with the three inactive position
rows removed. Same bounds, damping, normal rows and elbow constraints. This
unexecuted ablation omits later rear edge refinement and is NOT a controller.
No permission to discard stability/collision or train from these states.
"""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';sys.path[:0]=[str(stage),str(w),str(repo)]
from task_ik import solve
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);out=[]
for run,cid,task in [('front_diagonal_entry_groups_r1',840001,'push_box_to_bin'),('front_diagonal_entry_groups_r1',840004,'nudge_mailer_to_bin'),('micro_clearance_groups_r1',840001,'push_box_to_bin'),('micro_clearance_groups_r1',840004,'nudge_mailer_to_bin')]:
 ep=w/run/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in task else 'left';active=np.arange(3,6) if side=='right' else np.arange(3);inactive=np.arange(3) if side=='right' else np.arange(3,6);records=[];bounds=collections.Counter()
 for row in fr['rows']:
  if row['mode']!='top_push' or row['contact_load']['observed_vertical_load_n']<=.3:continue
  t=row['step'];inp=coords[t]['task_inputs'];J=np.array(inp['jacobian']);e=np.array(inp['error']);assert J.shape==(9,11);q=np.array(inp['current']);lo=np.array(inp['lower']);hi=np.array(inp['upper']);keep=np.r_[active,np.arange(6,9)];alt=dict(inp,jacobian=J[keep],error=e[keep]);base,bi=solve(enabled=True,geometry=guard.geometry,**inp);candidate,ci=solve(enabled=True,geometry=guard.geometry,**alt);assert base is not None
  active_bounds=np.flatnonzero(np.minimum(abs(base-lo),abs(base-hi))<2e-6)
  for i in active_bounds:bounds[int(i)]+=1
  entry=dict(step=t,accepted=candidate is not None,active_absolute_bounds=active_bounds.tolist(),waist_q=float(q[0]),waist_command=float(base[0]))
  if candidate is not None:
   rb=J@(base-q)-e;rc=J@(candidate-q)-e;entry.update(command_change_max_rad=float(max(abs(candidate-base))),baseline_active_residual_mm=float(np.linalg.norm(rb[active])*1000),relaxed_active_residual_mm=float(np.linalg.norm(rc[active])*1000),active_residual_reduction_mm=float((np.linalg.norm(rb[active])-np.linalg.norm(rc[active]))*1000),inactive_predicted_delta_mm=float(np.linalg.norm(J[inactive]@(candidate-q))*1000),baseline_normal_residual=float(np.linalg.norm(rb[6:])),relaxed_normal_residual=float(np.linalg.norm(rc[6:])))
  records.append(entry)
 accepted=[r for r in records if r['accepted']];summary={k:dict(median=float(np.median([r[k] for r in accepted])),maximum=float(max(r[k] for r in accepted))) for k in ['command_change_max_rad','baseline_active_residual_mm','relaxed_active_residual_mm','active_residual_reduction_mm','inactive_predicted_delta_mm','baseline_normal_residual','relaxed_normal_residual']}
 item=dict(episode=str(ep),loaded_frames=len(records),accepted_relaxations=len(accepted),absolute_bound_counts=dict(bounds),summary=summary,records=records,source_sha256={n:sha(ep/n) for n in ['frontal_bypass.json','coordination.json']});out.append(item);print(ep.name,run,'frames',len(records),'bounds',dict(bounds),'summary',json.dumps(summary),flush=True)
(w/'REAR_TASK_COMPETITION_DIAGNOSIS.json').write_text(json.dumps(dict(scope=__doc__,episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'task_ik.py',stage/'clearance_runtime.py',stage/'waist_coordination_clearance.py']},collector_changed=False,training_ready=False),indent=2))
