"""Independent geometric neighborhood check for step667; no audit replacement."""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import planes
from support_axis_local_dominance_bound_v1 import inspect_local_dominance
E=W/'front_box_trailing_physical_r2/case_840020/layout_840020_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prov=read(E.parent/'provenance.json')
def source(name):
 matches=[k for k in prov['source_sha256'] if Path(k).name==name];assert len(matches)==1;p=E.parent/'source_snapshot'/matches[0];assert sha(p)==prov['source_sha256'][matches[0]];sources[str(p)]=sha(p);return p
geom=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'));row=next(r for r in read(E/'coordination.json') if r['step']==667);x=np.array(row['self_clearance_task']['candidate_command']);proof=inspect_local_dominance(geom,x,'left');assert not proof['original_unique_axis_test_passes'];assert proof['strict_local_dominance'];assert proof['chosen_axis']==38
branch=read(E/'LOADED_PARENT_NEAR_AXIS_BRANCH_DIAGNOSIS_V1.json');assert branch['near_axis_combinations']==2 and branch['primal_feasible_combinations']==1
other=[r for r in proof['near_axes'] if r['axis']!=proof['chosen_axis']];assert len(other)==1 and other[0]['cannot_meet_original_primal_floor_anywhere_in_box']
# Sampling checks the bound implementation; the triangle/operator bound above,
# not this finite sample, is the stated reasoning for the entire neighborhood.
rng=np.random.default_rng(667);center=planes(geom,x,'left');indices=[r['joint_index'] for r in proof['contributions']];max_displacement=0.;max_ratio=0.;n=0
for values in [*__import__('itertools').product([-1.,1.],repeat=len(indices)),*rng.uniform(-1.,1.,(64,len(indices))).tolist()]:
 q=x.copy();q[indices]+=np.array(values)*proof['joint_box_radius_rad'];p=planes(geom,q,'left');observed=float(np.max(np.abs(p-center)));bound=proof['vertex_position_change_bound_m']*(float(np.linalg.norm(geom.axes,axis=1).max())+1e-12)+proof['projection_roundoff_allowance_m'];assert observed<=bound;assert int(p.min(0).argmax())==proof['chosen_axis'];max_displacement=max(max_displacement,observed);max_ratio=max(max_ratio,observed/bound);n+=1
wide=inspect_local_dominance(geom,x,'left',radius_rad=2e-5);assert not wide['strict_local_dominance']
neg=[]
for label,radius in [('zero',0.),('negative',-1.),('nan',float('nan'))]:
 try:inspect_local_dominance(geom,x,'left',radius_rad=radius)
 except ValueError:neg.append(label)
 else:raise AssertionError('Invalid radius accepted')
for p in [Path(__file__),W/'support_axis_local_dominance_bound_v1.py',W/'support_vertex_stationarity.py',W/'audit_self_clearance_task_optimality.py']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,step=667,local_dominance=proof,corner_and_random_implementation_checks=n,max_observed_projection_change_m=max_displacement,max_observed_to_bound_ratio=max_ratio,wide_radius_dominance_proof_rejected=True,invalid_radius_rejections=neg,original_audits_still_failed=True,source_sha256=sources,training_ready=False)
with (E/'LOADED_PARENT_LOCAL_AXIS_BOUND_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope','local_dominance']},indent=2));print(json.dumps(proof,indent=2))
