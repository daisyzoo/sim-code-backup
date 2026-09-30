"""Relate measured contact reacquisitions to hand posture; no causal inference."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]);side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer'
with np.load(p/'raw.npz') as z:qs=z['q']
with np.load(p/'parcel_orientation.npz') as z:angles=Rotation.from_quat(z[key]).as_euler('xyz')[:,2]
log=json.loads((p/'frontal_bypass.json').read_text())['rows'];cop=json.loads((p/'LOADED_CONTACT_OFFSETS.json').read_text())['records'];starts=[r['step'] for i,r in enumerate(log) if r['mode']=='top_push' and (i==0 or log[i-1]['mode']!='top_push')]
def hand_rotation(t):
 q=dict(zip(names,qs[t,12:23]));m=np.eye(4)
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@a
 return m[:3,:3]
rows=[];r0=None
for t in starts:
 selected=[x for x in cop if t<=x['controller_step']<t+20];end=next((r['step']-1 for r in log if r['step']>t and r['mode']!='top_push'),len(qs)-1);rr=hand_rotation(t)
 if r0 is None:r0=rr
 rows.append(dict(push_start=t,push_end=end,parcel_yaw_start_deg=float(np.degrees(angles[t])),parcel_yaw_end_deg=float(np.degrees(angles[end])),hand_world_euler_xyz_deg=Rotation.from_matrix(rr).as_euler('xyz',degrees=True).tolist(),hand_rotation_since_first_contact_deg=float(np.degrees(Rotation.from_matrix(rr@r0.T).magnitude())),first20_loaded_samples=len(selected),first20_median_cop_lever_xy_m=np.median([x['contact_minus_target_xy_m'] for x in selected],axis=0).tolist() if selected else None,first20_median_force_on_target_n=np.median([x['force_on_target_world_n'] for x in selected],axis=0).tolist() if selected else None))
out=dict(rows=rows,source_sha256={f:hashlib.sha256((p/f).read_bytes()).hexdigest() for f in ('raw.npz','parcel_orientation.npz','frontal_bypass.json','LOADED_CONTACT_OFFSETS.json')},scope='Independent URDF hand rotation at each measured top-push acquisition, parcel yaw and existing force-weighted real contact centroids. Correlation only; not full contact mechanics, controlled ablation or physics execution.',training_ready=False)
(p/'CONTACT_PATCH_REACQUISITION.json').write_text(json.dumps(out,indent=2));print(json.dumps(rows,indent=2))
