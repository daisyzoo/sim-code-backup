"""Offline contact-centred full hand orientation IK screen, never executed."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]);normal_only='--normal-only' in sys.argv[2:];virtual_reference='--virtual-reference' in sys.argv[2:];assert 'nudge_mailer' in p.name
with np.load(p/'raw.npz') as z:qs=z['q']
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
with np.load(p/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
mesh=np.asarray(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices']['left']);coord={x['step']:x for x in json.loads((p/'coordination.json').read_text())};cop=json.loads((p/'LOADED_CONTACT_OFFSETS.json').read_text())['records'];acq=json.loads((p/'CONTACT_PATCH_REACQUISITION.json').read_text())['rows'];lo[0]=-.98;hi[0]=.98

def transform(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q[names.index(name)]).as_matrix();m=m@a
 return m
results=[]
for acquisition in acq:
 t=acquisition['push_start'];contact=next(x for x in cop if t<=x['controller_step']<t+20);t=contact['controller_step'];q0=qs[t,12:23].astype(float);m0=transform('left',q0);orientation=m0[:3,:3];center_world=tr['mailer'][t].copy();center_world[:2]+=contact['contact_minus_target_xy_m'];center_world[2]+= .02
 # Only tangential X/Y of measured COP is used; normal coordinate lies on the
 # true mesh supporting plane at the selected fixed world orientation.
 local=(mesh.min(0)+mesh.max(0))/2 if virtual_reference else orientation.T@(center_world-m0[:3,3]);nlocal=orientation.T@np.array([0.,0.,1.]);local+=nlocal*((mesh@nlocal).min()-local@nlocal)
 anchor=np.array(coord[t]['inactive_anchor']);previous=q0.copy();paths=[]
 for y in [-.12,-.06,0.,.06,.12,.18,.205]:
  goal=np.array([.3675 if virtual_reference else .375,y,.7899758])
  def residual(q):
   left=transform('left',q);right=transform('right',q)
   return np.r_[left[:3,:3]@local+left[:3,3]-goal,right[:3,:3]@np.array([.20,0,.007])+right[:3,3]-anchor,.15*((left[:3,:3].T@np.array([0.,0.,1.])-orientation.T@np.array([0.,0.,1.])) if normal_only else Rotation.from_matrix(left[:3,:3]@orientation.T).as_rotvec())]
  best=None
  for initial in [previous,q0,np.zeros(11)]:
   fit=least_squares(residual,np.clip(initial,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=200,ftol=1e-10,xtol=1e-10,gtol=1e-10)
   if best is None or np.linalg.norm(fit.fun)<np.linalg.norm(best.fun):best=fit
  previous=best.x;left=transform('left',best.x);h=mesh@left[:3,:3].T+left[:3,3];near=h[h[:,2]-h[:,2].min()<.0002]
  target_margin=float(np.min(np.array([.135,.1276])/2-abs(near[:,:2]-goal[:2])))
  row=dict(goal=goal.tolist(),active_error_m=float(np.linalg.norm(best.fun[:3])),inactive_error_m=float(np.linalg.norm(best.fun[3:6])),orientation_error_deg=float(np.degrees(2*np.arcsin(np.clip(np.linalg.norm(best.fun[6:])/.30,0,1))) if normal_only else np.degrees(np.linalg.norm(best.fun[6:])/.15)),waist_rad=float(best.x[0]),near_lowest_support_core_xy_margin_m=target_margin,q=best.x.tolist())
  row['kinematic_tolerances_met']=row['active_error_m']<=.005 and row['inactive_error_m']<=.005 and row['orientation_error_deg']<=2.;paths.append(row)
 results.append(dict(measured_contact_frame=t,hand_orientation_world_matrix=orientation.tolist(),fixed_contact_tangent_reference_local=local.tolist(),rows=paths,all_waypoint_kinematics_met=all(x['kinematic_tolerances_met'] for x in paths)))
 print(t,[(round(x['active_error_m']*1000,2),round(x['orientation_error_deg'],2),x['kinematic_tolerances_met']) for x in paths],flush=True)
out=dict(reference_kind='existing_virtual_center_with_front0.9' if virtual_reference else 'contact_tangent_centered',orientation_mode='local_up_normal_only' if normal_only else 'full_world_rotation',results=results,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','LOADED_CONTACT_OFFSETS.json','CONTACT_PATCH_REACQUISITION.json']},scope='Offline multistart position+orientation IK of frozen sampled hand postures. Hypothetical flat parcel top and front path, contact-tangent reference from measured COP, inactive palm retained, bounded waist. Five-mm/2deg are screen tolerances, not original quality gates. No collision planner, dynamics, friction/rotation proof, continuous trajectory or executed actions. Failure is not global infeasibility proof.',training_ready=False)
(p/(('FIXED_VIRTUAL_NORMAL_SCREEN.json' if virtual_reference else 'FIXED_CONTACT_NORMAL_SCREEN.json') if normal_only else 'FIXED_CONTACT_POSE_SCREEN.json')).write_text(json.dumps(out,indent=2))
