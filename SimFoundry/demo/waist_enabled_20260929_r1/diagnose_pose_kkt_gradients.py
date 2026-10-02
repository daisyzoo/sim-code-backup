"""Compare unchanged audit finite differences with runtime branch derivatives.
Read-only diagnosis of every recorded nonlinear IK override. No auditor or
controller edits, threshold changes, data approval, or optimality certification.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import nnls
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def residual(gradient,gap,G,x,low,high):
 constraints=[]
 for i in range(2):
  if gap[i]-.005<=1e-6:constraints.append(G[i])
 for i in range(11):
  if x[i]-low[i]<=2e-6:constraints.append(np.eye(11)[i])
  if high[i]-x[i]<=2e-6:constraints.append(-np.eye(11)[i])
 if not constraints:return float(np.linalg.norm(gradient))
 A=np.array(constraints);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];return float(nnls(A.T,gradient,maxiter=1000)[1])

def main(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());guard=ClearanceGuard(ROOT,STAGE);hulls=STAGE/'elbow_torso_hulls.json';urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';independent=IndependentElbows(hulls,urdf);audit_path=ep/'CLOSED_PEAK_TRIAL_POSE_TASK_OPTIMALITY_AUDIT.json';audit=json.loads(audit_path.read_text());reference={x['step']:x for x in audit['records']};coord=json.loads((ep/'coordination.json').read_text());modes={x['step']:x['mode'] for x in json.loads((ep/'expert_control.json').read_text())};sources=[Path(__file__),audit_path,ep/'coordination.json',ep/'expert_control.json',W/'audit_self_clearance_task_optimality.py',W/'audit_closed_peak_trial_pose_task_optimality.py']
 for p in [hulls,urdf,STAGE/'task_ik.py',STAGE/'clearance_runtime.py',STAGE/'self_clearance.py',STAGE/'articulated_hand_geometry.py']:
  assert sha(p)==prov['source_sha256'][str(p.relative_to(ROOT))];sources.append(p)
 for name,h in audit['source_sha256'].items():assert sha(ep/name)==h
 def fd(x,h):
  G=np.zeros((2,11))
  for i in [1,2,3,4,6,7,8,9]:
   dx=np.eye(11)[i]*h;G[:,i]=(independent.gap(x+dx)-independent.gap(x-dx))/(2*h)
  return G
 rows=[]
 for c in coord:
  tr=c.get('self_clearance_task')
  if not tr or not tr.get('override'):continue
  t=c['step'];inp=c['task_inputs'];J=np.array(inp['jacobian']);e=np.array(inp['error']);q=np.array(inp['current']);prev=np.array(inp['previous']);x=np.array(tr['candidate_command']);damping=np.array(inp['damping']);prior=np.array(inp['preferred_step']);low=np.maximum.reduce([np.array(inp['lower']),q-np.array(inp['step_limits']),prev-.055]);high=np.minimum.reduce([np.array(inp['upper']),q+np.array(inp['step_limits']),prev+.055]);gradient=J.T@(J@(x-q)-e)+damping**2*(x-q-prior);gap=independent.gap(x);analytic=guard.geometry.jacobian(x);G=fd(x,2e-7);base=residual(gradient,gap,G,x,low,high);assert abs(base-reference[t]['kkt_residual'])<1e-12
  branches=[]
  for side in ['left','right']:
   a=guard.geometry.evaluate(x,side);ordered=np.sort(a['gaps']);branches.append(dict(side=side,gap_m=a['gap'],branch=a['branch'],vertex=a['vertex'],best_minus_second_gap_m=float(ordered[-1]-ordered[-2])))
  variants={f'{h:g}':residual(gradient,gap,fd(x,h),x,low,high) for h in [1e-8,1e-9]}
  rows.append(dict(step=t,mode=modes[t],original_kkt_residual=base,original_passed=base<=1e-6,runtime_branch_kkt_residual=residual(gradient,gap,analytic,x,low,high),finite_difference_residuals=variants,analytic_vs_original_fd_max_error=float(abs(analytic-G).max()),branches=branches,solver_iterations=tr['iterations']))
 assert len(rows)==audit['overrides']==175
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,rows=rows,overrides=len(rows),original_failed=sum(not x['original_passed'] for x in rows),branch_derivative_failed=sum(x['runtime_branch_kkt_residual']>1e-6 for x in rows),fd1e8_failed=sum(x['finite_difference_residuals']['1e-08']>1e-6 for x in rows),fd1e9_failed=sum(x['finite_difference_residuals']['1e-09']>1e-6 for x in rows),source_sha256={str(p):sha(p) for p in sources},training_ready=False,runtime_changed=False,audit_changed=False)
 with (ep/'POSE_KKT_GRADIENT_DIAGNOSIS.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']},indent=2));print(json.dumps([x for x in rows if not x['original_passed']],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');a=p.parse_args();main(a.episode)
