"""Measured hand yaw motion and parcel yaw during contact bouts; no causal claim."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
source=(w/'screen_lateral_camera_reach.py').read_text();exec(compile(source.split("run=root/'fresh_lateral_00_pilot_r1'")[0],'<validated_fk>','exec'))
run=w/'y_path_nearhalf_groups_r1';ep=run/'case_897003/layout_897003_nudge_mailer_to_bin'
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
with np.load(ep/'trace.npz') as z:palms=z['palm_left'];target=z['mailer']
with np.load(ep/'parcel_orientation.npz') as z:parcel_yaw=np.unwrap(Rotation.from_quat(z['mailer']).as_euler('xyz')[:,2])
mat=np.array([transform('left',x) for x in q]);fkerr=np.max(np.linalg.norm(mat[:,:3,3]+mat[:,:3,:3]@np.array([.20,0,.007])-palms,axis=1));assert fkerr<.0001
hand_rot=Rotation.from_matrix(mat[:,:3,:3]);dz=(hand_rot[1:]*hand_rot[:-1].inv()).as_rotvec()[:,2]
fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];forces=next(r for r in json.loads((run/'INITIAL_TOP_YAW_CONTACTS.json').read_text())['rows'] if r['episode']==ep.name)['records'];byframe={r['frame']:r for r in forces};bouts=[];current=[]
for r in fr:
 if r['mode']=='top_push':current.append(r)
 elif current:bouts.append(current);current=[]
if current:bouts.append(current)
results=[]
for bout in bouts:
 first,last=bout[0]['step'],bout[-1]['step'];last_next=min(last+1,len(q)-1);loaded=[byframe[r['step']] for r in bout if r['step'] in byframe];firstloaded=loaded[:3];lastloaded=loaded[-3:]
 results.append(dict(first_push=first,last_push=last,frames=len(bout),y_progress_m=float(target[last_next,1]-target[first,1]),hand_world_z_rotation_integral_rad=float(dz[first:last_next].sum()),parcel_yaw_delta_rad=float(parcel_yaw[last_next]-parcel_yaw[first]),waist_delta_rad=float(q[last_next,0]-q[first,0]),loaded_samples=len(loaded),first3_cop_xy_m=np.median([r['cop_lever_xy_m'] for r in firstloaded],axis=0).tolist() if loaded else None,last3_cop_xy_m=np.median([r['cop_lever_xy_m'] for r in lastloaded],axis=0).tolist() if loaded else None))
report=dict(episode=ep.name,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(),actual_fk_max_error_m=float(fkerr),bouts=results,scope='Hand orientations from actual23Dq and checked URDF FK. Sum successive world angular-z increments during pre-action top_push bouts; includes no-load frames. Parcel yaw and hand motion association is not causal proof and does not prove full orientation hold reachable/safe. Contact data last-substep only.',training_ready=False)
(run/'LOADED_HAND_TWIST.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
