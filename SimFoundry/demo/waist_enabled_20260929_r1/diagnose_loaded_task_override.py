"""Explain loaded-task audit rejection; not replacement execution admission.
Original frozen rejection remains. Inspect every top_push task override and
bind existing independent KKT evidence to candidate/parent/raw command chain.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_self_clearance_task_optimality import IndependentElbows
stage=w/'staged_precise_parent_seed';geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');ep=w/'parent_seed_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cs=json.loads((ep/'coordination.json').read_text());fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};kr=json.loads((ep/'PARENT_SEED_POSE_TASK_OPTIMALITY_AUDIT.json').read_text());assert kr['passed'];kkt={r['step']:r for r in kr['records']}
for name,h in kr['source_sha256'].items():assert sha(ep/name)==h
assert kr['auditor_sha256']==sha(w/'audit_parent_seed_pose_task_optimality.py');rows=[]
with np.load(ep/'raw.npz') as z:
 q=z['q'][:,12:23];u=z['action'][:,12:23]
 for c in cs:
  t=c['step'];task=c.get('self_clearance_task',{})
  if not task.get('override') or fr[t]['mode']!='top_push':continue
  tr=c['joint_edge_refinement'];inp=c['task_inputs'];baseline=np.array(task['parent_command']);candidate=np.array(task['candidate_command']);parent=np.array(tr['parent_final_upper_command']);actual=np.array(tr['final_upper_command']);low=np.maximum.reduce([np.array(inp['lower']),q[t]-np.array(inp['step_limits']),u[t-1].astype(float)-.055]);high=np.minimum.reduce([np.array(inp['upper']),q[t]+np.array(inp['step_limits']),u[t-1].astype(float)+.055]);assert np.array_equal(actual,u[t]);assert np.array_equal(parent,candidate)
  rows.append(dict(step=t,task_kkt=kkt[t],baseline_min_bound_margin_rad=float(min(np.min(baseline-low),np.min(high-baseline))),baseline_gap_mm=(geom.gap(baseline)*1000).tolist(),task_candidate_gap_mm=(geom.gap(candidate)*1000).tolist(),final_executed_gap_mm=(geom.gap(actual)*1000).tolist(),task_candidate_equals_refinement_parent=True,refinement_final_equals_raw=True,refinement_override=tr['override'],refinement_reason=tr['reason'],candidate_to_final_max_delta_rad=float(max(abs(candidate-actual))),previous_observed_load_n=fr[t].get('measured_load_n'),full_nonlinear_loaded_execution_verified=False))
out=dict(scope=__doc__,episode=ep.name,loaded_task_override_count=len(rows),rows=rows,original_loaded_audit_still_rejected=True,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_self_clearance_task_optimality.py',ep/'raw.npz',ep/'coordination.json',ep/'frontal_bypass.json',ep/'PARENT_SEED_POSE_TASK_OPTIMALITY_AUDIT.json',ep/'audit_parent_seed_pose_loaded_execution.py.log']});(w/'LOADED_TASK_OVERRIDE_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2));print(json.dumps(rows,indent=2))
