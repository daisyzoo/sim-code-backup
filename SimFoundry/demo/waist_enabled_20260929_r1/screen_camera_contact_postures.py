"""Static pose alternatives at recorded rear contact states; no trajectories/control changes.
Ask whether original joint ranges permit retaining measured active virtual reference,
inactive palm and measured hand-up direction while observing the target center alone versus both object centers, separately.
No per-step slew/path/full-arm/occlusion/contact certificate; not an expert or dataset.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,SORTING_D435I_POS,SORTING_D435I_ROT_XYZW,PARCEL_BOX_SIZE,MAILER_SIZE_XYH
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';model=ArticulatedHandGeometry(urdf,repo/'assets/robots/g1_hand_support_vertices.json');joint=next(j for j in ET.parse(urdf).getroot().findall('joint') if j.get('name')=='waist_yaw_joint');origin=joint.find('origin');B=np.eye(4);B[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix();B[:3,3]=SORTING_ROBOT_POS;O=np.eye(4);O[:3,3]=np.fromstring(origin.get('xyz'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix();C=np.eye(4);C[:3,3]=SORTING_D435I_POS;C[:3,:3]=Rotation.from_quat(SORTING_D435I_ROT_XYZW).as_matrix();lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].astype(float);hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].astype(float);lo[0]=-.98;hi[0]=.98
reports=[]
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';diag=json.loads((ep/'CAMERA_FRUSTUM_DIAGNOSIS.json').read_text());assert diag['runtime_camera_pose_samples_checked']==240
 for n,h in diag['source_sha256'].items():assert sha(ep/n)==h
 prov=json.loads((ep.parent/'provenance.json').read_text())
 for name in ['simfoundry/robots/g1_assets.py','simfoundry/calibration/sorting_station.py','simfoundry/data/hand_obstacle_clearance.py','third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json']:assert sha(repo/name)==prov['source_sha256'][name]
 geom=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));assert sha(w/'staged_joint_edge_command/articulated_hand_geometry.py')==prov['source_sha256'][geom]
 K=np.array(diag['actual_runtime_intrinsics']);key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';inactive='left' if side=='right' else 'right'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].astype(float) for k in z.files}
 fr=json.loads((ep/'frontal_bypass.json').read_text());eligible=[f for f in fr['rows'] if f['mode']=='top_push' and f.get('rear_joint_xy_progress',{}).get('override')];chosen=[eligible[i] for i in np.unique(np.linspace(0,len(eligible)-1,6,dtype=int))];rows=[]
 for f in chosen:
  t=f['step'];measured=q[t];offset=np.array(f['control_offset_local']);T,_,_=model.fk(side,measured);active_position=T[:3,3]+T[:3,:3]@offset;up=T[:3,:3].T@np.array([0,0,1]);Ti,_,_=model.fk(inactive,measured);inactive_position=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);objects=np.array([xyz[key][t],xyz[other][t]])
  def residual(x):
   T,_,_=model.fk(side,x);Ti,_,_=model.fk(inactive,x);return np.r_[T[:3,3]+T[:3,:3]@offset-active_position,Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007])-inactive_position,.15*(T[:3,:3].T@np.array([0,0,1])-up)]
  def view(x):
   Y=np.eye(4);Y[:3,:3]=Rotation.from_rotvec([0,0,x[0]]).as_matrix();cam=B@O@Y@C;observed=objects[:1] if visibility=='target_only' else objects;p=(observed-cam[:3,3])@cam[:3,:3];u=K[0]*p[:,0]+K[2]*p[:,2];v=K[1]*p[:,1]+K[3]*p[:,2];return np.r_[u-8*p[:,2],(640-8)*p[:,2]-u,v-8*p[:,2],(480-8)*p[:,2]-v,p[:,2]-.1]
  def objective(x):r=residual(x);return 1e4*float(r@r)+.01*float((x-measured)@(x-measured))
  visibility='both';measured_view_min_both=float(view(measured).min());visibility='target_only';measured_view_min_target=float(view(measured).min())
  starts=[np.clip(measured,lo,hi)]
  start=starts[0].copy();start[0]=0;starts.append(start);solutions=[]
  for index,initial in enumerate(starts):
   for visibility in ['unconstrained','target_only','both']:
    constrained=visibility!='unconstrained'
    result=minimize(objective,initial,bounds=Bounds(lo,hi),constraints=[dict(type='ineq',fun=view)] if constrained else [],method='SLSQP',options=dict(maxiter=400,ftol=1e-10));x=result.x;rvec=residual(x);T,_,_=model.fk(side,x);newup=T[:3,:3].T@np.array([0,0,1]);geom=model.scene_geometry(side,x,target_xyz=xyz[key][t],target_quat=quat[key][t],other_xyz=xyz[other][t],other_quat=quat[other][t],other_size=MAILER_SIZE_XYH if other=='mailer' else PARCEL_BOX_SIZE)
    solutions.append(dict(visibility=visibility,initializer=index,view_constrained=constrained,solver_success=bool(result.success),status=int(result.status),iterations=int(result.nit),waist_yaw_rad=float(x[0]),active_reference_error_mm=float(np.linalg.norm(rvec[:3])*1000),inactive_reference_error_mm=float(np.linalg.norm(rvec[3:6])*1000),normal_angle_error_rad=float(np.arccos(np.clip(newup@up,-1,1))),view_constraint_min=float(view(x).min()),hand_other_gap_mm=geom['hand_other_gap_m']*1000,max_joint_change_rad=float(np.max(abs(x-measured))),command=x.tolist()))
  rows.append(dict(step=t,measured_yaw_rad=float(measured[0]),measured_view_min_both=measured_view_min_both,measured_view_min_target=measured_view_min_target,solutions=solutions))
  for visibility in ['target_only','both']:
   choices=[s for s in solutions if s['visibility']==visibility];best=min(choices,key=lambda s:s['active_reference_error_mm']+s['inactive_reference_error_mm']);print(ep.name,t,visibility,{k:best[k] for k in ['solver_success','active_reference_error_mm','normal_angle_error_rad','view_constraint_min','hand_other_gap_mm','max_joint_change_rad']},flush=True)
 reports.append(dict(episode=ep.name,rows=rows,camera_diagnostic_sha256=sha(ep/'CAMERA_FRUSTUM_DIAGNOSIS.json'),provenance_sha256=sha(ep.parent/'provenance.json')))
out=dict(scope=__doc__,episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,control_wired=False,physical_started=False)
(w/'CAMERA_CONTACT_POSTURE_SCREEN.json').write_text(json.dumps(out,indent=2))
