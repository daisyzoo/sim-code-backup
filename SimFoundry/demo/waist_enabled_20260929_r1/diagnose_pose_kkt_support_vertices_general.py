"""Independent per-vertex KKT diagnostic for uniquely selected support axes.
For a fixed separating axis, min(vertex gap)>=5mm is the conjunction of all
vertex inequalities. A single derivative of that minimum can lose active normal
cone directions at vertex switches. Original bounds and1e-6 stationarity remain.
This is supplemental evidence, not a replacement of frozen audits or admission.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
import numpy as np
from scipy.optimize import nnls
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_self_clearance_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(ep):
 ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());src=prov['source_sha256'];snap=ep.parent/'source_snapshot'
 def archived(suffix):
  paths=[snap/n for n in src if n.endswith('/'+suffix)];assert len(paths)==1;p=paths[0];assert sha(p)==src[str(p.relative_to(snap))];return p
 hulls=archived('elbow_torso_hulls.json');urdf=archived('g1_23dof_rev_1_0_u1_black.urdf');geom=IndependentElbows(hulls,urdf)
 def planes(q,side):
  T=np.eye(4)
  for index,O,axis in geom.chains[side]:
   T=T@O
   if axis is not None:
    R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();T=T@R
  projected=(geom.v[side]@T[:3,:3].T+T[:3,3])@geom.axes.T
  return np.c_[projected-geom.tmax,geom.tmin-projected]
 auditpath=ep/'CLOSED_PEAK_TRIAL_POSE_TASK_OPTIMALITY_AUDIT.json';audit=json.loads(auditpath.read_text());prior={x['step']:x for x in audit['records']};coord=json.loads((ep/'coordination.json').read_text());rows=[]
 for c in coord:
  tr=c.get('self_clearance_task')
  if not tr or not tr.get('override'):continue
  inp=c['task_inputs'];J=np.array(inp['jacobian']);e=np.array(inp['error']);q=np.array(inp['current']);prev=np.array(inp['previous']);x=np.array(tr['candidate_command']);lo=np.maximum.reduce([np.array(inp['lower']),q-np.array(inp['step_limits']),prev-.055]);hi=np.minimum.reduce([np.array(inp['upper']),q+np.array(inp['step_limits']),prev+.055]);gradient=J.T@(J@(x-q)-e)+np.array(inp['damping'])**2*(x-q-np.array(inp['preferred_step']));constraints=[];detail=[]
  gap=geom.gap(x)
  for side_index,side in enumerate(['left','right']):
   p=planes(x,side);gaps=p.min(0);branch=int(gaps.argmax());assert abs(gaps[branch]-gap[side_index])<1e-12
   if gap[side_index]-.005>1e-6:continue
   vertices=np.flatnonzero(p[:,branch]-.005<=1e-6);assert len(vertices)
   G=np.zeros((len(vertices),11));h=2e-7
   for j in [1,2,3,4,6,7,8,9]:
    dx=np.eye(11)[j]*h;G[:,j]=(planes(x+dx,side)[vertices,branch]-planes(x-dx,side)[vertices,branch])/(2*h)
   constraints.extend(G);ordered=np.sort(gaps);detail.append(dict(side=side,axis_branch=branch,gap_m=float(gaps[branch]),axis_separation_from_second_m=float(ordered[-1]-ordered[-2]),active_vertices=vertices.tolist(),active_vertex_gap_excess_m=(p[vertices,branch]-.005).tolist(),unique_axis_with_2um_separation=bool(ordered[-1]-ordered[-2]>2e-6)))
  for j in range(11):
   if x[j]-lo[j]<=2e-6:constraints.append(np.eye(11)[j])
   if hi[j]-x[j]<=2e-6:constraints.append(-np.eye(11)[j])
  if constraints:
   A=np.array(constraints);norm=np.linalg.norm(A,axis=1);A=A[norm>1e-12]/norm[norm>1e-12,None];multipliers,res=nnls(A.T,gradient,maxiter=1000)
  else:res=float(np.linalg.norm(gradient))
  rows.append(dict(step=c['step'],original_residual=prior[c['step']]['kkt_residual'],original_passed=prior[c['step']]['stationary'],per_vertex_residual=float(res),per_vertex_stationary=bool(res<=1e-6),unique_active_axes=all(x['unique_axis_with_2um_separation'] for x in detail),geometry_constraints=detail))
 assert len(rows)==audit['overrides']
 # Exact corner: minimizing x+2y subject to x>=0,y>=0 has an optimum at0.
 # A central derivative of min(x,y) alone cannot represent its normal cone.
 corner_gradient=np.array([1.,2.]);single=nnls(np.array([[.5],[.5]]),corner_gradient)[1];separate=nnls(np.eye(2),corner_gradient)[1];assert single>1e-6 and separate==0
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,rows=rows,original_failures=sum(not x['original_passed'] for x in rows),per_vertex_failures=sum(not x['per_vertex_stationary'] for x in rows),ambiguous_axis_rows=sum(not x['unique_active_axes'] for x in rows),exact_corner_example=dict(single_min_gradient_residual=float(single),separate_vertex_residual=float(separate)),source_sha256={str(p):sha(p) for p in [Path(__file__),hulls,urdf,auditpath,ep/'coordination.json',W/'audit_self_clearance_task_optimality.py']},audit_changed=False,runtime_changed=False,training_ready=False)
 with (ep/'POSE_KKT_SUPPORT_VERTEX_DIAGNOSIS.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']},indent=2));print(json.dumps([dict(step=x['step'],original=x['original_residual'],per_vertex=x['per_vertex_residual'],active_vertices=[v['active_vertices'] for v in x['geometry_constraints']]) for x in rows if not x['original_passed']],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('episode');a=p.parse_args();main(a.episode)
