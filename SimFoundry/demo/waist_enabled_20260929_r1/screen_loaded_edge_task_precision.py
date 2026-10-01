"""Isolated tolerance replay on every ordinary geometry override with a complete
current audit report. Short rear trajectories lack full audit reports and are
explicitly outside this replay. Not wired into the current collector.
Original objective, derivatives, bounds, 150 iterations, float32 execution and
independent KKT1e-6 gate unchanged. Only SLSQP ftol1e-11 ->1e-13. No physics.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
from scipy.optimize import nnls
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'staged_loaded_edge_coverage';stage=w/'staged_task_ik_precision';assert stage.exists();sys.path[:0]=[str(parent),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=(parent/'task_ik.py').read_text();assert source.count('ftol=1e-11')==1;probe=stage/'task_ik_precision.py';candidate=source.replace('ftol=1e-11','ftol=1e-13')
if probe.exists():assert probe.read_text()==candidate
else:probe.write_text(candidate)
spec=importlib.util.spec_from_file_location('precision_candidate',probe);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);guard=ClearanceGuard(repo,parent);geom=IndependentElbows(parent/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
def kkt(inp,x):
 q=np.asarray(inp['current']);J=np.asarray(inp['jacobian']);e=np.asarray(inp['error']);D=np.asarray(inp['damping'])**2;previous=np.asarray(inp['previous']);limits=np.asarray(inp['step_limits']);low=np.maximum.reduce([inp['lower'],q-limits,previous-.055]);high=np.minimum.reduce([inp['upper'],q+limits,previous+.055]);gaps=geom.gap(x);assert min(gaps)>=.005-2e-7 and np.all(x>=low-2e-7) and np.all(x<=high+2e-7)
 gradient=J.T@(J@(x-q)-e)+D*(x-q-inp['preferred_step']);G=geom.gradient(x);constraints=[G[i] for i in range(2) if gaps[i]-.005<=1e-6]
 for i in range(11):
  if x[i]-low[i]<=2e-6:constraints.append(np.eye(11)[i])
  if high[i]-x[i]<=2e-6:constraints.append(-np.eye(11)[i])
 if constraints:
  A=np.array(constraints);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];_,res=nnls(A.T,gradient,maxiter=1000)
 else:res=np.linalg.norm(gradient)
 return float(res),float(min(gaps))
reports=[]
for run in ['loaded_edge_coverage_groups_r1']:
 for file in sorted((w/run).glob('case_*/*/LOADED_EDGE_TASK_OPTIMALITY_AUDIT.json')):
  ep=file.parent;assert json.loads((ep/'quality.json').read_text())['frames']==1200;original=json.loads(file.read_text());coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};records=[]
  for r in original['records']:
   if not r['override']:continue
   inp=coords[r['step']]['task_inputs'];x,info=module.solve(enabled=True,geometry=guard.geometry,**inp);out=dict(step=r['step'],original_kkt=r['kkt_residual'],accepted=x is not None)
   if x is not None:
    residual,gap=kkt(inp,x.astype(float));out.update(candidate_kkt=residual,stationary=residual<=1e-6,min_gap_m=gap,iterations=info.get('iterations'),command_change_rad=float(max(abs(x-np.asarray(coords[r['step']]['self_clearance_task']['candidate_command'])))))
   records.append(out)
  report=dict(episode=str(ep),overrides=len(records),old_failed=sum(r['original_kkt']>1e-6 for r in records),new_failed=sum(not r['accepted'] or not r['stationary'] for r in records),max_new_kkt=max((r.get('candidate_kkt',0) for r in records),default=0),records=records,source_sha256={n:sha(ep/n) for n in ['coordination.json','LOADED_EDGE_TASK_OPTIMALITY_AUDIT.json']});reports.append(report);print(ep.name,run,report['overrides'],report['old_failed'],report['new_failed'],report['max_new_kkt'],flush=True)
out=dict(scope=__doc__,episodes=reports,original_failed=sum(r['old_failed'] for r in reports),candidate_failed=sum(r['new_failed'] for r in reports),overrides=sum(r['overrides'] for r in reports),collector_wired=False,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),probe,parent/'task_ik.py',stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',stage/'INTEGRATION_CHECK.json',w/'audit_unloaded_wrist_task_optimality.py']});(w/'LOADED_EDGE_TASK_PRECISION_REPLAY.json').write_text(json.dumps(out,indent=2));print('TOTAL',out['overrides'],out['original_failed'],out['candidate_failed'])
