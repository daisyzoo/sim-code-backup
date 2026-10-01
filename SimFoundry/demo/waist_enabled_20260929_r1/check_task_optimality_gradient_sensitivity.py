"""Finite-difference sensitivity for the worst independently audited IK frame
of each difficult episode. No solver, command, gate or frozen report changes.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import nnls
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w));from audit_self_clearance_task_optimality import IndependentElbows
r=w/'self_clearance_groups_r1';rows=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for ep in sorted(r.glob('case_*/layout_*')):
 p=ep/'SELF_CLEARANCE_TASK_OPTIMALITY_AUDIT.json'
 if not p.exists():continue
 audit=json.loads(p.read_text())
 if audit['passed']:continue
 t=max(audit['errors'],key=lambda x:x['kkt_residual'])['step'];c=next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==t);inp=c['task_inputs'];tr=c['self_clearance_task'];prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot'
 def src(name):return snap/next(n for n in prov['source_sha256'] if n.endswith('/'+name))
 geom=IndependentElbows(src('elbow_torso_hulls.json'),src('g1_23dof_rev_1_0_u1_black.urdf'))
 x=np.array(tr['candidate_command']);q=np.array(inp['current']);prev=np.array(inp['previous']);limit=np.array(inp['step_limits']);low=np.maximum.reduce([inp['lower'],q-limit,prev-.055]);high=np.minimum.reduce([inp['upper'],q+limit,prev+.055]);J=np.array(inp['jacobian']);E=np.array(inp['error']);delta=x-q;grad=J.T@(J@delta-E)+np.array(inp['damping'])**2*(delta-np.array(inp['preferred_step']));gap=geom.gap(x);checks=[]
 for h in [2e-5,2e-6,2e-7,2e-8,2e-9]:
  G=np.zeros((2,11))
  for i in [1,2,3,4,6,7,8,9]:
   d=np.zeros(11);d[i]=h;G[:,i]=(geom.gap(x+d)-geom.gap(x-d))/(2*h)
  constraints=[G[i] for i in range(2) if gap[i]-.005<=1e-6]
  for i in range(11):
   if x[i]-low[i]<=2e-6:constraints.append(np.eye(11)[i])
   if high[i]-x[i]<=2e-6:constraints.append(-np.eye(11)[i])
  A=np.array(constraints);length=np.linalg.norm(A,axis=1);A=A[length>1e-12]/length[length>1e-12,None];_,res=nnls(A.T,grad,maxiter=1000)
  checks.append(dict(finite_difference_step=h,kkt_residual=float(res),passes_original_extra_check=bool(res<=1e-6)))
 rows.append(dict(episode=ep.name,step=t,checks=checks,source_sha256={n:sha(ep/n) for n in ['SELF_CLEARANCE_TASK_OPTIMALITY_AUDIT.json','coordination.json']}))
out=dict(scope=__doc__,rows=rows,all_tested_scales_fail=all(not c['passes_original_extra_check'] for row in rows for c in row['checks']),auditor_sha256=sha(__file__),training_ready=False);(r/'TASK_OPTIMALITY_GRADIENT_SENSITIVITY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
