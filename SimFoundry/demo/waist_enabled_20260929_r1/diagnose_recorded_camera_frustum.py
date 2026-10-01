"""Offline URDF/recorded-state camera-frustum diagnostic, not pixel visibility or a new gate.
Uses unchanged torso-relative calibration and actual runtime camera intrinsics; raw declared intrinsics mismatch is reported explicitly. A bounding-box
frustum exclusion indicates no intersection under this geometric reconstruction;
inside does NOT establish unoccluded visibility. No candidate commands or physics.
Runtime camera world pose and intrinsics are saved every five frames in viewer_observer.json; verify the URDF reconstruction at every logged sample. Unlogged frames remain reconstructed, and occlusion is not measured. This is not a controller/data admission constraint.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET,zipfile,itertools
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,SORTING_D435I_POS,SORTING_D435I_ROT_XYZW,PARCEL_BOX_SIZE,MAILER_SIZE_XYH
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ep=Path(sys.argv[1]).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());snap=ep.parent/'source_snapshot'
for n,h in prov['source_sha256'].items():assert sha(snap/n)==h
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';cal=repo/'simfoundry/calibration/sorting_station.py';vertices=repo/'assets/robots/g1_hand_support_vertices.json'
for p in [urdf,cal,vertices]:assert sha(p)==prov['source_sha256'][str(p.relative_to(repo))]
raw=ep/'raw.npz';quality=json.loads((ep/'quality.json').read_text());assert quality['frames']==1200
with np.load(raw) as z:q=z['q'].copy();K=z['intrinsics'].astype(float)
with zipfile.ZipFile(raw) as z:
 with z.open('rgb.npy') as f:
  version=np.lib.format.read_magic(f);assert version in [(1,0),(2,0)];reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0;shape,order,dtype=reader(f)
assert shape==(1200,3,480,640) and K.shape==(4,) and np.isfinite(K).all();height,width=shape[2:]
with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].astype(float) for k in z.files}
fr=json.loads((ep/'frontal_bypass.json').read_text());modes={0:'initial',**{r['step']:r['mode'] for r in fr['rows']}};key='box' if 'push_box' in ep.name else 'mailer';side='right' if key=='box' else 'left'
root=ET.parse(urdf).getroot();joint=next(j for j in root.findall('joint') if j.get('name')=='waist_yaw_joint');assert joint.find('parent').get('link')=='pelvis' and joint.find('child').get('link')=='torso_link';axis=np.fromstring(joint.find('axis').get('xyz'),sep=' ');assert np.array_equal(axis,[0,0,1]);origin=joint.find('origin')
B=np.eye(4);B[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix();B[:3,3]=SORTING_ROBOT_POS;O=np.eye(4);O[:3,3]=np.fromstring(origin.get('xyz'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix();C=np.eye(4);C[:3,3]=SORTING_D435I_POS;C[:3,:3]=Rotation.from_quat(SORTING_D435I_ROT_XYZW).as_matrix()
geometry=ArticulatedHandGeometry(urdf,vertices);max_palm_error=0.
for t in np.linspace(0,1199,61,dtype=int):
 for hand in ['left','right']:
  T,_,_=geometry.fk(hand,q[t,12:23]);p=T[:3,3]+T[:3,:3]@np.array([.2,0,.007]);max_palm_error=max(max_palm_error,float(np.max(abs(p-xyz['palm_'+hand][t]))))
assert max_palm_error<1e-4,('URDF-world hand reference mismatch',max_palm_error)
signs=np.array(list(itertools.product([-1,1],repeat=3)));sizes={'box':np.array(PARCEL_BOX_SIZE),'mailer':np.array(MAILER_SIZE_XYH)}
assert np.max(abs(sizes[key]-fr['plan']['top_recontact']['contact_size_xyz']))<1e-6
rotations={k:Rotation.from_quat(quat[k]).as_matrix() for k in ['box','mailer']};rows=[]
observer=json.loads((ep/'viewer_observer.json').read_text());camera_samples={int(x['pre_action_step']):x for x in observer['frames']};assert sorted(camera_samples)==list(range(0,1200,5));pose_errors=[]
raw_K=K.copy();runtime_K=np.array(camera_samples[0]['policy_camera_intrinsics']);assert runtime_K.shape==(3,3);K=np.array([runtime_K[0,0],runtime_K[1,1],runtime_K[0,2],runtime_K[1,2]]);raw_K_error=raw_K-K
def project(points,T):
 p=(np.asarray(points)-T[:3,3])@T[:3,:3];uv=p[...,:2]/p[...,2,None]*K[:2]+K[2:];return p,uv
for t in range(1200):
 Y=np.eye(4);Y[:3,:3]=Rotation.from_rotvec(axis*q[t,12]).as_matrix();camera=B@O@Y@C;row=dict(step=t,mode=modes[t],waist_yaw_rad=float(q[t,12]),objects={})
 if t in camera_samples:
  obs=camera_samples[t];actual_R=Rotation.from_quat(obs['policy_camera_quat_ros_xyzw']).as_matrix();actual_p=np.array(obs['policy_camera_position_world']);actual_K=np.array(obs['policy_camera_intrinsics']);poserr=float(np.max(abs(camera[:3,3]-actual_p)));roterr=float(np.max(abs(camera[:3,:3]-actual_R)));kerr=float(np.max(abs(actual_K-np.array([[K[0],0,K[2]],[0,K[1],K[3]],[0,0,1]]))));assert poserr<2e-6 and roterr<2e-6 and kerr<1e-5,(t,poserr,roterr,kerr);pose_errors.append(dict(step=t,max_pos_error_m=poserr,max_rotation_matrix_error=roterr,max_intrinsic_error=kerr))
 for obj in ['box','mailer']:
  corners=xyz[obj][t]+(signs*sizes[obj]/2)@rotations[obj][t].T;p,uv=project(corners,camera);pc,uc=project(xyz[obj][t][None],camera);u,v=uv.T;z=p[:,2]
  excluded=bool(np.all(z<.1) or np.all(z>8.) or np.all(K[0]*p[:,0]+K[2]*z<0) or np.all(K[0]*p[:,0]+(K[2]-width)*z>=0) or np.all(K[1]*p[:,1]+K[3]*z<0) or np.all(K[1]*p[:,1]+(K[3]-height)*z>=0))
  center_inside=bool(.1<=pc[0,2]<=8 and 0<=uc[0,0]<width and 0<=uc[0,1]<height)
  row['objects'][obj]=dict(center_uv=uc[0].tolist(),center_depth_m=float(pc[0,2]),center_in_frustum=center_inside,obb_frustum_excluded=excluded,projected_bounds_uv=[float(u.min()),float(v.min()),float(u.max()),float(v.max())])
 p,uv=project(xyz['palm_'+side][t][None],camera);row['working_palm_reference_in_frustum']=bool(.1<=p[0,2]<=8 and 0<=uv[0,0]<width and 0<=uv[0,1]<height);rows.append(row)
def summary(selected):
 return dict(frames=len(selected),target_obb_excluded=sum(r['objects'][key]['obb_frustum_excluded'] for r in selected),target_center_inside=sum(r['objects'][key]['center_in_frustum'] for r in selected),both_object_centers_inside=sum(all(o['center_in_frustum'] for o in r['objects'].values()) for r in selected),working_palm_reference_inside=sum(r['working_palm_reference_in_frustum'] for r in selected))
out=dict(episode=ep.name,scope=__doc__,all_frames=summary(rows),top_push=summary([r for r in rows if r['mode']=='top_push']),per_mode={mode:summary([r for r in rows if r['mode']==mode]) for mode in sorted(set(modes.values()))},max_hand_fk_reference_error_m=max_palm_error,actual_sample_frames=[r for r in rows if r['step'] in [0,171,342,513,685,856,1027,1199]],rows=rows,raw_declared_intrinsics=raw_K.tolist(),actual_runtime_intrinsics=K.tolist(),raw_minus_runtime_intrinsics=raw_K_error.tolist(),recorded_camera_world_pose_available=True,runtime_camera_pose_samples_checked=len(pose_errors),runtime_pose_errors=pose_errors,max_camera_position_error_m=max(x['max_pos_error_m'] for x in pose_errors),max_camera_rotation_matrix_error=max(x['max_rotation_matrix_error'] for x in pose_errors),current_camera_cfg_sha256=sha(repo/'simfoundry/isaac_envs/sorting_env_cfg.py'),camera_cfg_was_in_source_archive='simfoundry/isaac_envs/sorting_env_cfg.py' in prov['source_sha256'],source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','quality.json','viewer_observer.json']},calibration_sha256=sha(cal),urdf_sha256=sha(urdf),checker_sha256=sha(Path(__file__)),training_ready=False)
(ep/'CAMERA_FRUSTUM_DIAGNOSIS.json').write_text(json.dumps(out,indent=2));print(ep.name,out['all_frames'],out['top_push'],'handFKerror',max_palm_error,flush=True)
