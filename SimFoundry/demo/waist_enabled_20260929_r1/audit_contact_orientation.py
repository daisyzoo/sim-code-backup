"""Read-only FK and pose feasibility; never commands the simulated robot."""
from pathlib import Path
import ast,json,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
urdf=root.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')}
# Exact already FK-validated functions, without executing the source audit body.
src=ast.parse((root/'audit_hand_mesh_contact.py').read_text())
exec(compile(ast.Module(body=[n for n in src.body if isinstance(n,ast.FunctionDef) and n.name in ['chain','matrix']],type_ignores=[]),'<validated_fk>','exec'))
rows=[];observations=[];rng=np.random.default_rng(929)
for side,task,indices in [('left','nudge_mailer_to_bin',[12,*range(13,18)]),('right','push_box_to_bin',[12,*range(18,23)])]:
 names=['waist_yaw_joint']+[f'{side}_{s}_joint' for s in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']]
 layout=62004 if side=='left' else 62005
 ep=root/f'development32_r1/case_{layout}/layout_{layout}_{task}'
 with np.load(ep/'raw.npz') as z:
  states=z['q'][:,indices].copy()
 for t in [30,60,90,120,159]:
  mat=matrix(side,dict(zip(names,states[t])))
  observations.append(dict(side=side,layout=layout,frame=t,palm=(mat@np.array([.2,0,.007,1]))[:3].tolist(),finger_world_axis=mat[:3,0].tolist(),rotation_from_flat_rad=float(Rotation.from_matrix(mat[:3,:3]).magnitude())))
 lo=[-.63];hi=[.63]
 for name in names[1:]:
  j=next(j for j in xml.findall('joint') if j.get('name')==name);lo.append(float(j.find('limit').get('lower')));hi.append(float(j.find('limit').get('upper')))
 lo=np.array(lo);hi=np.array(hi)
 for y in [-.12,0,.22]:
  # Contact palm chosen .06m torso-side of far object; fingers extend .053m beyond palm.
  target=np.array([.54, y if side=='left' else -y, .830 if side=='left' else .835])
  def residual(q):
   m=matrix(side,dict(zip(names,q)))
   return np.r_[(m@np.array([.2,0,.007,1]))[:3]-target,.15*Rotation.from_matrix(m[:3,:3]).as_rotvec()]
  best=None
  for q in [np.clip(states[60],lo+1e-6,hi-1e-6),np.zeros(6),*rng.uniform(lo,hi,(4,6))]:
   fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=220)
   value=float(np.linalg.norm(fit.fun))
   if best is None or value<best['weighted_residual']:
    best=dict(weighted_residual=value,position_error_m=float(np.linalg.norm(fit.fun[:3])),orientation_error_rad=float(np.linalg.norm(fit.fun[3:])/.15),q=fit.x.tolist())
  rows.append(dict(side=side,target=target.tolist(),flat_orientation=np.eye(3).tolist(),best=best))
result=dict(observations=observations,pose_solutions=rows,limitations='Offline bounded multistart IK with .15m orientation scaling. No collision/path/dynamics or inactive-arm constraints; nonzero residual is not global infeasibility proof. Solved poses must not be applied directly.',training_ready=False)
(root/'CONTACT_ORIENTATION_FEASIBILITY.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
