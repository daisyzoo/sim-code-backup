"""Actual front-box cross-track command and measured response; no physical causal claim."""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());sources={str(Path(__file__)):sha(__file__),str(S/'articulated_hand_geometry.py'):sha(S/'articulated_hand_geometry.py'),**model.source_sha256}
def point(q,normal,center):
 T=model.fk('right',q)[0];n=T[:3,:3].T@normal;offset=center+n*(min(model.vertices['right']@n)-center@n);return T[:3,3]+T[:3,:3]@offset

def stats(xs):
 return dict(n=len(xs),mean=float(np.mean(xs)),median=float(np.median(xs)),min=float(min(xs)),max=float(max(xs))) if xs else None
versions=[]
for run in ['front_loaded_z_quarter_physical_r2','front_effective_height_physical_r1']:
 ep=W/run/'case_840020/layout_840020_push_box_to_bin';fr=read(ep/'frontal_bypass.json');co={c['step']:c for c in read(ep/'coordination.json')}
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 records=[]
 for r in fr['rows']:
  if r['mode']!='top_push':continue
  t=r['step'];c=co[t];task=c['task_inputs'];z=c['front_loaded_z_priority'];tp=c['joint_transport_clearance'];normal=rot[t,:,2];center=np.array(c['active_support_reference']['center_local']);current=point(q[t],normal,center)
  np.testing.assert_allclose(current,r['observed_support_xyz'],rtol=0,atol=2e-6)
  np.testing.assert_array_equal(tp['parent_command'],z['output_command']);np.testing.assert_array_equal(tp['output_command'],u[t])
  np.testing.assert_allclose(task['error'][3:6],np.clip(.72*(np.array(r['target_xyz'])-current),-.035,.035),rtol=0,atol=2e-6)
  commands={'before_z':np.array(z['context']['parent_command']),'after_z':np.array(z['output_command']),'after_transport':u[t]}
  nominal={k:((point(v,normal,center)-current)*1000).tolist() for k,v in commands.items()}
  records.append(dict(step=t,route_stage=r['route_stage'],transport_applied=tp['applied'],route_x_error_mm=(r['route_goal_x']-xyz[t,0])*1000,desired_support_dx_mm=(r['target_xyz'][0]-current[0])*1000,original_task_dx_mm=task['error'][3]*1000,nominal_delta_xyz_mm=nominal,next_measured_frozen_support_delta_xyz_mm=None if t==1199 else ((point(q[t+1],normal,center)-current)*1000).tolist(),next_target_delta_xyz_mm=None if t==1199 else ((xyz[t+1]-xyz[t])*1000).tolist()))
 lateral=[r for r in records if r['route_stage']=='lateral_y' and r['next_target_delta_xyz_mm'] is not None]
 summary=dict(push_frames=len(records),lateral_frames=len(lateral),transport_applied=sum(r['transport_applied'] for r in records),lateral_next_target_positive_x=sum(bool(r['next_target_delta_xyz_mm'][0]>0) for r in lateral),lateral_negative_x_goal_but_positive_target_response=sum(bool(r['route_x_error_mm']<0 and r['next_target_delta_xyz_mm'][0]>0) for r in lateral),lateral_negative_nominal_dx_but_positive_actual_hand_response=sum(bool(r['nominal_delta_xyz_mm']['after_transport'][0]<0 and r['next_measured_frozen_support_delta_xyz_mm'][0]>0) for r in lateral),lateral_transport_changed_nominal_x_by_mm=stats([r['nominal_delta_xyz_mm']['after_transport'][0]-r['nominal_delta_xyz_mm']['after_z'][0] for r in lateral if r['transport_applied']]),lateral_next_target_dx_mm=stats([r['next_target_delta_xyz_mm'][0] for r in lateral]))
 versions.append(dict(run=run,summary=summary,rows=records))
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json']:sources[str(ep/name)]=sha(ep/name)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,versions=versions,source_sha256=sources,training_ready=False,limitations=['Same captured support center and current normal used at all nominal and next measured joint states; physical COP may move.','Servo target is not expected one-frame displacement. Forces, velocity and material slip need separate analysis.','Recorded solver/context comparison alone does not prove causal response under changed commands.'])
encoded=json.dumps(report,indent=2)
with (W/'front_effective_height_physical_r1/FRONT_BOX_CROSS_TRACK_CHAIN_V2.json').open('x') as f:f.write(encoded)
for v in versions:
 print(json.dumps(dict(run=v['run'],summary=v['summary'])))
 if 'effective' in v['run']:
  for r in v['rows']:
   if r['step'] in [1004,1008,1009,1131,1146,1147]:print(json.dumps(r))
