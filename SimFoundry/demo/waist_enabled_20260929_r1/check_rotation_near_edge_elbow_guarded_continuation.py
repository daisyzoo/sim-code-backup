"""Counterfactual STICKING material-point continuation; object path prescribed.
Prescribed near_edge; both hand and parcel material points remain fixed.
Redundant fixed XY bounds omitted during solve only, rechecked on every result.
This prevents accepting a rotating object below a stationary slipping hand.
Fixed real material vertex, bounded consecutive joint differences, target center view,
full hand vertices against target top/table/other. NO torque, full arm, initial
zero-to-contact approach, commanded/measured dynamics or pixel occlusion guarantee.
"""
from pathlib import Path
import json,hashlib,sys,xml.etree.ElementTree as ET,time
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,SORTING_D435I_POS,SORTING_D435I_ROT_XYZW,MAILER_SIZE_XYH,TABLE_TOP_Z
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';model=ArticulatedHandGeometry(urdf,repo/'assets/robots/g1_hand_support_vertices.json');points={s:v[ConvexHull(v).vertices] for s,v in model.vertices.items()};report_file=w/'ROTATION_LEVER_CONTACT_SCREEN.json';source=json.loads(report_file.read_text());r=source['episodes'][0];route=r['chosen_route'];assert route['rotation_deg']==80
start=next(s for s in r['rows'][1]['solutions'] if s['static_feasible'] and s['observe_target'] and s['initializer']==1);previous=np.array(start['command']);vertex=np.array(start['material_vertex']);parcel_material_point=np.array(start['contact_local']);parcel_material_point[2]=np.array(r['actual_core']['collision_core_size_xyz'])[2]/2;ep=w/'joint_edge_retry_groups_r1/case_840001/layout_840001_push_box_to_bin'
for n,h in r['source_sha256'].items():assert sha(ep/n)==h
with np.load(ep/'trace.npz') as z:initial=z['box'][0].astype(float);obstacle=z['mailer'][0].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:initial_rotation=Rotation.from_quat(z['box'][0]);Ro=Rotation.from_quat(z['mailer'][0]).as_matrix()
size=np.array(r['actual_core']['collision_core_size_xyz']);other_size=np.array(MAILER_SIZE_XYH);K=np.array(json.loads((ep/'CAMERA_FRUSTUM_DIAGNOSIS.json').read_text())['actual_runtime_intrinsics']);lo=np.array(U1_JOINT_LIMIT_LO)[12:23].astype(float);hi=np.array(U1_JOINT_LIMIT_HI)[12:23].astype(float);lo[0]=-.98;hi[0]=.98
B=np.eye(4);B[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix();B[:3,3]=SORTING_ROBOT_POS;j=next(j for j in ET.parse(urdf).getroot().findall('joint') if j.get('name')=='waist_yaw_joint');o=j.find('origin');O=np.eye(4);O[:3,3]=np.fromstring(o.get('xyz'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix();C=np.eye(4);C[:3,3]=SORTING_D435I_POS;C[:3,:3]=Rotation.from_quat(SORTING_D435I_ROT_XYZW).as_matrix()
Ti,_,_=model.fk('left',previous);inactive_anchor=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);path=[]
for angle in np.linspace(0,80,81):path.append(dict(phase='rotate',angle=float(angle),xyz=initial.copy()))
for k,(a,b) in enumerate(zip(route['waypoints_xy'],route['waypoints_xy'][1:])):
 a=np.array(a);b=np.array(b)
 for f in np.linspace(0,1,int(np.ceil(np.linalg.norm(b-a)/.003))+1)[1:]:
  p=initial.copy();p[:2]=a+(b-a)*f;path.append(dict(phase='front_x' if k==0 else 'lateral_y',angle=80.,xyz=p))
from rotation_elbow_clearance import ElbowTorsoClearance
elbow_clearance=ElbowTorsoClearance(model,w/'rotation_elbow_torso_vertices.json')
rows=[];output=w/'ROTATION_NEAR_EDGE_ELBOW_GUARDED_CONTINUATION.json'
def save():output.write_text(json.dumps(dict(scope=__doc__,source_report_sha256=sha(report_file),checker_sha256=sha(Path(__file__)),planned_stations=len(path),completed_stations=sum(s['accepted'] for s in rows),all_stations_accepted=len(rows)==len(path) and all(s['accepted'] for s in rows),source_episode=r['episode'],fixed_material_vertex=vertex.tolist(),fixed_parcel_material_point=parcel_material_point.tolist(),max_station_joint_change_rad=.055,rows=rows,elbow_guard_m=.010,elbow_model_sha256=sha(w/'rotation_elbow_clearance.py'),elbow_vertices_sha256=sha(w/'rotation_elbow_torso_vertices.json'),training_ready=False,controller_wired=False),indent=2))
def gap(pts,c,R,sz):
 l=(pts-c)@R;return float(np.maximum(l.min(0)-sz/2,-sz/2-l.max(0)).max())
for index,p in enumerate(path):
 target=p['xyz'];Rt=(Rotation.from_rotvec([0,0,np.deg2rad(p['angle'])])*initial_rotation).as_matrix();cache={}
 def geometry(x):
  token=x.tobytes()
  if token in cache:return cache[token]
  T,_,_=model.fk('right',x);Ti,_,_=model.fk('left',x);a=points['right']@T[:3,:3].T+T[:3,3];b=points['left']@Ti[:3,:3].T+Ti[:3,3];local=(a-target)@Rt;contact=(T[:3,:3]@vertex+T[:3,3]-target)@Rt;pi=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);value=(a,b,local,contact,pi);cache.clear();cache[token]=value;return value
 def view(x):
  Y=np.eye(4);Y[:3,:3]=Rotation.from_rotvec([0,0,x[0]]).as_matrix();cam=B@O@Y@C;v=(target-cam[:3,3])@cam[:3,:3];u=K[0]*v[0]+K[2]*v[2];py=K[1]*v[1]+K[3]*v[2];return np.r_[np.array([u-8*v[2],632*v[2]-u,py-8*v[2],472*v[2]-py])/max(K[:2]),v[2]-.1]
 def inequalities(x):
  a,b,l,c,pi=geometry(x);return np.r_[size[:2]/2-.010-c[:2],size[:2]/2-.010+c[:2],l[:,2].min()-size[2]/2+.0002,a[:,2].min()-TABLE_TOP_Z-.001,b[:,2].min()-TABLE_TOP_Z-.001,gap(a,obstacle,Ro,other_size)-.010,gap(b,obstacle,Ro,other_size)-.010,gap(b,target,Rt,size)-.010,view(x),elbow_clearance.gap(x)-.010]
 def equality(x):return geometry(x)[3]-parcel_material_point
 def objective(x):
  pi=geometry(x)[4];return float((x-previous)@(x-previous))+10*float((pi-inactive_anchor)@(pi-inactive_anchor))
 tic=time.monotonic();solution=minimize(objective,previous,bounds=Bounds(np.maximum(lo,previous-.055),np.minimum(hi,previous+.055)),constraints=[dict(type='eq',fun=equality),dict(type='ineq',fun=lambda x:inequalities(x)[4:])],method='SLSQP',options=dict(maxiter=200,ftol=1e-10));x=solution.x;g=inequalities(x);eq=float(np.max(np.abs(equality(x))));delta=float(np.max(abs(x-previous)));accepted=bool(solution.success and g.min()>=-1e-6 and eq<=1e-6 and delta<=.05500001)
 # Recompute all original vertices independently of optimization hull for table and top plane.
 T,_,_=model.fk('right',x);Ti,_,_=model.fk('left',x);a=model.vertices['right']@T[:3,:3].T+T[:3,3];b=model.vertices['left']@Ti[:3,:3].T+Ti[:3,3];alltop=float(((a-target)@Rt)[:,2].min()-size[2]/2);table=float(min(a[:,2].min(),b[:,2].min())-TABLE_TOP_Z)
 if accepted:assert alltop>=-.000201 and table>=.000999
 row=dict(index=index,elbow_torso_gap_m=elbow_clearance.gap(x),phase=p['phase'],rotation_deg=p['angle'],target_xyz=target.tolist(),accepted=accepted,solver_status=int(solution.status),iterations=int(solution.nit),seconds=time.monotonic()-tic,min_inequality=float(g.min()),contact_material_error_m=eq,max_joint_change_rad=delta,all_vertices_top_gap_m=alltop,all_vertices_table_gap_m=table,contact_local=geometry(x)[3].tolist(),view_min_m=float(view(x).min()),inactive_palm_change_mm=float(np.linalg.norm(geometry(x)[4]-inactive_anchor)*1000),command=x.tolist());rows.append(row);save()
 if index%20==0 or not accepted:print(index,len(path),p['phase'],p['angle'],accepted,solution.status,'gap',g.min(),'eq',eq,'dq',delta,flush=True)
 if not accepted:break
 previous=x.copy()
print('complete',sum(s['accepted'] for s in rows),'/',len(path),flush=True)
