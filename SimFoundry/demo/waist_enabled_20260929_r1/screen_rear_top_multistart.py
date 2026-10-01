"""Offline multi-start IK at real stalled rear-box state; never execute solved q."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
source=(w/'screen_lateral_camera_reach.py').read_text()
exec(compile(source.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated_fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.data.top_contact_bypass import top_surface_point
run=w/'current_lateral_profile_r1';ep=run/'case_895001/layout_895001_push_box_to_bin'
with np.load(ep/'raw.npz') as z:q0=z['q'][1199,12:23].astype(float)
with np.load(ep/'trace.npz') as z:tr={k:z[k][1199] for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][1199] for k in z.files}
coord=json.loads((ep/'coordination.json').read_text())[-1];assert coord['step']==1199 and coord['contact_normal_tracking'] is None
anchor=np.asarray(coord['inactive_anchor']);mesh=np.array(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices']['right']);normal=Rotation.from_quat(ori['box']).as_matrix()[:,2]
errors={s:float(np.linalg.norm(transform(s,q0)[:3,3]+transform(s,q0)[:3,:3]@np.array([.20,0,.007])-tr['palm_'+s])) for s in ('left','right')};assert max(errors.values())<.0001
surface=np.array(top_surface_point(tr['box'],ori['box'],(.14,.09,.045)))
rng=np.random.default_rng(2026093002);starts=[q0,np.zeros(11),rng.uniform(lo,hi)]
rows=[]
for name,height in [('cross',.91),('contact',float(surface[2]+.004))]:
 goal=np.r_[surface[:2],height]
 for keep_inactive in [True,False]:
  def residual(q):
   m=transform('right',q);ref=projected_support_reference(mesh,m[:3,:3],normal);point=m[:3,3]+m[:3,:3]@ref['reference_local'];other=transform('left',q);delta=other[:3,3]+other[:3,:3]@np.array([.20,0,.007])-anchor
   return np.r_[point-goal,delta] if keep_inactive else point-goal
  fits=[]
  for i,start in enumerate(starts):
   fit=least_squares(residual,np.clip(start,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=200,ftol=1e-10,gtol=1e-10,xtol=1e-10)
   q=fit.x;m=transform('right',q);ref=projected_support_reference(mesh,m[:3,:3],normal);point=m[:3,3]+m[:3,:3]@ref['reference_local'];mi=transform('left',q);pi=mi[:3,3]+mi[:3,:3]@np.array([.20,0,.007]);low=m[:3,3]+m[:3,:3]@ref['lowest_vertex_local'];delta_local=Rotation.from_quat(ori['box']).inv().apply(low-tr['box'])
   fits.append(dict(start=i,active_error_m=float(np.linalg.norm(point-goal)),inactive_error_m=float(np.linalg.norm(pi-anchor)),residual_norm=float(np.linalg.norm(fit.fun)),nfev=fit.nfev,solver_success=bool(fit.success),waist_rad=float(q[0]),hand_other_gap_m=float(hand_face_separation('right').gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr['mailer'],ori['mailer'],(.15,.145,.04))),lowest_vertex_local_target_xyz=delta_local.tolist(),lowest_vertex_inside_top_xy=bool(abs(delta_local[0])<=.07 and abs(delta_local[1])<=.045),q=q.tolist()))
  best=min(fits,key=lambda f:f['residual_norm']);row=dict(phase=name,inactive_anchor_constraint=keep_inactive,goal=goal.tolist(),best=best,starts=fits);rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='starts'}),flush=True)
result=dict(episode=ep.name,frame=1199,actual_fk_errors_m=errors,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,scope='Three-start bounded nonlinear position IK, actual projected support/box pose and original bounds; contact-normal constraint is absent at actual prepress phase. Compare retained versus removed inactive anchor as diagnosis only. Fixed object/instantaneous pose, not global infeasibility, dynamics, swept path, all-arm collision or task success proof. Never directly execute solved q.',training_ready=False)
(run/'REAR_TOP_MULTISTART_REACH.json').write_text(json.dumps(result,indent=2))
