from pathlib import Path
import json,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
urdf=root.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')}
def chain(side):
 link=side+'_wrist_roll_rubber_hand';out=[]
 while link in bychild:
  j=bychild[link];out.append(j);link=j.find('parent').get('link')
 return out[::-1]
def fk(side,q):
 mat=np.eye(4);mat[:3,3]=[.08,0,.793]
 for j in chain(side):
  orig=j.find('origin');t=np.eye(4)
  if orig is not None:
   t[:3,3]=np.fromstring(orig.get('xyz','0 0 0'),sep=' ');t[:3,:3]=Rotation.from_euler('xyz',np.fromstring(orig.get('rpy','0 0 0'),sep=' ')).as_matrix()
  mat=mat@t
  if j.get('type') in ('revolute','continuous'):
   axis=np.fromstring(j.find('axis').get('xyz'),sep=' ');r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(j.get('name'),0)).as_matrix();mat=mat@r
 return (mat@np.array([.20,0,.007,1]))[:3]
rows=[];errors=[]
for side,task,indices in [('left','nudge_mailer_to_bin',range(13,18)),('right','push_box_to_bin',range(18,23))]:
 names=['waist_yaw_joint']+[f'{side}_{suffix}_joint' for suffix in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']]
 ep=root/f'rear_bypass_r1/layout_61001_{task}'
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr:
  states=z['q'][:,[12,*indices]]
  for t in [0,30,100,319]:errors.append(float(np.max(abs(fk(side,dict(zip(names,states[t])))-tr['palm_'+side][t]))))
  initial=states[-1].copy()
 bypass=json.loads((ep/'bypass.json').read_text())[-1];target=np.array(bypass['palm_target'])
 for limit in [.20,.65]:
  lo=[-limit];hi=[limit]
  for name in names[1:]:
   j=next(j for j in xml.findall('joint') if j.get('name')==name);lo.append(float(j.find('limit').get('lower')));hi.append(float(j.find('limit').get('upper')))
  lo=np.array(lo);hi=np.array(hi);rng=np.random.default_rng(929);best=None
  for q in [np.clip(initial,lo+1e-6,hi-1e-6),*rng.uniform(lo,hi,(12,6))]:
   fit=least_squares(lambda q:fk(side,dict(zip(names,q)))-target,q,bounds=(lo,hi),max_nfev=250)
   error=float(np.linalg.norm(fit.fun))
   if best is None or error<best['error_m']:best=dict(error_m=error,joint_names=names,joint_angles=fit.x.tolist(),palm=fk(side,dict(zip(names,fit.x))).tolist())
  rows.append(dict(side=side,waist_limit_rad=limit,target=target.tolist(),best=best))
result=dict(fk_max_abs_error_vs_sim_m=max(errors),rows=rows,limitations='URDF FK plus multistart position-only IK. Does not enforce collision/visibility/inactive-arm/dynamics; failure to find a pose is not a proof of infeasibility. Do not deploy solved poses directly.',training_ready=False)
(root/'KINEMATIC_REACH_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
