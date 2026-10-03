"""Offline selection decision for source-bound candidate states, not execution.
Keep the original action when it already meets the original requested nominal
Z step. Otherwise accept a candidate only with the existing independent nominal
certificate, stricter-than-zero finite exact downward motion and a smaller exact
support-Z tracking error, and certified nominal hand/non-target path separation.
A fallback leaves the old command unchanged; it is not counted as task success.
Other-role same-layout collision core checks correct the planner-envelope path
bound for floating-point differences, without relaxing any separation threshold.
"""
from pathlib import Path
import json,datetime,hashlib
import numpy as np
W=Path(__file__).resolve().parent;C=W/'front_initial_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();A=W/'FRONT_LOADED_Z_PRIORITY_FULL_OFFLINE_GEOMETRY_AUDIT.json';P=W/'FRONT_LOADED_Z_PRIORITY_CLEARANCE_FULL_OBSERVATIONS_PROBE.json';audit=json.loads(A.read_text());probe=json.loads(P.read_text());sources={str(A):sha(A),str(P):sha(P),str(Path(__file__)):sha(__file__)}
for d in [audit,probe]:
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
rows=[];summary=[]
for ep in audit['episodes']:
 if not ep['selected']:summary.append(dict(episode=ep['episode'],selected=False,candidate_changes=0,physical_success_claim=False));continue
 other_task='nudge_mailer_to_bin' if 'push_box' in ep['episode'] else 'push_box_to_bin';layout=ep['episode'].split('_')[1];other_ep=C/f'case_{layout}/layout_{layout}_{other_task}';opp=other_ep/'frontal_bypass.json';plan=json.loads(opp.read_text())['plan'];cores=[]
 def find(x):
  if isinstance(x,dict):
   if 'collision_core_size_xyz' in x:cores.append(x)
   else:
    for v in x.values():find(v)
 find(plan);assert cores;core=np.array(cores[0]['collision_core_size_xyz']);assert all(np.allclose(c['collision_core_size_xyz'],core,atol=0,rtol=0) and c['core_center_local']==[0.,0.,0.] and c['primitive_type']=='Cube' for c in cores)
 envelope=np.array(ep['obstacle_envelope_size_xyz_m']);extra_extent=float(np.linalg.norm(np.maximum(core-envelope,0)/2));sources[str(opp)]=sha(opp);matches=next(x for x in probe['episodes'] if x['episode']==ep['episode']);by_step={r['step']:r for r in matches['rows']};decision=[]
 for r in ep['rows']:
  req=r['original_requested_z_mm'];parent=r['nominal_parent_support_delta_mm'][2];cand=r['nominal_candidate_support_delta_mm'][2];paths=r['nominal_straight_path_hands_non_target'];sep=all(v['certified'] and v['minimum_certified_gap_lower_bound_m']-extra_extent>0 for v in paths.values());p=by_step[r['step']]
  if parent<=req:reason='original_already_meets_requested_nominal_downward_step';changed=False
  elif not r['independent_nominal_passed'] or not sep:reason='independent_nominal_certificate_or_path_reject';changed=False
  elif cand>=0:reason='exact_support_motion_not_downward';changed=False
  elif abs(cand-req)>=abs(parent-req):reason='exact_support_tracking_not_improved';changed=False
  else:reason='verified_nominal_downward_tracking_improvement';changed=True
  decision.append(dict(step=r['step'],candidate_selected=changed,reason=reason,original_requested_z_mm=req,parent_nominal_support_z_mm=parent,candidate_nominal_support_z_mm=cand,parent_error_mm=abs(parent-req),candidate_error_mm=abs(cand-req),reported_solver_success=p['solver_success'],independent_certificate_passed=p['independent_nominal_primal_and_kkt_passed'],corrected_minimum_nominal_non_target_path_bound_m=min(v.get('minimum_certified_gap_lower_bound_m',float('-inf')) for v in paths.values())-extra_extent))
 reasons={k:sum(r['reason']==k for r in decision) for k in sorted({r['reason'] for r in decision})};chosen=[r for r in decision if r['candidate_selected']]
 summary.append(dict(episode=ep['episode'],selected=True,eligible_original_states=len(decision),candidate_changes=len(chosen),original_command_fallback=len(decision)-len(chosen),reason_counts=reasons,first_changed_step=chosen[0]['step'] if chosen else None,original_envelope_xyz=envelope.tolist(),other_role_measured_core_xyz=core.tolist(),conservative_core_extent_correction_m=extra_extent,minimum_corrected_nominal_non_target_path_bound_m=min(r['corrected_minimum_nominal_non_target_path_bound_m'] for r in decision),selected_parent_median_abs_z_error_mm=float(np.median([r['parent_error_mm'] for r in chosen])),selected_candidate_median_abs_z_error_mm=float(np.median([r['candidate_error_mm'] for r in chosen])),solver_non_success_selected_with_independent_certificate=sum(not r['reported_solver_success'] for r in chosen),physical_success_claim=False));rows.append(dict(episode=ep['episode'],rows=decision))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,summary=summary,episodes=rows,source_sha256=sources,controller_integrated=False,no_counterfactual_trajectory=True,physical_success_proven=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_SELECTION_SCREEN.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(summary,indent=2))
