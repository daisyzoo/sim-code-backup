"""Capture independent selection-auditor failures without replacing official audits.
Only this diagnostic process continues after capturing an AssertionError, so all
mismatches can be located. Its continuation result is NOT an audit-pass claim.
No frozen source, physical data, command or official failed report is modified.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
import audit_rear_early_edge_selection_v1 as selection
from audit_rear_early_edge_r1_v1_stage_rear_xy import reconstruct
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};ep=W/'rear_early_edge_physical_r1/case_840023/layout_840023_push_box_to_bin'
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
fr=read(ep/'frontal_bypass.json');region=read(ep/'region_approach.json')['rows'];handover=next(r['step'] for r in region if r['solver'] and r['solver'].get('handover'));packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']};steps={id(r['rear_joint_xy_progress']):r['step'] for r in fr['rows'] if 'rear_joint_xy_progress' in r};arrays=[]
for name in ['trace.npz','parcel_orientation.npz']:
 p=ep/name;sources[str(p)]=sha(p)
 with np.load(p) as z:arrays.append(z['box'].astype(float))
original=selection.verify_selection;failures=[];calls=[]
def capture(**kw):
 step=steps[id(kw['observed'])];calls.append(step)
 try:return original(**kw)
 except AssertionError as exc:
  inputs=[np.asarray(kw[k],float) for k in ['previous_xyz','parent_xyz','reference_xyz','object_rotation','core_size','cop_local']];parent=selection._independent_xy(*inputs,kw['direction'],.010);candidate=selection._independent_xy(*inputs,kw['direction'],.020);observed=kw['observed'];recorded=observed['early_edge']['candidate_result']
  failures.append(dict(step=step,error=str(exc),independent_parent=parent,independent_candidate=candidate,recorded_candidate=recorded,recorded_selected=observed,candidate_override_equal=candidate['override']==recorded['override'],independent_candidate_reason=candidate['reason'],recorded_candidate_reason=recorded['reason'],arguments={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in kw.items() if k!='observed'}))
  return dict(diagnostic_only=True,passed=False,original_assertion_captured=True)
selection.verify_selection=capture
try:continued=reconstruct(fr['rows'],fr['plan'],arrays[0],arrays[1],packets,'box',handover)
finally:selection.verify_selection=original
for p in [Path(__file__),W/'audit_rear_early_edge_selection_v1.py',W/'audit_rear_early_edge_r1_v1_stage_rear_xy.py',ep/'audit_rear_early_edge_r1_v1_stage_rear_xy.py.log',ep/'audit_rear_early_edge_r1_v3_stage_pose_loaded_execution.py.log']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,eligible_calls=len(calls),failure_count=len(failures),failures=failures,remaining_reconstruction_errors=continued['errors'],official_audits_still_failed=True,source_sha256=sources,training_ready=False)
with (ep/'EARLY_SELECTION_FAILURE_DIAGNOSIS_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(eligible_calls=len(calls),failure_count=len(failures),failures=[{k:r[k] for k in ['step','error','independent_candidate_reason','recorded_candidate_reason','candidate_override_equal']} for r in failures],remaining_reconstruction_errors=continued['errors'])))
