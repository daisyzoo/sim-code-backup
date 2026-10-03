"""Diagnose a frozen original task certificate failure; never change admission.
Rigid FK pivot displacement bounds prove winner stability on each FD segment.
This is a diagnostic, not a replacement for the full original episode audit.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w))
from audit_self_clearance_task_optimality import IndependentElbows
from support_vertex_stationarity import planes,certificate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=w/'front_corridor_midpoint_physical_r1'
eps=list(r.glob('case_840023/**/layout_840023_nudge_mailer_to_bin'));assert len(eps)==1
ep=eps[0];orig=ep/'FRONT_CORRIDOR_MIDPOINT_STAGE_TASK_OPTIMALITY_V2_AUDIT.json';report=json.loads(orig.read_text())
assert not report['passed'] and len(report['errors'])==1
error=report['errors'][0];assert error['step']==1039 and error['vertex_certificate']['reason']=='ambiguous_active_axis'
provpath=ep.parent/'provenance.json';prov=json.loads(provpath.read_text());snap=ep.parent/'source_snapshot'
def archived(name):
 matches=[(snap/n,h) for n,h in prov['source_sha256'].items() if n.endswith('/'+name)];assert len(matches)==1
 p,h=matches[0];assert sha(p)==h;return p
hulls=archived('elbow_torso_hulls.json');urdf=archived('g1_23dof_rev_1_0_u1_black.urdf');g=IndependentElbows(hulls,urdf)
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
c=next(c for c in json.loads((ep/'coordination.json').read_text()) if c['step']==1039);t=c['step'];inp=c['task_inputs'];tr=c['self_clearance_task'];x=np.array(tr['candidate_command']);J=np.array(inp['jacobian']);E=np.array(inp['error']);d=np.array(inp['damping']);prior=np.array(inp['preferred_step'])
assert np.array_equal(x,x.astype(np.float32).astype(float))
lo=np.maximum.reduce([np.array(inp['lower']),q[t]-inp['step_limits'],u[t-1]-.055]);hi=np.minimum.reduce([np.array(inp['upper']),q[t]+inp['step_limits'],u[t-1]+.055])
gradient=J.T@(J@(x-q[t])-E)+d*d*(x-q[t]-prior)
old=certificate(geometry=g,x=x,gradient=gradient,lower=lo,upper=hi);assert old==error['vertex_certificate']
H=2e-7;details=[];normals=[]
for side in ['left','right']:
 T=np.eye(4);pivots={}
 for idx,O,a in g.chains[side]:
  T=T@O
  if a is not None:
   assert abs(np.linalg.norm(a)-1)<1e-12
   if idx is not None:pivots[idx]=(T[:3,3].copy(),T[:3,:3]@a)
   R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(a*(x[idx] if idx is not None else 0.)).as_matrix();T=T@R
 vertices=g.v[side]@T[:3,:3].T+T[:3,3];p=planes(g,x,side);ag=p.min(0);order=np.argsort(ag);axis=int(order[-1]);sep=float(ag[axis]-ag[order[-2]])
 active=np.flatnonzero(p[:,axis]-.005<=1e-6);assert len(active)
 normal=g.axes[axis%len(g.axes)]*(1 if axis<len(g.axes) else -1)
 A=np.zeros((len(active),11));F=np.zeros_like(A);bounds=[]
 for j in range(11):
  dq=np.eye(11)[j]*H;pp=planes(g,x+dq,side);pm=planes(g,x-dq,side)
  F[:,j]=(pp[active,axis]-pm[active,axis])/(2*H)
  D=0.
  if j in pivots:
   pivot,ax=pivots[j];vectors=vertices-pivot
   radius=np.linalg.norm(np.cross(ax,vectors),axis=1);D=float(2*radius.max()*np.sin(H/2))
   A[:,j]=np.cross(ax,vectors[active])@normal
  # Every support projection is 1-Lipschitz in vertex displacement.
  # Winner-runner gap loses at most 2*D for all |dq_j| <= H.
  slack=sep-2*D
  observed=max(float(abs(pp-p).max()),float(abs(pm-p).max()))
  assert observed<=D+1e-12
  bounds.append(dict(joint_index=j,max_vertex_displacement_m=D,winner_separation_lower_bound_m=slack,stencil_same_winner=bool(pp.min(0).argmax()==axis==pm.min(0).argmax()),observed_max_projection_change_m=observed))
 details.append(dict(side=side,axis=axis,runner_up_axis=int(order[-2]),axis_gap_m=float(ag[axis]),runner_up_gap_m=float(ag[order[-2]]),separation_m=sep,original_fixed_separation_requirement_m=2e-6,vertices=active.tolist(),vertex_gaps_m=p[active,axis].tolist(),analytic_fd_max_error=float(abs(A-F).max()),all_segments_proven_stable_with_1pm_numerical_reserve=all(b['winner_separation_lower_bound_m']>1e-12 for b in bounds),segments=bounds))
 normals.extend(A)
for j in range(11):
 if x[j]-lo[j]<=2e-6:normals.append(np.eye(11)[j])
 if hi[j]-x[j]<=2e-6:normals.append(-np.eye(11)[j])
A=np.array(normals);n=np.linalg.norm(A,axis=1);A=A[n>1e-12]/n[n>1e-12,None];mult,res=nnls(A.T,gradient,maxiter=1000)
files=[Path(__file__),orig,ep/'raw.npz',ep/'coordination.json',provpath,hulls,urdf,w/'support_vertex_stationarity.py',w/'audit_self_clearance_task_optimality.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=str(ep),step=t,original_failure_unchanged=old,axis_details=details,diagnostic_analytic_stationarity_residual=float(res),original_stationarity_tolerance=1e-6,source_sha256={str(p):sha(p) for p in files},training_ready=False,original_audit_resolved=False,physical_task_passed=False,next_requirement='Versioned independent certificate validation and full affected episode supplemental audit; no gate or original report mutation.')
path=r/'TASK_AXIS_SEPARATION_DIAGNOSTIC.json'
with path.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','original_failure_unchanged']},indent=2))
