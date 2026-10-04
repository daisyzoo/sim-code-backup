"""Advect each observed contact center with actual/emitted rigidhand poses.
Only scoring uses next observed object pose. This does not construct commands,
assume contact persists at the same point, or identify a causal mechanism.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());model=ArticulatedHandGeometry(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');versions=[];sources={str(Path(__file__)):sha(Path(__file__)),str(S/'articulated_hand_geometry.py'):sha(S/'articulated_hand_geometry.py'),**model.source_sha256}
def stats(records):
 keys=['commanded_material_signed_y_mm','observed_material_signed_y_mm','object_signed_y_mm','material_minus_object_signed_y_mm','commanded_minus_observed_material_signed_y_mm','virtual_contact_distance_mm']
 return dict(frames=len(records),**{k:dict(mean=float(np.mean([x[k] for x in records])),median=float(np.median([x[k] for x in records])),sum=float(sum(x[k] for x in records))) for k in keys}) if records else dict(frames=0)
for run in ['front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 ep=W/run/'case_840023/layout_840023_push_box_to_bin';fr=read(ep/'frontal_bypass.json');packets={p['after_action_step']:p for p in read(ep/'solved_contact_forces.json')['rows']};direction=fr['plan']['direction'];assert direction==-1
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 rows=[]
 for row in fr['rows']:
  t=row['step']
  if row['mode']!='top_push' or t>=len(q)-1:continue
  packet=packets[t-1];assert packet['solver_force_buffer_unchanged'];np.testing.assert_allclose(packet['post_action_pose']['box'],xyz[t],rtol=0,atol=1e-6);points=[];weights=[]
  for c in packet['parcel_contacts']:
   slots=[i for i,name in enumerate(c['shapes']) if '/parcel_box/' in name]
   if len(slots)!=1 or not any('right_wrist' in n for n in c['shapes']):continue
   force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
   if load>.05:points.append(c['position_world']);weights.append(load)
  if sum(weights)<.3:continue
  cop=np.average(points,axis=0,weights=weights);T=model.fk('right',q[t])[0];U=model.fk('right',u[t])[0];N=model.fk('right',q[t+1])[0];local=T[:3,:3].T@(cop-T[:3,3]);virtual=T[:3,3]+T[:3,:3]@np.array(row['control_offset_local']);np.testing.assert_allclose(virtual,row['observed_support_xyz'],rtol=0,atol=1e-6);commanded=U[:3,3]+U[:3,:3]@local;observed=N[:3,3]+N[:3,:3]@local
  dc=direction*(commanded[1]-cop[1])*1000;dm=direction*(observed[1]-cop[1])*1000;do=direction*(xyz[t+1,1]-xyz[t,1])*1000
  rows.append(dict(step=t,load_n=sum(weights),commanded_material_signed_y_mm=float(dc),observed_material_signed_y_mm=float(dm),object_signed_y_mm=float(do),material_minus_object_signed_y_mm=float(dm-do),commanded_minus_observed_material_signed_y_mm=float(dc-dm),virtual_contact_distance_mm=float(np.linalg.norm(cop-virtual)*1000)))
 bounds=read(ep/'OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json')['bouts'];versions.append(dict(run=run,summary=stats(rows),bouts=[dict(start=b['start'],end=b['end'],summary=stats([x for x in rows if b['start']<=x['step']<=b['end']])) for b in bounds],rows=rows))
 for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','OBSERVED24_CONTACT_BOUT_DIAGNOSTIC.json']:sources[str(ep/n)]=sha(ep/n)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,versions=versions,source_sha256=sources,runtime_changed=False,training_ready=False,limitation='Contact-center advection measures material-point kinematics. It is not a future-contact prediction, fulltime impulse or counterfactual causal proof.')
with (W/'front_effective_height_physical_r1/REAR_BOX_MATERIAL_PROGRESS_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([dict(run=v['run'],summary=v['summary']) for v in versions]))
