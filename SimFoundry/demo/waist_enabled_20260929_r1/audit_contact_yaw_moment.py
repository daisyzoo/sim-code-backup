"""Measured hand yaw moment and hypothetical zero-moment translation, no actuation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(sys.argv[1]).resolve()
key,actor,side=('box','parcel_box','right') if 'push_box' in p.name else ('mailer','mailer','left')
with np.load(p/'trace.npz') as z:positions=z[key].copy()
with np.load(p/'parcel_orientation.npz') as z:yaw=np.unwrap(Rotation.from_quat(z[key]).as_euler('xyz')[:,2])
control={r['step']:r for r in json.loads((p/'expert_control.json').read_text())}
front={r['step']:r for r in json.loads((p/'frontal_bypass.json').read_text())['rows']}
packets=json.loads((p/'solved_contact_forces.json').read_text())['rows'];records=[]
for packet in packets:
 t=packet['after_action_step']
 if t+1>=len(yaw) or control[t]['mode']!='top_push':continue
 center=np.array(packet['post_action_pose'][key]);alignment=float(np.max(abs(center-positions[t+1])))
 assert alignment<1e-6
 force=np.zeros(3);moment=np.zeros(3);contacts=0
 for c in packet['parcel_contacts']:
  slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
  if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
  f=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1)
  force+=f;moment+=np.cross(np.array(c['position_world'])-center,f);contacts+=1
 horizontal=float(np.linalg.norm(force[:2]))
 if not contacts or horizontal<.2 or force[2]>-.1:continue
 # d x F = -tau_z: minimum-norm lateral translation assuming forces fixed.
 # This is not a prediction after moving the hand or a proposed command.
 shift=moment[2]*np.array([-force[1],force[0]])/(horizontal**2)
 assert abs(moment[2]+shift[0]*force[1]-shift[1]*force[0])<1e-9
 records.append(dict(after_action_step=t,route_stage=front[t].get('route_stage') or 'top_y',force_world_n=force.tolist(),hand_moment_about_com_nm=moment.tolist(),hypothetical_zero_yaw_moment_shift_xy_m=shift.tolist(),yaw_step_deg=float(np.degrees(yaw[t+1]-yaw[t])),pose_alignment_error_m=alignment,contacts=contacts))
summary={}
for stage in sorted({r['route_stage'] for r in records}):
 rr=[r for r in records if r['route_stage']==stage];summary[stage]=dict(samples=len(rr))
 for field in ['force_world_n','hand_moment_about_com_nm','hypothetical_zero_yaw_moment_shift_xy_m','yaw_step_deg']:
  values=np.array([r[field] for r in rr]);summary[stage][field]={k:np.quantile(values,q,axis=0).tolist() for k,q in [('p10',.1),('median',.5),('p90',.9)]}
files=['trace.npz','parcel_orientation.npz','expert_control.json','frontal_bypass.json','solved_contact_forces.json','raw.npz']
out=dict(summary=summary,records=records,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in files},scope='Sum actual individual recorded last-tick hand contact moments about next preaction COM. Force packet alignment checked. Hypothetical lateral shift only solves a frozen-force geometric equation; excludes table friction/inertia and does not predict changed contact mechanics, safe reachability or successful control. No object/force modification, no admission.',training_ready=False)
(p/'CONTACT_YAW_MOMENT.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
