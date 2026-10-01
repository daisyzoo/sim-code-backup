"""Offline per-bout orientation hold reach screen on measured goals."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
s=(w/'screen_lateral_camera_reach.py').read_text();exec(compile(s.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated_fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference
run=w/'y_path_nearhalf_groups_r1';ep=run/'case_897003/layout_897003_nudge_mailer_to_bin';mesh=np.asarray(json.loads((repo/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices']['left'])
with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};controls={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};bout_report=json.loads((run/'LOADED_HAND_TWIST.json').read_text());results=[]
for bout in [bout_report['bouts'][i] for i in [0,3,6]]:
 start=bout['first_push'];orientation=transform('left',qs[start])[:3,:3]
 for t in sorted(set([min(start+20,bout['last_push']),bout['last_push']])):
  q0=qs[t];goal=np.array(controls[t]['target_xyz']);anchor=np.array(coords[t]['inactive_anchor']);normal=Rotation.from_quat(ori['mailer'][t]).as_matrix()[:,2];up=np.array(coords[t]['contact_normal_tracking']['target_local_up'])
  for full in [False,True]:
   def residual(q):
    m=transform('left',q);rot=m[:3,:3];ref=projected_support_reference(mesh,rot,normal);point=m[:3,3]+rot@ref['reference_local'];mi=transform('right',q);pi=mi[:3,3]+mi[:3,:3]@np.array([.20,0,.007]);angular=Rotation.from_matrix(rot@orientation.T).as_rotvec() if full else rot.T@np.array([0.,0.,1.])-up
    return np.r_[point-goal,pi-anchor,.15*angular]
   best=None
   for initial in [q0,qs[start]]:
    fit=least_squares(residual,np.clip(initial,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=160,ftol=1e-10,xtol=1e-10,gtol=1e-10)
    if best is None or np.linalg.norm(fit.fun)<np.linalg.norm(best.fun):best=fit
   q=best.x;m=transform('left',q);ref=projected_support_reference(mesh,m[:3,:3],normal);low=m[:3,3]+m[:3,:3]@ref['lowest_vertex_local'];local=Rotation.from_quat(ori['mailer'][t]).inv().apply(low-tr['mailer'][t]);r=dict(bout_start=start,frame=t,full_orientation_hold=full,goal=goal.tolist(),active_error_m=float(np.linalg.norm(best.fun[:3])),inactive_error_m=float(np.linalg.norm(best.fun[3:6])),angular_residual_norm=float(np.linalg.norm(best.fun[6:])/.15),solver_success=bool(best.success),nfev=best.nfev,hand_other_gap_m=float(hand_face_separation('left').gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),tr['box'][t],ori['box'][t],(.14,.09,.045))),lowest_vertex_target_local_xyz=local.tolist(),lowest_vertex_inside_xy=bool(abs(local[0])<=.075 and abs(local[1])<=.0725),q=q.tolist());results.append(r);print(json.dumps({k:v for k,v in r.items() if k!='q'}),flush=True)
report=dict(rows=results,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),scope='Measured goals at start/middle/late contact bouts, current projected-support reference and original inactive anchor/bounds. Compare original normal tracking with orientation latched at start of each bout; two-start static fitting only. Not dynamic pose holding, force/slip/yaw improvement, whole-arm or path certification. Different residual semantics: full rotvec norm vs normal chord. No production change, no direct execution of q.',training_ready=False)
(run/'CONTACT_BOUT_ORIENTATION_SCREEN.json').write_text(json.dumps(report,indent=2))
