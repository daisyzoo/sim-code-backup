"""Fixed recorded contact goals under camera bounds; offline IK only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
source=(w/'screen_lateral_camera_reach.py').read_text();exec(compile(source.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated_camera_fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference
vertices=json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'];run=w/'initial_top_short_recovery_depth_r1';results=[]
for name,frames in [('case_880003/layout_880003_push_box_to_bin',[600,840]),('case_880002/layout_880002_nudge_mailer_to_bin',[730,850])]:
 ep=run/name;side='right' if 'push_box' in name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);mesh=np.asarray(vertices[side]);coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};controls={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())}
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);intr=z['intrinsics'];shape=z['rgb'].shape
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 for t in frames:
  rec=coords[t];q0=qs[t];goal=np.array(controls[t]['target_xyz']);anchor=np.array(rec['inactive_anchor']);normal=Rotation.from_quat(ori[key][t]).as_matrix()[:,2];up=np.array(rec['contact_normal_tracking']['target_local_up']);errors={s:float(np.linalg.norm(transform(s,q0)[:3,:3]@np.array([.20,0,.007])+transform(s,q0)[:3,3]-tr['palm_'+s][t])) for s in ('left','right')};assert max(errors.values())<.0001
  yaws,fracs=camera_fraction(tr[key][t],ori[key][t],size,intr,shape[3],shape[2]);variants=[]
  for fraction in [0.,.01,.5]:
   lower=lo.copy();upper=hi.copy();allowed=np.flatnonzero(fracs>=fraction) if fraction else np.arange(len(yaws));assert len(allowed)>1 and np.all(np.diff(allowed)==1);lower[0],upper[0]=yaws[allowed[0]],yaws[allowed[-1]]
   def residual(q):
    m=transform(side,q);r=m[:3,:3];ref=projected_support_reference(mesh,r,normal);point=m[:3,3]+r@ref['reference_local'];mi=transform(inactive,q);pi=mi[:3,3]+mi[:3,:3]@np.array([.20,0,.007]);return np.r_[point-goal,pi-anchor,.15*(r.T@np.array([0.,0.,1.])-up)]
   best=None
   for start in [q0,np.zeros(11)]:
    fit=least_squares(residual,np.clip(start,lower+1e-6,upper-1e-6),bounds=(lower,upper),max_nfev=160,ftol=1e-10,xtol=1e-10,gtol=1e-10)
    if best is None or np.linalg.norm(fit.fun)<np.linalg.norm(best.fun):best=fit
   q=best.x;m=transform(side,q);gap=hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr[other][t],ori[other][t],osize);record=dict(min_bbox_fraction=fraction,waist_window_rad=[lower[0],upper[0]],active_error_m=float(np.linalg.norm(best.fun[:3])),inactive_error_m=float(np.linalg.norm(best.fun[3:6])),normal_error_rad=float(np.arccos(np.clip((m[:3,:3].T@np.array([0.,0.,1.]))@up,-1,1))),waist_rad=float(q[0]),bbox_fraction=float(np.interp(q[0],yaws,fracs)),hand_other_gap_m=float(gap),q=q.tolist());variants.append(record);print(json.dumps(dict(episode=ep.name,frame=t,**{k:v for k,v in record.items() if k!='q'})),flush=True)
  results.append(dict(episode=ep.name,frame=t,mode=controls[t]['mode'],raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),actual_fk_errors_m=errors,actual_waist_rad=float(q0[0]),actual_bbox_fraction=float(np.interp(q0[0],yaws,fracs)),rows=variants))
(run/'CURRENT_CAMERA_CONTACT_REACH.json').write_text(json.dumps(dict(rows=results,scope='Four measured states, actual projected reference (orientation-dependent), retained .15 normal constraint and inactive anchor, original calibrated camera/current joint bounds, two-start least-squares.1%/50% bbox constraints are diagnostic, not new gates. Fixed objects and instantaneous position fit: not contact/dynamics/whole-arm/table/swept-path proof, not global infeasibility, solved q must not be executed directly.',training_ready=False),indent=2))
