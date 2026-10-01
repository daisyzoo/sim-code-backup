"""Measured contact force moments about parcel center, not a tipping prediction.
Uses final-substep force samples aligned to next observation. Point-force moments
exclude any solver contact torque and do not integrate a control interval. Normal
and tangential components below are parcel-local, not a claim about net torque.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for run in ['rear_short_recovery_groups_r1','unloaded_wrist_prior_groups_r1','recontact_pose_groups_r1']:
 ep=w/run/'case_840001/layout_840001_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 with np.load(ep/'trace.npz') as z:xyz=z['box'].copy()
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z['box']).as_matrix()
 records=[]
 for row in fr:
  t=row['step']
  if row['mode']!='top_push' or t-1 not in packets:continue
  packet=packets[t-1];assert np.max(abs(np.array(packet['post_action_pose']['box'])-xyz[t]))<1e-6
  forces=[];points=[];normal_moment=np.zeros(3);tangent_moment=np.zeros(3)
  for c in packet['parcel_contacts']:
   slots=[i for i,s in enumerate(c['shapes']) if '/parcel_box/' in s]
   if len(slots)!=1 or not any('right_wrist' in s for s in c['shapes']):continue
   f=R[t].T@(np.array(c['force_world_N'])*(1 if slots[0]==1 else -1));p=R[t].T@(np.array(c['position_world'])-xyz[t])
   forces.append(f);points.append(p);normal_moment+=np.cross(p,[0,0,f[2]]);tangent_moment+=np.cross(p,[f[0],f[1],0])
  if not forces:continue
  f=np.sum(forces,axis=0);load=-f[2]
  if load<.3:continue
  weights=np.maximum(-np.array(forces)[:,2],0);cop=np.average(points,axis=0,weights=weights)
  records.append({'step':t,'hand_normal_load_n':float(load),'hand_force_local_n':f.tolist(),'cop_local_mm':(cop*1000).tolist(),'normal_point_moment_local_nm':normal_moment.tolist(),'tangential_point_moment_local_nm':tangent_moment.tolist(),'object_tilt_rad':float(np.arccos(np.clip(R[t,2,2],-1,1)))})
 assert records
 summary={'loaded_push_samples':len(records),'median_load_n':float(np.median([r['hand_normal_load_n'] for r in records])),'median_cop_local_mm':np.median([r['cop_local_mm'] for r in records],axis=0).tolist(),'median_abs_normal_point_moment_xy_nm':np.median(np.abs([r['normal_point_moment_local_nm'][:2] for r in records]),axis=0).tolist(),'median_abs_tangential_point_moment_xy_nm':np.median(np.abs([r['tangential_point_moment_local_nm'][:2] for r in records]),axis=0).tolist()}
 reports.append({'run':run,'summary':summary,'records':records,'source_sha256':{n:sha(ep/n) for n in ['frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']}});print(run,summary,flush=True)
(w/'RECONTACT_CONTACT_MOMENTS.json').write_text(json.dumps({'scope':__doc__,'episodes':reports,'script_sha256':sha(Path(__file__)),'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'training_ready':False},indent=2))
