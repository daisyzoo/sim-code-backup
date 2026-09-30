"""Two-sided object-envelope bypass and static top-contact reach; no sim commands."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split('results=[];rng')[0],'<cached_fk>','exec'))
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
from simfoundry.data.frontal_bypass import extent_x_from_quat
p=Path(sys.argv[1]).resolve();z=np.load(p/'raw.npz');tr=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');side='right' if 'push_box' in p.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);other_size=np.array([.15,.145,.04] if other=='mailer' else [.14,.09,.045]);other_core=np.array([.135,.1276,.04] if other=='mailer' else [.1344,.0864,.045]);target=tr[key][0].copy();obstacle=tr[other][0];quat=ori[key][0];rotation=Rotation.from_quat(quat).as_matrix();normal=rotation[:,2];radius=extent_x_from_quat(size,quat);other_radius=extent_x_from_quat(other_size,ori[other][0]);routes={'front':obstacle[0]-radius-other_radius-.02,'rear':obstacle[0]+radius+other_radius+.02};goal_y=direction*max(.205,direction*target[1]+.16)
mesh=np.asarray(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side]);q_initial=z['q'][40,12:23].astype(float);inactive_target=tr['palm_'+inactive][40];lo[0]=-1.;hi[0]=1.;rng=np.random.default_rng(92908)
def matrix_at(which,values):
 q=dict(zip(names,values));m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[which]:
  m=m@origin
  if axis is not None:a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 return m

def points_at(q):
 m=matrix_at(side,q);v=mesh@m[:3,:3].T+m[:3,3];a=v[np.argmin(v@normal)];b=(matrix_at(inactive,q)@np.array([.20,0,.007,1]))[:3];return a,b,m
results=[]
for route,x in routes.items():
 table_margin=min(x-radius-.28,.88-x-radius)
 if table_margin<0:results.append(dict(route=route,object_x=float(x),table_margin_m=float(table_margin),object_envelope_eligible=False));continue
 for contact in ['front_inset20mm','center','rear_inset20mm']:
  local=np.array([{'front_inset20mm':-size[0]/2+.02,'center':0.,'rear_inset20mm':size[0]/2-.02}[contact],0.,size[2]/2]);q_prev=q_initial.copy()
  for phase,position in [('initial_contact',target),('after_x_reposition',np.array([x,target[1],target[2]])),('cross_other_y',np.array([x,obstacle[1],target[2]])),('goal',np.array([x,goal_y,target[2]]))]:
   desired=position+rotation@local+normal*.002;solutions=[]
   for initial in [q_prev,np.clip(q_initial+rng.normal(0,.15,11),lo+1e-6,hi-1e-6)]:
    def residual(q):
     a,b,_=points_at(q);return np.r_[a-desired,b-inactive_target]
    opt=least_squares(residual,np.clip(initial,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9);a,b,m=points_at(opt.x);gap=hand_face_separation(side).gap(m[:3,3],Rotation.from_matrix(m[:3,:3]).as_quat(),obstacle,ori[other][0],other_core)
    solutions.append(dict(active_error_m=float(np.linalg.norm(a-desired)),inactive_error_m=float(np.linalg.norm(b-inactive_target)),hand_other_face_axis_gap_m=float(gap),q=opt.x.tolist(),solver_success=bool(opt.success)))
   best=min(solutions,key=lambda a:a['active_error_m']+a['inactive_error_m']);q_prev=np.array(best['q']);record=dict(route=route,contact=contact,phase=phase,object_x=float(position[0]),object_y=float(position[1]),table_margin_m=float(table_margin),object_envelope_eligible=True,**best);results.append(record);print(route,contact,phase,round(best['active_error_m']*1000,3),'mm gap',round(best['hand_other_face_axis_gap_m']*1000,3),flush=True)
report=dict(episode=p.name,initial_target_xyz=target.tolist(),obstacle_xyz=obstacle.tolist(),routes=routes,rows=results,scope='Read-only initial-yaw rectangle envelopes with20mm object clearance and original table footprint bounds. Independent URDF static actual-hand support IK,2 starts per point, waist1rad and recorded inactive palm anchor. Positive face-axis gap certifies separation on a tested axis only at that hypothetical pose; no edge-cross axes, all-arm, loaded-contact, dynamic path, visibility or global reachability proof. Hypothetical object moves are never applied to simulator. Initial_contact rows are repeated for solver warm-start comparison.',training_ready=False)
(p/'FRONT_REAR_ROUTE_REACH.json').write_text(json.dumps(report,indent=2))
