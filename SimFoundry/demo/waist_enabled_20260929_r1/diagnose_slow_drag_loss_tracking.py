"""Observed command/measurement/load history near contact loss.
No counterfactual dynamics, no relaxation of the original gates.
"""
from pathlib import Path
import json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent;r=w/'rear_slow_drag_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};nr=json.loads((ep/'SLOW_DRAG_NUMERIC_REVIEW.json').read_text());out=[]
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
for bout in nr['bouts']:
 if bout['exit_reason']!='lost_contact':continue
 rows=[]
 for t in range(max(bout['start'],bout['end']-11),bout['end']+1):
  f=fs[t];c=cs[t];inp=c['task_inputs'];J=np.asarray(c['control_jacobian_world']);active=slice(3,6);point=np.asarray(f['observed_support_xyz']);target=np.asarray(f['target_xyz']);error=(target-point)*1000
  command=np.asarray(c['joint_edge_refinement']['final_upper_command']);assert np.max(abs(command-u[t]))==0
  predicted=J[active]@(command-q[t])*1000;actual=(np.array(fs[t+1]['observed_support_xyz'])-point)*1000
  offset_same=np.max(abs(np.asarray(fs[t+1]['control_offset_local'])-np.asarray(f['control_offset_local'])))<1e-10
  lo=np.asarray(inp['lower']);hi=np.asarray(inp['upper']);bounds_margin=np.minimum(command-lo,hi-command);waist_margin=min(command[0]-lo[0],hi[0]-command[0])
  rows.append(dict(step=t,observed_load_n=f['contact_load']['observed_vertical_load_n'],filtered_load_n=f['contact_load']['filtered_vertical_load_n'],applied_z_bias_mm=f['contact_load']['applied_z_bias_m']*1000,target_minus_observed_xyz_mm=error.tolist(),commanded_linear_point_delta_mm=predicted.tolist(),observed_next_point_delta_mm=actual.tolist(),same_virtual_offset_next=bool(offset_same),waist_command_rad=float(command[0]),waist_bound_margin_rad=float(waist_margin),saturated_joint_indices=np.flatnonzero(bounds_margin<=2e-6).tolist(),previous_command_tracking_error_rad=(u[t-1]-q[t]).tolist(),rear_governor=f.get('rear_joint_xy_progress'),edge_reason=c['joint_edge_refinement']['reason']))
 out.append(dict(start=bout['start'],end=bout['end'],exit_step=bout['end']+1,rows=rows,all_bias_at_lower_limit=all(abs(x['applied_z_bias_mm']+6)<1e-8 for x in rows),waist_saturated_frames=sum(x['waist_bound_margin_rad']<=2e-6 for x in rows),median_target_error_xyz_mm=np.median([x['target_minus_observed_xyz_mm'] for x in rows],axis=0).tolist()))
report=dict(scope=__doc__,episodes=[dict(episode=ep.name,losses=out)],source_sha256={str(p):sha(p) for p in [Path(__file__),ep/'raw.npz',ep/'frontal_bypass.json',ep/'coordination.json',ep/'SLOW_DRAG_NUMERIC_REVIEW.json']},training_ready=False)
(r/'LOSS_TRACKING_DIAGNOSTIC.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='rows'} for x in out],indent=2))
