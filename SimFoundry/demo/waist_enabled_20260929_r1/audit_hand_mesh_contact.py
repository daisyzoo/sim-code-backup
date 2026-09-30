"""Offline geometric lower bound, never a substitute for recorded forces."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,struct
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
root=Path(__file__).resolve().parent
urdf=root.parents[1]/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
xml=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in xml.findall('joint')}
def chain(side):
 link=side+'_wrist_roll_rubber_hand';out=[]
 while link in bychild:
  j=bychild[link];out.append(j);link=j.find('parent').get('link')
 return out[::-1]
def matrix(side,values):
 mat=np.eye(4);mat[:3,3]=[.08,0,.793]
 for j in chain(side):
  origin=j.find('origin');t=np.eye(4)
  if origin is not None:
   t[:3,3]=np.fromstring(origin.get('xyz','0 0 0'),sep=' ')
   t[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix()
  mat=mat@t
  if j.get('type') in ('revolute','continuous'):
   axis=np.fromstring(j.find('axis').get('xyz'),sep=' ');t=np.eye(4);t[:3,:3]=Rotation.from_rotvec(axis*values.get(j.get('name'),0)).as_matrix();mat=mat@t
 return mat
meshes={};bounds={}
for side in ['left','right']:
 p=urdf.parent/'meshes'/f'{side}_wrist_roll_rubber_hand.STL';b=p.read_bytes();count=struct.unpack('<I',b[80:84])[0]
 assert len(b)==84+50*count
 dtype=np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attr','<u2')])
 vertices=np.frombuffer(b[84:],dtype=dtype)['vertices'].reshape(-1,3)
 vertices=np.unique(vertices,axis=0);hull=ConvexHull(vertices);meshes[side]=vertices[hull.vertices]
 bounds[side]=dict(min=vertices.min(axis=0).tolist(),max=vertices.max(axis=0).tolist(),hull_vertices=len(hull.vertices))
rows=[]
for ep in sorted((root/'development32_r1').glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 side='right' if 'push_box' in ep.name else 'left';target='box' if side=='right' else 'mailer'
 names=['waist_yaw_joint']+[f'{side}_{s}_joint' for s in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']]
 indices=[12,*range(18,23)] if side=='right' else [12,*range(13,18)]
 with np.load(ep/'raw.npz') as z,np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  errors=[];gaps=[]
  half=np.array([.14,.09,.045] if target=='box' else [.15,.145,.04])/2
  for t,q in enumerate(z['q'][:,indices]):
   mat=matrix(side,dict(zip(names,q)))
   errors.append(np.max(abs((mat@np.array([.20,0,.007,1]))[:3]-tr['palm_'+side][t])))
   world=meshes[side]@mat[:3,:3].T+mat[:3,3]
   objrot=Rotation.from_quat(ori[target][t]).as_matrix()
   local=(world-tr[target][t])@objrot
   sep=np.maximum(np.maximum(-half-local.max(axis=0),local.min(axis=0)-half),0)
   gaps.append(float(np.linalg.norm(sep)))
  ix=int(np.argmin(gaps));quality=json.loads((ep/'quality.json').read_text())
  rows.append(dict(episode=str(ep.relative_to(root)),target=target,numeric_pass=quality['passed'],fk_error_m=float(max(errors)),min_mesh_envelope_gap_m=gaps[ix],closest_recorded_frame=ix,frames_envelope_overlap=sum(g<=1e-6 for g in gaps),initial_target_xyz=tr[target][0].tolist(),target_displacement_max_m=float(np.linalg.norm(tr[target]-tr[target][0],axis=1).max())))
result=dict(mesh_bounds=bounds,rows=rows,scope='URDF hand convex-envelope AABB in recorded object frame, each pre-action sample. Positive gap is a geometric separation lower bound at those samples. AABB overlap is NOT collision proof. Not all physics substeps, not confirmation of engine collision decomposition.',training_ready=False)
(root/'HAND_MESH_CONTACT_AUDIT.json').write_text(json.dumps(result,indent=2))
for row in rows:print(row['episode'],round(row['min_mesh_envelope_gap_m'],4),row['frames_envelope_overlap'],row['numeric_pass'])
