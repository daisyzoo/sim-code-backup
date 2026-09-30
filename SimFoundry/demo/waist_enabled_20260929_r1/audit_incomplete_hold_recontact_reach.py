"""Read-only static reach at a failed ordinary-route hold, not dynamic success."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.top_contact_bypass import top_surface_point
p=Path(sys.argv[1]).resolve();raw=np.load(p/'raw.npz');trace=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');control=json.loads((p/'expert_control.json').read_text());task=str(raw['task_id']);side='right' if task=='push_box_to_bin' else 'left';other='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
mesh=np.asarray(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);size=(.14,.09,.045) if key=='box' else (.15,.145,.04);normal=Rotation.from_quat(ori[key][-1]).as_matrix()[:,2];q0=raw['q'][-1,12:23].astype(float);lo[0]= -1.;hi[0]=1.;inactive_target=trace['palm_'+other][-1]
def hand_matrix(which,values):
 q=dict(zip(names,values));m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[which]:
  m=m@origin
  if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 return m

def measured(values):
 m=hand_matrix(side,values);vertices=mesh@m[:3,:3].T+m[:3,3];active=vertices[np.argmin(vertices@normal)];inactive=(hand_matrix(other,values)@np.array([.20,0,.007,1]))[:3];return active,inactive
position=trace[key][-1].copy();surface=np.asarray(top_surface_point(position,ori[key][-1],size));final=position.copy();final[1]=direction*max(.205,direction*trace[key][0,1]+.155);end=np.asarray(top_surface_point(final,ori[key][-1],size));points=[('above_current_contact',np.r_[surface[:2],.91]),('current_contact',surface+normal*.002),('goal_contact_nominal_constant_x',end+normal*.002)]
for forward in (.02,.04):
 hypothetical=final.copy();hypothetical[0]-=forward;point=np.asarray(top_surface_point(hypothetical,ori[key][-1],size))+normal*.002
 points.append((f'goal_contact_if_object_physically_moves_front_{forward:.2f}m',point))
rng=np.random.default_rng(20260929);results=[]
for label,target in points:
 candidates=[]
 for initial in [q0,*[np.clip(q0+rng.normal(0,.12,11),lo+1e-6,hi-1e-6) for _ in range(3)]]:
  def residual(q):
   active,inactive=measured(q);return np.r_[active-target,inactive-inactive_target]
  opt=least_squares(residual,np.clip(initial,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=140,ftol=1e-10,xtol=1e-10,gtol=1e-10)
  active,inactive=measured(opt.x);candidates.append(dict(active_error_m=float(np.linalg.norm(active-target)),inactive_error_m=float(np.linalg.norm(inactive-inactive_target)),q=opt.x.tolist(),solver_success=bool(opt.success)))
 best=min(candidates,key=lambda c:c['active_error_m']+c['inactive_error_m']);results.append(dict(waypoint=label,target_xyz=target.tolist(),**best));print(label,best['active_error_m'],best['inactive_error_m'],flush=True)
hold=next((r['step'] for r in control if r['mode']=='hold'),None)
report=dict(episode=p.name,final_target_xyz=position.tolist(),first_hold_step=hold,frames=len(raw['q']),target_xy_motion_during_hold_m=float(np.linalg.norm(trace[key][-1,:2]-trace[key][hold,:2])) if hold is not None else None,rows=results,scope='Independent full11D static URDF IK using actual hand support vertex and recorded inactive palm;4 starts per pose, waist within1rad. No physical commands executed, no collision/path/load/visibility proof. Nominal goal retains final measured object X/orientation; two alternatives hypothetically move object X20/40mm toward robot. These are hypothetical static object poses, NOT applied pose edits or proven physical paths; actual pushing may differ. Tests plausibility of adding measured-target top recontact when ordinary sweep ends outside goal; does not approve that controller or data.',training_ready=False)
(p/'INCOMPLETE_HOLD_RECONTACT_REACH.json').write_text(json.dumps(report,indent=2))
