"""Conservative local support-axis dominance bound; no acceptance certificate.
For |dq_j|<=rho, rotating a downstream vertex of radius r about an axis a moves
it by at most r*||a||*rho, because 2*sin(|angle|/2)<=|angle|. A telescoping sum
bounds simultaneous joint changes. Every vertex projection then has this bound,
and taking the minimum preserves it. Compare the chosen axis lower bound to
ALL other axis upper bounds. Never substitute this for original task/IK audits.
"""
import numpy as np
from support_vertex_stationarity import planes

def inspect_local_dominance(geometry,x,side,*,radius_rad=2e-7):
 x=np.asarray(x,float)
 if x.shape!=(11,) or not np.isfinite(x).all() or side not in ('left','right'):raise ValueError('Invalid configuration/side')
 if not np.isfinite(radius_rad) or radius_rad<=0:raise ValueError('Invalid radius')
 chain=geometry.chains[side];v=np.asarray(geometry.v[side]);axes=np.asarray(geometry.axes)
 if v.ndim!=2 or v.shape[1]!=3 or axes.ndim!=2 or axes.shape[1]!=3 or not np.isfinite(v).all() or not np.isfinite(axes).all():raise ValueError('Invalid vertices or projection axes')
 if np.any(np.linalg.norm(axes,axis=1)<1e-12):raise ValueError('Zero projection axis')
 factors=[];translations=[]
 for index,O,axis in chain:
  if np.shape(O)!=(4,4) or not np.isfinite(O).all():raise ValueError('Invalid rigid transform')
  if not np.allclose(O[:3,:3].T@O[:3,:3],np.eye(3),atol=1e-12,rtol=0):raise ValueError('Nonrigid archived transform')
  if axis is not None and (np.shape(axis)!=(3,) or not np.isfinite(axis).all()):raise ValueError('Invalid rotation axis')
  # Padding makes the computed matrix-norm upper bounds conservative relative
  # to floating-point roundoff; this is not an original geometry gate change.
  factors.append(max(1.,float(np.linalg.norm(O[:3,:3],2)))+1e-12);translations.append(float(np.linalg.norm(O[:3,3]))+1e-12)
 contributions=[]
 for i,(index,O,axis) in enumerate(chain):
  if index is None or axis is None:continue
  reach=float(np.linalg.norm(v,axis=1).max())+1e-12
  for k in range(len(chain)-1,i,-1):reach=factors[k]*reach+translations[k]
  upstream=float(np.prod(factors[:i+1]));axis_norm=float(np.linalg.norm(axis))+1e-12;bound=upstream*reach*axis_norm*radius_rad
  contributions.append(dict(joint_index=int(index),downstream_radius_bound_m=reach,upstream_operator_bound=upstream,joint_axis_norm_bound=axis_norm,vertex_displacement_bound_m=bound))
 displacement=sum(r['vertex_displacement_bound_m'] for r in contributions)
 axis_norms=np.tile(np.linalg.norm(axes,axis=1)+1e-12,2);projection_bounds=displacement*axis_norms+1e-10
 p=planes(geometry,x,side);gaps=p.min(0);chosen=int(gaps.argmax());other=np.arange(len(gaps))!=chosen;lower=gaps-projection_bounds;upper=gaps+projection_bounds;separation=lower[chosen]-upper[other];competitors=np.flatnonzero(other);worst=int(competitors[int(separation.argmin())]);ordered=np.argsort(gaps)[::-1];near=ordered[gaps[chosen]-gaps[ordered]<=2e-6]
 return dict(side=side,scope=__doc__,joint_box_radius_rad=radius_rad,chosen_axis=chosen,original_near_axis_threshold_m=2e-6,original_unique_axis_test_passes=bool(gaps[ordered[0]]-gaps[ordered[1]]>2e-6),vertex_position_change_bound_m=displacement,projection_roundoff_allowance_m=1e-10,all_competitors_checked=int(other.sum()),worst_competitor=worst,guaranteed_axis_separation_m=float(separation.min()),strict_local_dominance=bool(np.all(separation>0)),contributions=contributions,near_axes=[dict(axis=int(i),center_gap_m=float(gaps[i]),lower_gap_m=float(lower[i]),upper_gap_m=float(upper[i]),cannot_meet_original_primal_floor_anywhere_in_box=bool(upper[i]<.005-2e-7)) for i in near],original_audit_changed=False,training_ready=False)
