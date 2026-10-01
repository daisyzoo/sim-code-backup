"""Observed rear posture across repeated contact bouts. No controller changes.
World hand heading tracks the initially most horizontal local hand axis, avoiding
Euler singularities. A changing joint angle alone is not a proven causal limit.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices);out=[]
for run,cid,task in [(run,cid,task) for run in ['rear_short_recovery_groups_r1','unloaded_wrist_prior_groups_r1'] for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]]:
 ep=w/run/f'case_{cid}/layout_{cid}_{task}'
 if not (ep/'quality.json').exists():continue
 fr=json.loads((ep/'frontal_bypass.json').read_text());coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';index=10 if side=='right' else 5
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:object_yaw=np.unwrap(Rotation.from_quat(z[key]).as_euler('xyz')[:,2])
 first=next(r['step'] for r in fr['rows'] if r['mode']=='top_push');T=model.fk(side,q[first])[0];axis=int(np.argmax(np.linalg.norm(T[:2,:3],axis=0)));rotations=np.array([model.fk(side,v)[0][:3,:3] for v in q]);projected=rotations[:,:2,axis];assert min(np.linalg.norm(projected,axis=1))>.1;heading=np.unwrap(np.arctan2(projected[:,1],projected[:,0]));rows=[];last=None
 for r in fr['rows']:
  t=r['step']
  if r['mode']=='top_push' and last!='top_push':
   c=coord[t];normal=c['contact_normal_tracking'];rows.append(dict(step=t,waist_rad=float(q[t,0]),wrist_roll_rad=float(q[t,index]),shoulder_yaw_rad=float(q[t,8 if side=='right' else 3]),elbow_rad=float(q[t,9 if side=='right' else 4]),hand_heading_change_deg=float(np.rad2deg(heading[t]-heading[first])),object_yaw_change_deg=float(np.rad2deg(object_yaw[t]-object_yaw[first])),target_to_reference_mm=((np.array(r['target_xyz'])-np.array(c['control_point_positions'][side]))*1000).tolist(),normal_tracking_error_norm=float(np.linalg.norm(normal['error'])) if normal else None))
  last=r['mode']
 item=dict(episode=str(ep),horizontal_hand_axis=axis,bout_starts=rows,source_sha256={n:sha(ep/n) for n in ['raw.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']});out.append(item);print(ep.name,run,'first',rows[0],'last',rows[-1],flush=True)
(w/'UNLOADED_WRIST_POSTURE_DIAGNOSIS.json').write_text(json.dumps(dict(scope=__doc__,episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'articulated_hand_geometry.py',urdf,vertices]},training_ready=False),indent=2))
