"""Shadow measurement from completed raw; no relocated trajectory or admission."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from contact_center_calibration_candidate import ContactCenterCalibration
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
p=Path(sys.argv[1]).resolve();side='right' if 'push_box' in p.name else 'left';key='box' if side=='right' else 'mailer';actor='parcel_box' if key=='box' else 'mailer'
with np.load(p/'raw.npz') as z:qs=z['q'].copy()
with np.load(p/'trace.npz') as z:positions=z[key].copy()
with np.load(p/'parcel_orientation.npz') as z:rotations=Rotation.from_quat(z[key]).as_matrix()
control={r['step']:r for r in json.loads((p/'expert_control.json').read_text())};packets={r['after_action_step']:r for r in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
vertices=json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side];cal=ContactCenterCalibration(vertices);records=[];first=None
for t in range(1,len(qs)):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*qs[t,12+names.index(name)]).as_matrix();m=m@a
 result=cal.observe(packets.get(t-1),step=t,mode=control[t-1]['mode'],side=side,actor=actor,hand_xyz=m[:3,3],hand_rotation=m[:3,:3],object_xyz=positions[t],object_normal=rotations[t,:,2]);records.append(dict(step=t,**result))
 if result['ready'] and control[t]['mode'] in ('top_press','top_push'):
  first=t;cal.commit();break
out=dict(first_ready_step=first,proposed_local_center=cal.center_local.tolist() if first is not None else None,records=records,helper_sha256=hashlib.sha256((root/'contact_center_calibration_candidate.py').read_bytes()).hexdigest(),raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Unexecuted helper replay using prior control mode and exact previous solved-force packet, current independent URDF hand pose and parcel pose/normal. Only tests initial measurement feasibility. No collector wiring, actual lift/recenter, changed forces, future contact accuracy or physical success.',training_ready=False)
(p/'CONTACT_CENTER_CALIBRATION_SHADOW.json').write_text(json.dumps(out,indent=2));print(p.name,first,out['proposed_local_center'])
