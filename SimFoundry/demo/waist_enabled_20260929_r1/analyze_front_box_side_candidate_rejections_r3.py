"""Evaluate omitted SAT geometry on ALL saved side-search endpoints; no new search.
Original 20deg orientation eligibility remains required. Diagnostic breakdown
only: never promote a point that fails orientation or original quality guards.
"""
from pathlib import Path
import ast,hashlib,json,datetime,sys,collections
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_midpoint_integrated';sys.path[:0]=[str(S),str(ROOT)]
from articulated_hand_geometry import ArticulatedHandGeometry
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=W/'screen_front_z_box_trailing_face_palm.py';node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='sat');ns={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns);sat=ns['sat']
model=ArticulatedHandGeometry(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');points=model.vertices['right'];hull=ConvexHull(points);verts=points[hull.vertices];faces=points[hull.simplices];normals=hull.equations[:,:3];edges=np.concatenate([faces[:,1]-faces[:,0],faces[:,2]-faces[:,1],faces[:,0]-faces[:,2]])
sources={str(source):sha(source)};runs=[]
for name in ['front_z_box_trailing_face_static_r1','front_z_box_trailing_face_static_r2','front_z_box_trailing_face_static_r3']:
 p=W/name/'RESULT.json';data=json.loads(p.read_text());record=data['rows'][0];ep=Path(record['episode']);t=record['actual_frame'];sources[str(p)]=sha(p)
 for key,h in data['source_sha256'].items():assert sha(key)==h,key
 for key,h in record['source_sha256'].items():assert sha(ep/key)==h,key;sources[str(ep/key)]=h
 with np.load(ep/'trace.npz') as z:center=z['box'][t];other=z['mailer'][t]
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box'][t]).as_matrix();orot=Rotation.from_quat(z['mailer'][t]).as_matrix()
 half=np.array([.14,.09,.045])*record['core_scale']/2;rows=[];counts=collections.Counter()
 for r in record['attempts']:
  T,_,_=model.fk('right',np.asarray(r['q']));R=T[:3,:3];v=verts@R.T+T[:3,3];target_gap=sat(v,normals@R.T,edges@R.T,center,rot,half);other_gap=sat(v,normals@R.T,edges@R.T,other,orot,np.array([.15,.145,.04])/2)
  gates=dict(point_3mm=r['position_error_m']<=.003,normal_20deg=r['normal_error_rad']<=np.deg2rad(20),active_mesh_table=r['hand_min_z_m']>=.7459,inactive_anchor_2mm=r['inactive_palm_error_m']<=.002,target_precontact_1mm=target_gap>=.001,other_5mm=other_gap>=.005,elbows_5mm=min(r['elbow_gaps_m'])>=.005-2e-7,inactive_mesh_table=r['inactive_hand_min_z_m']>=.746,palm_table=r['original_palm_table_margin_m']>=0)
  if r['sat_gaps_m'] is not None:np.testing.assert_allclose([target_gap,other_gap],[r['sat_gaps_m']['box'],r['sat_gaps_m']['mailer']],atol=1e-12,rtol=0)
  assert all(gates.values())==r['static_candidate']
  counts.update(k for k,vv in gates.items() if not vv);rows.append(dict(face=r['face_id'],seed=r['seed'],target_gap_m=target_gap,other_gap_m=other_gap,gates=gates,only_orientation_failed=not gates['normal_20deg'] and all(vv for k,vv in gates.items() if k!='normal_20deg')))
 runs.append(dict(run=name,attempts=len(rows),original_eligible=sum(all(r['gates'].values()) for r in rows),rejection_counts=dict(counts),only_orientation_failed=sum(r['only_orientation_failed'] for r in rows),rows=rows))
for p in [Path(__file__),S/'articulated_hand_geometry.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=runs,source_sha256=sources,eligibility_changed=False,new_candidate_selected=False,physics_started=False,training_ready=False)
with (W/'front_z_priority_physical_r1/BOX_SIDE_ENDPOINT_REJECTION_BREAKDOWN_R3.json').open('x') as f:json.dump(out,f,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))
print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in runs],indent=2))
