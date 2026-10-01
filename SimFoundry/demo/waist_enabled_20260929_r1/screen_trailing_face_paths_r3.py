"""Reject unsafe straight joint paths to measured-state side-contact candidates.
Discrete whole-hand convex SAT only; no full-arm, dynamics, or continuous proof.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;repo=w.parents[1]
sys.path[:0]=[str(w/'staged_front_cop_route_axis'),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
def unit_axes(a):
 a=np.asarray(a);length=np.linalg.norm(a,axis=1);a=a[length>1e-8]/length[length>1e-8,None]
 # Either sign denotes the same separating axis.
 sign=np.where(a[np.arange(len(a)),np.argmax(abs(a),axis=1)]<0,-1,1)
 return np.unique(np.round(a*sign[:,None],10),axis=0)
def hull_geometry(points):
 h=ConvexHull(points);f=points[h.simplices]
 return points[h.vertices],unit_axes(h.equations[:,:3]),unit_axes(np.concatenate([f[:,1]-f[:,0],f[:,2]-f[:,1],f[:,0]-f[:,2]]))
geometries={s:hull_geometry(v) for s,v in model.vertices.items()}
def gap(geo,T,center,R,half,threshold=None):
 verts,normals,edges=geo;v=(verts@T[:3,:3].T+T[:3,3]-center)@R
 if threshold is not None:
  box_gap=float(np.maximum(v.min(0)-half,-half-v.max(0)).max())
  if box_gap>=threshold:return box_gap
 n=normals@T[:3,:3].T@R;e=edges@T[:3,:3].T@R
 axes=unit_axes(np.concatenate([n,np.eye(3)]+[np.cross(e,a) for a in np.eye(3)]))
 p=v@axes.T;radius=abs(axes)@half
 return float(np.maximum(p.min(0)-radius,-radius-p.max(0)).max())
# Independent cube geometry sanity: overlap and separated with known face gap.
from itertools import product
cube=hull_geometry(np.array(list(product([-1.,1.],repeat=3))))
assert abs(gap(cube,np.eye(4),np.array([3.,0,0]),np.eye(3),np.ones(3))-1)<1e-8
assert gap(cube,np.eye(4),np.array([.5,0,0]),np.eye(3),np.ones(3))<0
rng=np.random.default_rng(732)
for j in range(20):
 q=np.r_[rng.uniform(-.9,.9),rng.uniform(-.4,.4,10)];T=model.fk('right',q)[0];center=T[:3,3]+rng.uniform(-.3,.3,3);R=Rotation.from_rotvec(rng.uniform(-1,1,3)).as_matrix();half=np.array([.07,.045,.0225]);threshold=[-.001,.005][j%2]
 full=gap(geometries['right'],T,center,R,half);fast=gap(geometries['right'],T,center,R,half,threshold)
 assert (full>=threshold)==(fast>=threshold) and fast<=full+1e-8
out=w/'trailing_face_path_screen_r3';out.mkdir(exist_ok=False);rows=[];sources={} 
for name in ['trailing_face_region_w098_screen_r1','trailing_face_region_w130_screen_r1']:
 p=w/name/'RESULT.json';d=json.loads(p.read_text());assert d['complete'];sources[str(p)]=sha(p)
 for state in d['rows']:
  ep=Path(state['episode']);t=state['actual_frame'];key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';active='right' if key=='box' else 'left';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])};half={key:sizes[key]*state['core_scale']/2,other:sizes[other]/2}
  for f,h in state['source_sha256'].items():assert sha(ep/f)==h
  with np.load(ep/'raw.npz') as z:start=z['q'][t,12:23].astype(float)
  with np.load(ep/'trace.npz') as z:centers={k:z[k][t].astype(float) for k in sizes}
  with np.load(ep/'parcel_orientation.npz') as z:rotations={k:Rotation.from_quat(z[k][t]).as_matrix() for k in sizes}
  attempts=[]
  for candidate in state['attempts']:
   if not candidate['static_candidate']:continue
   end=np.array(candidate['q']);n=int(np.ceil(np.max(abs(end-start))/.01))+1;path=np.linspace(start,end,n);minimum={};first_failure=None;max_inactive_drift=0.
   inactive='left' if active=='right' else 'right';T0=model.fk(inactive,start)[0];anchor=T0[:3,3]+T0[:3,:3]@np.array([.2,0,.007]);endpoint={}
   assert np.all(path>=np.array(U1_JOINT_LIMIT_LO)[12:23]-1e-8) and np.all(path<=np.array(U1_JOINT_LIMIT_HI)[12:23]+1e-8)
   for i,q in enumerate(path):
    metrics={}
    for side in ['left','right']:
     T=model.fk(side,q)[0];v=model.vertices[side]@T[:3,:3].T+T[:3,3];metrics[side+'_min_z_m']=float(v[:,2].min())
     for obj in sizes:metrics[side+'_'+obj+'_gap_m']=gap(geometries[side],T,centers[obj],rotations[obj],half[obj],threshold=-.001 if side==active and obj==key else .005)
     if side==inactive:max_inactive_drift=max(max_inactive_drift,float(np.linalg.norm(T[:3,3]+T[:3,:3]@np.array([.2,0,.007])-anchor)))
    for k,v in metrics.items():minimum[k]=min(minimum.get(k,float('inf')),v)
    reasons=[]
    for side in ['left','right']:
     if metrics[side+'_min_z_m']<.7459:reasons.append(side+'_table_height')
     for obj in sizes:
      threshold=-.001 if side==active and obj==key else .005
      if metrics[side+'_'+obj+'_gap_m']<threshold:reasons.append(side+'_'+obj+'_clearance')
    if reasons and first_failure is None:first_failure=dict(index=i,fraction=i/(n-1),reasons=reasons,metrics=metrics)
    if i==n-1:endpoint=metrics
    if first_failure is not None:break
   attempts.append(dict(face_id=candidate['face_id'],seed=candidate['seed'],solver_success=candidate['solver_success'],samples=n,inspected_samples=i+1,all_samples_inspected=i==n-1,max_joint_step_rad=float(np.max(abs(np.diff(path,axis=0)))),minimum=minimum,endpoint=endpoint,max_inactive_palm_drift_m=max_inactive_drift,first_failure=first_failure,discrete_hand_screen_passed=first_failure is None))
  rows.append(dict(search=name,episode=ep.name,actual_start_frame=t,waist_bound_rad=state['waist_bound_rad'],static_candidates=state['static_candidates'],tested=len(attempts),passed=sum(a['discrete_hand_screen_passed'] for a in attempts),attempts=attempts))
  result=dict(complete=len(rows)==8,rows=rows,source_reports_sha256=sources,script_sha256=sha(__file__),geometry_source_sha256=model.source_sha256,scope='Early-exit version: failing candidates stop at first observed violation and minima cover only the inspected prefix; empty endpoint means it was not reached. All passing candidates inspect all samples. All geometrically eligible static poses, straight interpolation from actual recorded upper11 q, sample steps<=0.01rad. Both hand hulls vs target core/other nominal box and sampled table height. Clearance reports are conservative lower bounds: positive box-face separation exits early only when it proves the exact per-pair threshold; otherwise full convex SAT including face and edge cross axes is used. Both branches have identical threshold decisions, as checked on20 random hand/object poses. Original objects held at recorded pose offline only. Passive palm drift descriptive because dual-arm motion allowed. Does not check arm/self collision, continuous swept collision, servo tracking, force, table footprint, moving objects or success. Hypothetical1.30rad search not approved as working range. No physical state or production source changed.',training_ready=False)
  (out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in rows[-1].items() if k!='attempts'}),flush=True)
