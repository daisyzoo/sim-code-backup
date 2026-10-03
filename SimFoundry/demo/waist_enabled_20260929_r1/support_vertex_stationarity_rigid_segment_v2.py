"""Independent versioned stationarity certificate for fixed-axis elbow support.
For a UNIQUE maximizing axis, max_axis min_vertex gap>=margin is locally the
intersection of every vertex inequality on that axis. At a vertex tie every
active vertex normal is required; a derivative of min alone is insufficient.
Near axes require a rigid rotation stability proof; unresolved ties are rejected.
Original primal/active/stationarity tolerances remain explicit and unchanged.
This certificate alone does not validate source, task, contacts or data admission.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import nnls
VERSION='unique_axis_all_support_vertices_rigid_segment_v2'
def planes(geometry,q,side):
 T=np.eye(4)
 for index,O,axis in geometry.chains[side]:
  T=T@O
  if axis is not None:
   R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();T=T@R
 projected=(geometry.v[side]@T[:3,:3].T+T[:3,3])@geometry.axes.T
 return np.c_[projected-geometry.tmax,geometry.tmin-projected]
def certificate(*,geometry,x,gradient,lower,upper,extra_values=None,extra_jacobian=None):
 x,gradient,lower,upper=(np.asarray(v,float) for v in [x,gradient,lower,upper])
 if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [x,gradient,lower,upper]) or np.any(lower>upper):raise ValueError('Invalid finite11D certificate input')
 extra=np.array([]) if extra_values is None else np.asarray(extra_values,float);Gextra=np.empty((0,11)) if extra_jacobian is None else np.asarray(extra_jacobian,float)
 if extra.ndim!=1 or Gextra.shape!=(len(extra),11) or not np.isfinite(extra).all() or not np.isfinite(Gextra).all():raise ValueError('Invalid extra inequality')
 gaps=geometry.gap(x);valid=bool(np.all(x>=lower-2e-7) and np.all(x<=upper+2e-7) and min(gaps)>=.005-2e-7 and np.all(extra>=-1e-7))
 result=dict(version=VERSION,primal_feasible=valid,passed=False,elbow_gaps_m=gaps.tolist(),extra_values=extra.tolist(),axis_details=[],stationarity_residual=None)
 if not valid:result['reason']='original_primal_constraint_failure';return result
 normals=[g for v,g in zip(extra,Gextra) if v<=1e-6];h=2e-7
 for si,side in enumerate(['left','right']):
  if gaps[si]-.005>1e-6:continue
  p=planes(geometry,x,side);axis_gaps=p.min(0);branch=int(axis_gaps.argmax());assert abs(axis_gaps[branch]-gaps[si])<1e-12
  separation=float(np.sort(axis_gaps)[-1]-np.sort(axis_gaps)[-2]);vertices=np.flatnonzero(p[:,branch]-.005<=1e-6)
  result['axis_details'].append(dict(side=side,axis=branch,separation_m=separation,vertices=vertices.tolist(),vertex_gap_m=p[vertices,branch].tolist()))
  if separation<=2e-6:
   proof=prove_axis_stability(geometry,x,side,branch,vertices)
   result['axis_details'][-1]['axis_stability_proof']=proof
   if not proof['passed']:result['reason']='ambiguous_active_axis';return result
  assert len(vertices)
  G=np.zeros((len(vertices),11))
  for j in [1,2,3,4,6,7,8,9]:
   dq=np.eye(11)[j]*h;G[:,j]=(planes(geometry,x+dq,side)[vertices,branch]-planes(geometry,x-dq,side)[vertices,branch])/(2*h)
  normals.extend(G)
 for j in range(11):
  if x[j]-lower[j]<=2e-6:normals.append(np.eye(11)[j])
  if upper[j]-x[j]<=2e-6:normals.append(-np.eye(11)[j])
 if normals:
  A=np.array(normals);n=np.linalg.norm(A,axis=1);A=A[n>1e-12]/n[n>1e-12,None];mult,res=nnls(A.T,gradient,maxiter=1000)
 else:A=np.empty((0,11));mult=np.array([]);res=float(np.linalg.norm(gradient))
 assert np.all(mult>=0)
 result.update(passed=bool(res<=1e-6),stationarity_residual=float(res),normalized_active_normals=A.tolist(),nonnegative_multipliers=mult.tolist(),reason='stationary' if res<=1e-6 else 'stationarity_failure')
 return result

def prove_axis_stability(geometry,x,side,branch,active_vertices):
 """Bound every original +/-2e-7 single-joint FD segment by rigid rotation.
 Each unit-axis support gap is 1-Lipschitz in maximum vertex displacement.
 Hence winner separation decreases by at most twice that displacement.
 This proves local fixed-branch derivatives, not robot path clearance.
 """
 h=2e-7;reserve=1e-10
 if not np.allclose(np.linalg.norm(geometry.axes,axis=1),1.,rtol=0,atol=1e-12):
  return dict(passed=False,reason='nonunit_support_axes')
 T=np.eye(4);pivots={}
 for index,O,axis in geometry.chains[side]:
  T=T@O
  if axis is not None:
   if abs(np.linalg.norm(axis)-1)>1e-12:return dict(passed=False,reason='nonunit_joint_axis')
   if index is not None:
    if index in pivots:return dict(passed=False,reason='repeated_joint_index')
    pivots[index]=(T[:3,3].copy(),T[:3,:3]@axis)
   R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(x[index] if index is not None else 0.)).as_matrix();T=T@R
 v=geometry.v[side]@T[:3,:3].T+T[:3,3];p=planes(geometry,x,side);gaps=p.min(0)
 if int(gaps.argmax())!=branch:return dict(passed=False,reason='wrong_winning_axis')
 separation=float(gaps[branch]-np.max(np.delete(gaps,branch)))
 active_vertices=np.asarray(active_vertices,dtype=int)
 if not np.array_equal(active_vertices,np.flatnonzero(p[:,branch]-.005<=1e-6)):
  return dict(passed=False,reason='missing_active_support_vertex')
 normal=geometry.axes[branch%len(geometry.axes)]*(1 if branch<len(geometry.axes) else -1)
 analytic=np.zeros((len(active_vertices),11));finite=np.zeros_like(analytic);rows=[]
 for j in range(11):
  displacement=0.
  if j in pivots:
   pivot,axis=pivots[j];lever=v-pivot
   displacement=float(2*np.linalg.norm(np.cross(axis,lever),axis=1).max()*np.sin(h/2))
   analytic[:,j]=np.cross(axis,lever[active_vertices])@normal
  delta=np.eye(11)[j]*h;plus=planes(geometry,x+delta,side);minus=planes(geometry,x-delta,side)
  finite[:,j]=(plus[active_vertices,branch]-minus[active_vertices,branch])/(2*h)
  observed=float(max(abs(plus-p).max(),abs(minus-p).max()))
  slack=separation-2*displacement
  rows.append(dict(joint_index=j,displacement_bound_m=displacement,separation_lower_bound_m=slack,observed_projection_change_m=observed,same_winner=bool(plus.min(0).argmax()==branch==minus.min(0).argmax())))
 error=float(abs(analytic-finite).max(initial=0))
 passed=bool(separation>reserve and all(z['separation_lower_bound_m']>reserve and z['same_winner'] and z['observed_projection_change_m']<=z['displacement_bound_m']+reserve for z in rows) and error<=1e-8)
 return dict(passed=passed,reason='rigid_rotation_segment_proof' if passed else 'axis_stability_not_proven',separation_m=separation,numerical_reserve_m=reserve,finite_difference_step_rad=h,segments=rows,analytic_fd_max_error=error)
