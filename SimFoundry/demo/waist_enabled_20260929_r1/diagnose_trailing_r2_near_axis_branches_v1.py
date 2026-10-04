"""Exhaustive near-axis diagnosis of the original step667 certificate rejection.
Each near-axis branch is analyzed separately, never mixed to find a favorable
normal cone. This is diagnostic evidence only; original2um uniqueness gate and
all failed audits remain unchanged. Finite differences do not certify a region.
"""
from pathlib import Path
import sys,json,hashlib,datetime,itertools
import numpy as np
from scipy.optimize import nnls
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate,planes
E=W/'front_box_trailing_physical_r2/case_840020/layout_840020_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prov=read(E.parent/'provenance.json')
def source(name):
 paths=[n for n in prov['source_sha256'] if Path(n).name==name];assert len(paths)==1;p=E.parent/'source_snapshot'/paths[0];assert sha(p)==prov['source_sha256'][paths[0]];sources[str(p)]=sha(p);return p
geom=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'));coord=read(E/'coordination.json');prior=read(E/'LOADED_PARENT_STATIONARITY_DIAGNOSIS_V2.json');assert [r['step'] for r in prior['bad']]==[667]
c=next(r for r in coord if r['step']==667);a=c['task_inputs'];tr=c['self_clearance_task'];assert tr['override'];x=np.array(tr['candidate_command']);current=np.array(a['current']);previous=np.array(a['previous']);J=np.array(a['jacobian']);err=np.array(a['error']);damping=np.array(a['damping']);preferred=np.array(a['preferred_step']);limits=np.array(a['step_limits']);lower=np.maximum.reduce([np.array(a['lower']),current-limits,previous-.055]);upper=np.minimum.reduce([np.array(a['upper']),current+limits,previous+.055]);delta=x-current;gradient=J.T@(J@delta-err)+damping*damping*(delta-preferred)
p=E/'raw.npz';sources[str(p)]=sha(p)
with np.load(p) as z:assert np.array_equal(current,z['q'][667,12:23]) and np.array_equal(previous,z['action'][666,12:23])
original=certificate(geometry=geom,x=x,gradient=gradient,lower=lower,upper=upper);assert original==prior['bad'][0]['certificate'];assert original['reason']=='ambiguous_active_axis'
gaps=geom.gap(x);side_rows=[];choices=[]
for si,side in enumerate(['left','right']):
 p=planes(geom,x,side);ag=p.min(axis=0);maximum=float(ag.max());assert abs(maximum-gaps[si])<1e-12
 active=maximum-.005<=1e-6;near=np.flatnonzero(maximum-ag<=2e-6) if active else np.array([],dtype=int)
 records=[]
 for axis in near:
  # Original vertex threshold, unchanged even for the nonmaximizing branch.
  vertices=np.flatnonzero(p[:,axis]-.005<=1e-6);assert len(vertices)
  records.append(dict(axis=int(axis),axis_gap_m=float(ag[axis]),behind_maximum_m=maximum-float(ag[axis]),primal_feasible_at_original_elbow_tolerance=bool(ag[axis]>=.005-2e-7),vertices=vertices.tolist(),vertex_gaps_m=p[vertices,axis].tolist()))
 side_rows.append(dict(side=side,active=bool(active),max_gap_m=maximum,max_axis=int(ag.argmax()),near_axes=records));choices.append(records if active else [None])
bound_normals=[];active_bounds=[]
for j in range(11):
 if x[j]-lower[j]<=2e-6:bound_normals.append(np.eye(11)[j]);active_bounds.append(dict(joint=j,side='lower',slack=float(x[j]-lower[j])))
 if upper[j]-x[j]<=2e-6:bound_normals.append(-np.eye(11)[j]);active_bounds.append(dict(joint=j,side='upper',slack=float(upper[j]-x[j])))
results=[];probes=[]
for selection in itertools.product(*choices):
 entry=dict(branches=[dict(side=side_rows[i]['side'],axis=r['axis'],primal_feasible=r['primal_feasible_at_original_elbow_tolerance']) for i,r in enumerate(selection) if r is not None],all_branch_primal_feasible=all(r is None or r['primal_feasible_at_original_elbow_tolerance'] for r in selection),finite_difference_scales=[])
 for h in [1e-7,2e-7,4e-7]:
  normals=list(bound_normals)
  for si,r in enumerate(selection):
   if r is None:continue
   side=side_rows[si]['side'];vertices=r['vertices'];axis=r['axis'];G=np.zeros((len(vertices),11))
   for j in [1,2,3,4,6,7,8,9]:
    dq=np.eye(11)[j]*h;minus=planes(geom,x-dq,side);plus=planes(geom,x+dq,side);G[:,j]=(plus[vertices,axis]-minus[vertices,axis])/(2*h)
    if h==2e-7:probes.append(dict(side=side,joint=j,step_rad=h,center_max_axis=side_rows[si]['max_axis'],minus_max_axis=int(minus.min(0).argmax()),plus_max_axis=int(plus.min(0).argmax()),minus_gap_m=float(minus.min(0).max()),plus_gap_m=float(plus.min(0).max())))
   normals.extend(G)
  A=np.array(normals);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];multipliers,res=nnls(A.T,gradient,maxiter=1000);assert np.min(multipliers)>=0
  entry['finite_difference_scales'].append(dict(step_rad=h,stationarity_residual=float(res),within_original_1e_minus6_residual_gate=bool(res<=1e-6),normal_count=len(A),multipliers=multipliers.tolist(),normalized_normals=A.tolist()))
 results.append(entry)
feasible=[r for r in results if r['all_branch_primal_feasible']]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,step=667,original_certificate=original,gradient=gradient.tolist(),gradient_norm=float(np.linalg.norm(gradient)),side_analysis=side_rows,active_bounds=active_bounds,branch_results=results,near_axis_combinations=len(results),primal_feasible_combinations=len(feasible),all_primal_feasible_combinations_within_original_residual_gate=all(all(v['within_original_1e_minus6_residual_gate'] for v in r['finite_difference_scales']) for r in feasible) and bool(feasible),finite_difference_axis_probes=probes,all_sampled_differences_keep_maximizing_axis=all(r['center_max_axis']==r['minus_max_axis']==r['plus_max_axis'] for r in probes),original_uniqueness_gate_unchanged=True,original_audits_still_failed=True,not_a_new_acceptance_certificate=True,training_ready=False)
for p in [Path(__file__),W/'support_vertex_stationarity.py',W/'audit_self_clearance_task_optimality.py']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out['source_sha256']=sources
with (E/'LOADED_PARENT_NEAR_AXIS_BRANCH_DIAGNOSIS_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:out[k] for k in ['step','near_axis_combinations','primal_feasible_combinations','all_primal_feasible_combinations_within_original_residual_gate','all_sampled_differences_keep_maximizing_axis','original_audits_still_failed']}))
for r in results:print(json.dumps(dict(branches=r['branches'],residuals=[v['stationarity_residual'] for v in r['finite_difference_scales']])))
