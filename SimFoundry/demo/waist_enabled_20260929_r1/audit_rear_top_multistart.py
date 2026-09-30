"""Bounded multistart positional IK screen, no execution or dynamics."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
src=(root/'audit_front_contact_fraction_kinematics.py').read_text();exec(compile(src.split('actual=next(r for r in rows')[0],'<measured_fk>','exec'))
from simfoundry.data.hand_obstacle_clearance import ConvexFaceSeparation
other_quat=ori[other_key][start];other_size=np.array([.14,.09,.045] if side=='left' else [.15,.145,.04]);other_radius=(abs(Rotation.from_quat(other_quat).as_matrix())@other_size/2)[0];rear_x=float(obstacle[0]+other_radius+np.linalg.norm(size[:2]/2)+.012+.003);direction=log['plan']['direction'];goal_y=direction*max(.205,direction*log['plan']['initial_target_xyz'][1]+.16)
rng=np.random.default_rng(930);starts=[initial.copy(),np.zeros(11),*rng.uniform(lo+1e-5,hi-1e-5,(8,11))];results=[];separation=ConvexFaceSeparation(vertices)
for center in [np.array([.63,target[1],target[2]]),np.array([rear_x,target[1],target[2]]),np.array([rear_x,goal_y,target[2]])]:
 desired=np.array(top_surface_point(center,quat,size,front_inset_fraction=None))+normal*.002
 for coupled in [True,False]:
  def residual_jac(q):
   m,jl,jw=fk(side,q);rotation=m[:3,:3];ref=projected_support_reference(vertices,rotation,normal);point=m[:3,3]+rotation@ref['reference_local'];ja=projected_support_jacobian(jl,jw,rotation,ref)
   if not coupled:return point-desired,ja
   mi,jli,jwi=fk(other_side,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
   return np.r_[point-desired,pi-anchor],np.vstack([ja,ji])
  candidates=[]
  for n,q0 in enumerate(starts):
   fit=least_squares(lambda q:residual_jac(q)[0],np.clip(q0,lo+1e-6,hi-1e-6),jac=lambda q:residual_jac(q)[1],bounds=(lo,hi),max_nfev=240)
   error=residual_jac(fit.x)[0];m,_,_=fk(side,fit.x);rotation=m[:3,:3];gap=separation.gap(m[:3,3],Rotation.from_matrix(rotation).as_quat(),obstacle,other_quat,other_size)
   heights=vertices@(rotation.T@normal);near=vertices[heights-heights.min()<=.0002];local=((m[:3,3]+near@rotation.T)-center)@rp;scale=np.array([.96,.96] if side=='right' else [.90,.88]);margin=float(np.min(size[:2]*scale/2-np.abs(local[:,:2])))
   candidates.append(dict(start=n,error_norm_m=float(np.linalg.norm(error)),active_error_xyz_m=error[:3].tolist(),inactive_error_xyz_m=error[3:].tolist(),q=fit.x.tolist(),hand_other_face_gap_m=gap,near_support_core_margin_m=margin,nfev=fit.nfev,solver_success=bool(fit.success)))
  best=min(candidates,key=lambda r:r['error_norm_m']);record=dict(hypothetical_target_xyz=center.tolist(),desired_reference_xyz=desired.tolist(),coupled=coupled,best=best,candidates=candidates);results.append(record);print(json.dumps({k:v for k,v in record.items() if k!='candidates'}),flush=True)
out=dict(rows=results,waist_limit_rad=.98,starts_per_condition=len(starts),raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Fixed hypothetical parcel poses; multistart bounded position IK only. Free-inactive cases omit its world anchor and can be unsafe. Isolated endpoint solution does not certify continuous route, contact forces or reach under dynamics. Failure is not global infeasibility proof. No commands executed.',training_ready=False)
(p/'REAR_TOP_MULTISTART.json').write_text(json.dumps(out,indent=2))
