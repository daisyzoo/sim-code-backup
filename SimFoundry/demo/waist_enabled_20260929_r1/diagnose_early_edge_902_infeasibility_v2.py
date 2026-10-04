"""Exact rational infeasibility witness for the recorded step902 candidate.
This diagnoses a reason-string mismatch only; official failed audits remain.
The candidate was not selected; no trajectory, tolerance or action is modified.
"""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,datetime
W=Path(__file__).resolve().parent;E=W/'rear_early_edge_physical_r1/case_840023/layout_840023_push_box_to_bin';P=E/'EARLY_SELECTION_FAILURE_DIAGNOSIS_V1.json';d=json.loads(P.read_text());assert d['eligible_calls']==625 and d['failure_count']==1 and not d['remaining_reconstruction_errors'];r=d['failures'][0];assert r['step']==902;results=[]
for source in ['recorded_candidate','independent_candidate']:
 c=r[source];A=[[F(x) for x in row] for row in c['constraints_mm']];b=[F(x) for x in c['rhs_mm']];assert A[0][0]<0<A[1][0] and A[4]==[0,-1] and b[4]==0
 # Positive weighted sum cancels dx. Add scale>=0 (row4) to cancel scale.
 u=A[1][0];v=-A[0][0];s=u*A[0][1]+v*A[1][1];assert min(u,v,s)>0
 lhs=[u*A[0][i]+v*A[1][i]+s*A[4][i] for i in [0,1]];rhs=u*b[0]+v*b[1]+s*b[4];assert lhs==[0,0] and rhs<0
 # Separately check whether this witness survives per-row 1e-8 relaxation.
 # This is the existing runtime admissibility tolerance, in the mm LP units.
 tolerance=F(1e-8);relaxed=rhs+tolerance*(u+v+s)
 results.append(dict(source=source,positive_multipliers_exact=[str(x) for x in [u,v,s]],constraint_rows=[0,1,4],weighted_lhs_exact=[str(x) for x in lhs],weighted_rhs_exact=str(rhs),weighted_rhs_float=float(rhs),exact_constraints_infeasible=True,existing_1e_minus8_tolerance_relaxed_rhs=float(relaxed),tolerance_relaxed_infeasibility_proven=relaxed<0))
sel=r['recorded_selected'];assert sel['early_edge']['candidate_selected'] is False and sel['early_edge']['fallback']=='complete_original_joint_XY_result';assert {k:v for k,v in sel.items() if k!='early_edge'}==r['independent_parent'];assert r['candidate_override_equal']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,step=902,eligible_calls=625,only_reason_mismatch=True,certificates=results,selected_complete_parent_verified=True,official_audits_still_failed=True,interpretation='Recorded and independent candidate linear systems are exactly infeasible. Runtime numerical_infeasible and LP no_joint_XY_direction both reject this candidate, retaining the original parent. The certificate does not replace official audits, prove tolerance-relaxed infeasibility, or change the failed physical task.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),P]},training_ready=False)
with (E/'EARLY_EDGE_902_INFEASIBILITY_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
