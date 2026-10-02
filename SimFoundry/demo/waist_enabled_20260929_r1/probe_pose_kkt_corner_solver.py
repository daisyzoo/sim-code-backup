"""Offline recorded-IK corner replay and fixed-axis per-vertex SLSQP probe.
All original objective, limits, slew and 5mm clearance retained. No runtime or
frozen-auditor changes; nominal geometry is not full robot/path certification.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import minimize,Bounds,nnls
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];STAGE=W/'staged_closed_peak_trial';sys.path[:0]=[str(STAGE),str(ROOT),str(W)]
from clearance_runtime import ClearanceGuard
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());guard=ClearanceGuard(ROOT,STAGE);hulls=STAGE/'elbow_torso_hulls.json';urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';geom=IndependentElbows(hulls,urdf)
 sources=[Path(__file__),ep/'coordination.json',ep/'POSE_KKT_SUPPORT_VERTEX_DIAGNOSIS.json',W/'audit_self_clearance_task_optimality.py']
 for p in [hulls,urdf,STAGE/'task_ik.py',STAGE/'clearance_runtime.py',STAGE/'self_clearance.py',STAGE/'articulated_hand_geometry.py']:
  assert sha(p)==prov['source_sha256'][str(p.relative_to(ROOT))];sources.append(p)
 def vertices(q,side):
  T=np.eye(4)
  for index,O,axis in geom.chains[side]:
   T=T@O
   if axis is not None:
    R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();T=T@R
  return geom.v[side]@T[:3,:3].T+T[:3,3]
 def planes(q,side):
  p=vertices(q,side)@geom.axes.T;return np.c_[p-geom.tmax,geom.tmin-p]
 def fixed(q,branches):
  out=[]
  for side,b in zip(['left','right'],branches):
   p=vertices(q,side)@geom.axes[b%len(geom.axes)]
   out.extend(p-geom.tmax[b] if b<len(geom.axes) else geom.tmin[b-len(geom.axes)]-p)
  return np.array(out)-.005
 def derivative(fun,x,h=2e-7):
  G=np.zeros((len(fun(x)),11))
  for j in [1,2,3,4,6,7,8,9]:
   dx=np.eye(11)[j]*h;G[:,j]=(fun(x+dx)-fun(x-dx))/(2*h)
  return G
 records=[];coord=json.loads((ep/'coordination.json').read_text());diagnosis=json.loads((ep/'POSE_KKT_SUPPORT_VERTEX_DIAGNOSIS.json').read_text());chosen={r['step'] for r in diagnosis['rows'] if not r['original_passed']}
 for c in coord:
  if c['step'] not in chosen:continue
  inp=c['task_inputs'];J=np.array(inp['jacobian']);E=np.array(inp['error']);q=np.array(inp['current']);prev=np.array(inp['previous']);original=np.array(c['self_clearance_task']['candidate_command']);D=np.array(inp['damping'])**2;prior=np.array(inp['preferred_step']);lo=np.maximum.reduce([np.array(inp['lower']),q-np.array(inp['step_limits']),prev-.055]);hi=np.minimum.reduce([np.array(inp['upper']),q+np.array(inp['step_limits']),prev+.055]);branches=[int(planes(original,s).min(0).argmax()) for s in ['left','right']]
  def cost(x):
   d=x-q;t=J@d-E;r=d-prior;return float(t@t+np.sum(D*r*r)),2*J.T@t+2*D*r
  def measure(x):
   gradients=[];axis_separation=[];slacks=[]
   for side in ['left','right']:
    P=planes(x,side);g=P.min(0);b=int(g.argmax());axis_separation.append(float(np.sort(g)[-1]-np.sort(g)[-2]))
    if g[b]-.005<=1e-6:
     ids=np.flatnonzero(P[:,b]-.005<=1e-6);fun=lambda z:planes(z,side)[ids,b];gradients.extend(derivative(fun,x));slacks.extend((P[ids,b]-.005).tolist())
   for j in range(11):
    if x[j]-lo[j]<=2e-6:gradients.append(np.eye(11)[j])
    if hi[j]-x[j]<=2e-6:gradients.append(-np.eye(11)[j])
   g=cost(x)[1]/2
   if gradients:
    A=np.array(gradients);n=np.linalg.norm(A,axis=1);A=A[n>1e-12]/n[n>1e-12,None];res=nnls(A.T,g,maxiter=1000)[1]
   else:res=np.linalg.norm(g)
   gaps=geom.gap(x);bound=max(float(np.max(lo-x)),float(np.max(x-hi)),0.)
   return dict(objective=cost(x)[0],per_vertex_kkt_residual=float(res),stationary=bool(res<=1e-6),minimum_gap_m=float(gaps.min()),bound_violation_rad=bound,feasible_original_tolerance=bool(gaps.min()>=.005-2e-7 and bound<=2e-7),axis_separation_m=axis_separation,active_vertex_slacks_m=slacks)
  attempts=[]
  for mode,ftol,seed in [('original',1e-11,'previous'),('original',1e-14,'candidate'),('per_vertex',1e-11,'previous'),('per_vertex',1e-14,'previous'),('per_vertex',1e-14,'candidate')]:
   fun=(lambda x:guard.geometry.constraints(x)-.005) if mode=='original' else lambda x:fixed(x,branches)
   jac=guard.geometry.jacobian if mode=='original' else lambda x:derivative(fun,x)
   start=np.clip(prev if seed=='previous' else original,lo,hi)
   r=minimize(cost,start,jac=True,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=fun,jac=jac)],method='SLSQP',options=dict(maxiter=150,ftol=ftol))
   x=r.x.astype(np.float32).astype(float);a=dict(mode=mode,ftol=ftol,seed=seed,success=bool(r.success),status=int(r.status),iterations=int(r.nit),original_command_max_difference_rad=float(abs(x-original).max()),float64=measure(r.x),float32=measure(x),command=x.tolist());attempts.append(a)
   if mode=='original' and seed=='previous':a['reproduced_original_within_1e7']=bool(a['original_command_max_difference_rad']<1e-7)
  row=dict(step=c['step'],original=measure(original),fixed_axis_branches=branches,attempts=attempts);records.append(row)
  print(json.dumps(dict(step=c['step'],original=row['original']['per_vertex_kkt_residual'],attempts=[{k:a[k] for k in ['mode','ftol','seed','success','iterations','float32']} for a in attempts])),flush=True)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,source_sha256={str(p):sha(p) for p in sources},audit_changed=False,runtime_changed=False,training_ready=False)
 with (ep/'POSE_KKT_CORNER_SOLVER_PROBE.json').open('x') as f:json.dump(report,f,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');a=p.parse_args();main(a.episode)
