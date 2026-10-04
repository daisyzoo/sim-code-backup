"""Narrow diagnosis of the original failed loaded-Z parent optimality assertion.
Uses unchanged certificate and raw current/previous actual command. This is not
an audit replacement, relaxation, task success or training-admission decision.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import certificate
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
E=W/'front_box_trailing_physical_r2/case_840020/layout_840020_push_box_to_bin';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
prov=read(E.parent/'provenance.json')
def source(name):
 paths=[n for n in prov['source_sha256'] if Path(n).name==name];assert len(paths)==1;p=E.parent/'source_snapshot'/paths[0];assert sha(p)==prov['source_sha256'][paths[0]];sources[str(p)]=sha(p);return p
geom=IndependentElbows(source('elbow_torso_hulls.json'),source('g1_23dof_rev_1_0_u1_black.urdf'))
p=E/'raw.npz';sources[str(p)]=sha(p)
with np.load(p) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
coord=read(E/'coordination.json');priority={r['step']:r for r in read(E/'front_loaded_z_priority.json')['rows']};records=[]
for c in coord:
 t=c['step']
 if not priority[t]['applied']:continue
 tr=c['self_clearance_task']
 if not tr['override']:continue
 a=c['task_inputs'];J=np.asarray(a['jacobian']);error=np.asarray(a['error']);prior=np.asarray(a['preferred_step']);damping=np.asarray(a['damping']);x=np.asarray(tr['candidate_command']);current=q[t];previous=u[t-1]
 assert np.array_equal(a['current'],current) and np.array_equal(a['previous'],previous)
 lo=np.asarray(a['lower']);hi=np.asarray(a['upper']);limits=np.asarray(a['step_limits']);low=np.maximum.reduce([lo,current-limits,previous-.055]);high=np.minimum.reduce([hi,current+limits,previous+.055]);delta=x-current
 gradient=J.T@(J@delta-error)+damping*damping*(delta-prior)
 proof=certificate(geometry=geom,x=x,gradient=gradient,lower=low,upper=high)
 assert np.max(abs(geom.gap(x)-tr['candidate_gaps_m']))<=2e-10
 records.append(dict(step=t,certificate=proof,runtime_solver_success=tr['solver_success'],runtime_iterations=tr['iterations'],runtime_status=tr['status'],runtime_candidate_command=x.tolist(),z_refinement_applied=True,task_objective=.5*float(np.dot(J@delta-error,J@delta-error)+np.dot(damping*(delta-prior),damping*(delta-prior)))))
bad=[r for r in records if not r['certificate']['passed']]
for p in [Path(__file__),W/'support_vertex_stationarity.py',W/'audit_self_clearance_task_optimality.py',W/'audit_front_loaded_z_priority_parent.py',E/'audit_front_box_trailing_r2_v2_execution.py.log']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checked_loaded_overrides=len(records),failed_count=len(bad),bad=bad,all_primal_feasible=all(r['certificate']['primal_feasible'] for r in records),stationarity_gate=1e-6,records=records,source_sha256=sources,original_failure_retained=True,training_ready=False)
with (E/'LOADED_PARENT_STATIONARITY_DIAGNOSIS_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(checked=len(records),bad=[dict(step=r['step'],reason=r['certificate']['reason'],residual=r['certificate']['stationarity_residual'],primal_feasible=r['certificate']['primal_feasible']) for r in bad],all_primal_feasible=out['all_primal_feasible'])))
