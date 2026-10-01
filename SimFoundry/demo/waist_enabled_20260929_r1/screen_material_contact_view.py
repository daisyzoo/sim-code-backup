"""Diagnostic static material-vertex contact with free hand orientation.
No controller/path/dynamics/full-arm/occlusion certification or training admission.
Actual target core and hand convex hull; other object visual OBB conservative.
"""
from pathlib import Path
import json,hashlib,sys,xml.etree.ElementTree as ET,time
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize,Bounds
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,SORTING_D435I_POS,SORTING_D435I_ROT_XYZW,PARCEL_BOX_SIZE,MAILER_SIZE_XYH,TABLE_TOP_Z
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';model=ArticulatedHandGeometry(urdf,vertices)
hull={s:ConvexHull(v).vertices for s,v in model.vertices.items()};points={s:model.vertices[s][hull[s]] for s in hull}
B=np.eye(4);B[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix();B[:3,3]=SORTING_ROBOT_POS
joint=next(j for j in ET.parse(urdf).getroot().findall('joint') if j.get('name')=='waist_yaw_joint');origin=joint.find('origin');O=np.eye(4);O[:3,3]=np.fromstring(origin.get('xyz'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(origin.get('rpy','0 0 0'),sep=' ')).as_matrix();C=np.eye(4);C[:3,3]=SORTING_D435I_POS;C[:3,:3]=Rotation.from_quat(SORTING_D435I_ROT_XYZW).as_matrix()
lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].astype(float);hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].astype(float);lo[0]=-.98;hi[0]=.98
output=w/'MATERIAL_CONTACT_VIEW_SCREEN.json';reports=[]
def save():output.write_text(json.dumps(dict(scope=__doc__,episodes=reports,checker_sha256=sha(Path(__file__)),training_ready=False,control_wired=False,full_arm_checked=False,source_sha256={str(p.relative_to(repo)):sha(p) for p in [urdf,vertices,repo/'simfoundry/calibration/sorting_station.py',repo/'simfoundry/robots/g1_assets.py',w/'staged_joint_edge_command/articulated_hand_geometry.py']}),indent=2))
for cid,task,steps in [(840001,'push_box_to_bin',[495,1160]),(840004,'nudge_mailer_to_bin',[257,1087])]:
 ep=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}';diag=json.loads((ep/'CAMERA_FRUSTUM_DIAGNOSIS.json').read_text());assert diag['runtime_camera_pose_samples_checked']==240
 for n,h in diag['source_sha256'].items():assert sha(ep/n)==h
 prov=json.loads((ep.parent/'provenance.json').read_text())
 for p in [urdf,vertices,repo/'simfoundry/calibration/sorting_station.py',repo/'simfoundry/robots/g1_assets.py']:assert sha(p)==prov['source_sha256'][str(p.relative_to(repo))]
 K=np.array(diag['actual_runtime_intrinsics']);key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';inactive='left' if side=='right' else 'right'
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz={k:z[k].astype(float) for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:quat={k:z[k].astype(float) for k in z.files}
 fr=json.loads((ep/'frontal_bypass.json').read_text());core=fr['plan']['region_causal_response']['actual_core'];assert np.max(np.abs(core['core_center_local']))<1e-9;size=np.array(core['collision_core_size_xyz']);other_size=np.array(MAILER_SIZE_XYH if other=='mailer' else PARCEL_BOX_SIZE)
 record=dict(episode=ep.name,actual_core=core,rows=[],source_sha256={n:sha(ep/n) for n in ['CAMERA_FRUSTUM_DIAGNOSIS.json','raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']});reports.append(record)
 for t in steps:
  measured=q[t];target=xyz[key][t];obstacle=xyz[other][t];Rt=Rotation.from_quat(quat[key][t]).as_matrix();Ro=Rotation.from_quat(quat[other][t]).as_matrix();Ti,_,_=model.fk(inactive,measured);inactive_anchor=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);starts=[np.clip(measured,lo,hi)]
  for yaw in [0.,-.45 if side=='right' else .45]:
   start=starts[0].copy();start[0]=yaw;starts.append(start)
  row=dict(step=t,measured_yaw_rad=float(measured[0]),solutions=[]);record['rows'].append(row)
  for index,initial in enumerate(starts):
   T,_,_=model.fk(side,initial);local=(points[side]@T[:3,:3].T+T[:3,3]-target)@Rt;vindex=int(np.argmin(local[:,2]));vertex=points[side][vindex]
   for observe in [False,True]:
    cache={}
    def geometry(x):
     token=x.tobytes()
     if token in cache:return cache[token]
     T,_,_=model.fk(side,x);Ti,_,_=model.fk(inactive,x);a=points[side]@T[:3,:3].T+T[:3,3];b=points[inactive]@Ti[:3,:3].T+Ti[:3,3];local=(a-target)@Rt;pi=Ti[:3,3]+Ti[:3,:3]@np.array([.2,0,.007]);value=(a,b,local,pi)
     cache.clear();cache[token]=value;return value
    def gap(pts,c,R,sz):
     l=(pts-c)@R;return float(np.maximum(l.min(0)-sz/2,-sz/2-l.max(0)).max())
    def view(x):
     Y=np.eye(4);Y[:3,:3]=Rotation.from_rotvec([0,0,x[0]]).as_matrix();cam=B@O@Y@C;p=(target-cam[:3,3])@cam[:3,:3];u=K[0]*p[0]+K[2]*p[2];v=K[1]*p[1]+K[3]*p[2];return np.array([u-8*p[2],632*p[2]-u,v-8*p[2],472*p[2]-v,p[2]-.1])
    def inequalities(x):
     a,b,l,pi=geometry(x);contact=l[vindex];values=np.r_[size[:2]/2-.010-contact[:2],size[:2]/2-.010+contact[:2],l[:,2].min()-size[2]/2+.0002,a[:,2].min()-TABLE_TOP_Z-.001,b[:,2].min()-TABLE_TOP_Z-.001,gap(a,obstacle,Ro,other_size)-.010,gap(b,obstacle,Ro,other_size)-.010,gap(b,target,Rt,size)-.010]
     return np.r_[values,view(x)] if observe else values
    def equality(x):return (geometry(x)[2][vindex,2]-size[2]/2)*100
    def objective(x):
     a,b,l,pi=geometry(x);return .001*float((x-measured)@(x-measured))+10*float((pi-inactive_anchor)@(pi-inactive_anchor))+float(l[vindex,:2]@l[vindex,:2])
    tic=time.monotonic();result=minimize(objective,initial,bounds=Bounds(lo,hi),constraints=[dict(type='eq',fun=equality),dict(type='ineq',fun=inequalities)],method='SLSQP',options=dict(maxiter=250,ftol=1e-10));x=result.x;a,b,l,pi=geometry(x);c=l[vindex];g=inequalities(x);eq=abs(float(equality(x)))/100
    # Recheck every original mesh vertex, not merely the optimization hull.
    Ta,_,_=model.fk(side,x);Tb,_,_=model.fk(inactive,x);all_a=model.vertices[side]@Ta[:3,:3].T+Ta[:3,3];all_b=model.vertices[inactive]@Tb[:3,:3].T+Tb[:3,3];all_local=(all_a-target)@Rt
    assert abs(all_local[:,2].min()-l[:,2].min())<1e-10
    feasible=bool(result.success and eq<=1e-6 and g.min()>=-1e-6 and np.all(x>=lo-1e-8) and np.all(x<=hi+1e-8))
    sol=dict(observe_target=observe,initializer=index,vertex_original_index=int(hull[side][vindex]),material_vertex=vertex.tolist(),solver_success=bool(result.success),solver_status=int(result.status),iterations=int(result.nit),seconds=time.monotonic()-tic,static_feasible=feasible,contact_local=c.tolist(),contact_height_error_mm=eq*1000,min_inequality=float(g.min()),view_min=float(view(x).min()),active_min_target_plane_mm=float((all_local[:,2].min()-size[2]/2)*1000),active_other_gap_mm=gap(all_a,obstacle,Ro,other_size)*1000,inactive_other_gap_mm=gap(all_b,obstacle,Ro,other_size)*1000,inactive_target_gap_mm=gap(all_b,target,Rt,size)*1000,hand_table_min_mm=float(min(all_a[:,2].min(),all_b[:,2].min())-TABLE_TOP_Z)*1000,inactive_palm_change_mm=float(np.linalg.norm(pi-inactive_anchor)*1000),max_joint_change_rad=float(np.max(abs(x-measured))),command=x.tolist())
    row['solutions'].append(sol);save();print(ep.name,t,index,observe,feasible,'status',result.status,'heightmm',round(eq*1000,4),'min',round(float(g.min()),6),'yaw',round(float(x[0]),3),flush=True)
print('complete',output,flush=True)
