"""Read-only USD upper-arm collider check on prescribed contact route and interpolation.
Uses actual USD enabled meshes/outer cylinder polygons and URDF transforms, validated
at zero pose against USD. All10 upper limb shapes vs target/other/table; active hand
vs target intentionally excluded. Cross-arm and distal-arm/torso checked conservatively.
No initial approach, dynamic tracking, contact-force feasibility or adjacent-link
self-collision certification. Nonpositive separating-axis result is unresolved overlap.
"""
from pathlib import Path
import json,hashlib,sys,xml.etree.ElementTree as ET,itertools
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation,Slerp
from pxr import Usd,UsdGeom,UsdPhysics
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(repo),str(w/'staged_joint_edge_command')]
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW,MAILER_SIZE_XYH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source=w/'ROTATION_NEAR_EDGE_STICKING_CONTINUATION.json';r=json.loads(source.read_text());assert r['all_stations_accepted'] and len(r['rows'])==263
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';xml=ET.parse(urdf).getroot();children={j.find('child').get('link'):j for j in xml.findall('joint')};model=ArticulatedHandGeometry(urdf,repo/'assets/robots/g1_hand_support_vertices.json');names=model.names
chains={}
def fk(link,q):
 if link not in chains:
  chain=[];l=link
  while l in children:
   j=children[l];o=j.find('origin');M=np.eye(4)
   if o is not None:M[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');M[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
   chain.append((j.get('name'),M,None if j.find('axis') is None else np.fromstring(j.find('axis').get('xyz'),sep=' ')));l=j.find('parent').get('link')
  chains[link]=list(reversed(chain))
 M=model.base.copy()
 for name,O,axis in chains[link]:
  M=M@O
  if axis is not None:
   R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[names.index(name)] if name in names else 0.)).as_matrix();M=M@R
 return M
usd=repo/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/g1_23dof_rev_1_0_u1_black.usda';stage=Usd.Stage.Open(str(usd));cache=UsdGeom.XformCache();pelvis=stage.GetPrimAtPath(str(stage.GetDefaultPrim().GetPath())+'/Geometry/pelvis');shapes=[];links={};validation=[]
for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
 if not prim.HasAPI(UsdPhysics.CollisionAPI) or not UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get():continue
 path=str(prim.GetPath());isarm=any(v in path for v in ['shoulder','elbow','wrist']);istorso='torso_link' in path and not isarm
 if not (isarm or istorso):continue
 body=prim
 while body and not body.HasAPI(UsdPhysics.RigidBodyAPI):body=body.GetParent()
 if not body:raise ValueError('No rigid body')
 link=body.GetName();links[link]=body;relative=np.array(cache.ComputeRelativeTransform(prim,body)[0]).T
 if prim.IsA(UsdGeom.Mesh):
  local=np.array(UsdGeom.Mesh(prim).GetPointsAttr().Get(),dtype=float);shape_kind='mesh_convex_hull'
  assert prim.GetAttribute('physics:approximation').Get()=='convexHull'
 elif prim.IsA(UsdGeom.Cylinder):
  c=UsdGeom.Cylinder(prim);radius=float(c.GetRadiusAttr().Get());height=float(c.GetHeightAttr().Get());axis=str(c.GetAxisAttr().Get());i={'X':0,'Y':1,'Z':2}[axis];xy=[j for j in range(3) if j!=i];a=np.arange(32)*2*np.pi/32;local=np.zeros((64,3));local[:,i]=np.repeat([-height/2,height/2],32);local[:,xy[0]]=np.tile(np.cos(a)*radius/np.cos(np.pi/32),2);local[:,xy[1]]=np.tile(np.sin(a)*radius/np.cos(np.pi/32),2);shape_kind='circumscribed32gon_cylinder'
 else:raise ValueError(prim.GetTypeName())
 local=local@relative[:3,:3].T+relative[:3,3];hull=ConvexHull(local);v=local[hull.vertices];axes=np.unique(np.round(hull.equations[:,:3],10),axis=0);shapes.append(dict(path=path,link=link,kind=shape_kind,vertices=v,axes=axes,isarm=isarm))
for link,body in links.items():
 expected=model.base@np.array(cache.ComputeRelativeTransform(body,pelvis)[0]).T;error=float(np.abs(fk(link,np.zeros(11))-expected).max());assert error<2e-6,(link,error);validation.append(dict(link=link,zero_transform_max_error=error))
for side in ['left','right']:
 shape=next(s for s in shapes if s['link']==side+'_wrist_roll_rubber_hand');assert np.allclose(shape['vertices'].min(0),model.vertices[side].min(0),atol=1e-7);assert np.allclose(shape['vertices'].max(0),model.vertices[side].max(0),atol=1e-7)
assert sum(s['isarm'] for s in shapes)==10
source_geom=json.loads((w/'ROTATION_LEVER_CONTACT_SCREEN.json').read_text())['episodes'][0];size=np.array(source_geom['actual_core']['collision_core_size_xyz']);ep=w/'joint_edge_retry_groups_r1/case_840001/layout_840001_push_box_to_bin'
with np.load(ep/'trace.npz') as z:other=z['mailer'][0].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:base_rotation=Rotation.from_quat(z['box'][0]);other_rotation=Rotation.from_quat(z['mailer'][0]).as_matrix()
signs=np.array(list(itertools.product([-1,1],repeat=3)));fixed=[('other',signs*np.array(MAILER_SIZE_XYH)/2@other_rotation.T+other,other_rotation.T),('table',signs*np.array([.6,1.5,.025])/2+np.array([.58,0,.7375]),np.eye(3))]
def gap(a,b,axes):
 pa=a@axes.T;pb=b@axes.T;return float(np.maximum(pa.min(0)-pb.max(0),pb.min(0)-pa.max(0)).max())
minimum={};unresolved=[];samples=[];interp_material=[]
for index,row in enumerate(r['rows']):
 if index==0:samples.append((0,0.,np.array(row['command']),np.array(row['target_xyz']),row['rotation_deg']))
 else:
  old=r['rows'][index-1]
  for t in [.25,.5,.75,1.]:samples.append((index,t,(1-t)*np.array(old['command'])+t*np.array(row['command']),(1-t)*np.array(old['target_xyz'])+t*np.array(row['target_xyz']),(1-t)*old['rotation_deg']+t*row['rotation_deg']))
vertex=np.array(r['fixed_material_vertex']);parcel_point=np.array(r['fixed_parcel_material_point'])
for index,t,q,position,angle in samples:
 frames={link:fk(link,q) for link in links};world=[]
 for s in shapes:
  T=frames[s['link']];world.append((s,s['vertices']@T[:3,:3].T+T[:3,3],s['axes']@T[:3,:3].T))
 Rt=(Rotation.from_rotvec([0,0,np.deg2rad(angle)])*base_rotation).as_matrix();target=('target',signs*size/2@Rt.T+position,Rt.T)
 for s,a,axes in world:
  if not s['isarm']:continue
  for label,b,baxes in [*fixed,target]:
   if label=='target' and s['link']=='right_wrist_roll_rubber_hand':continue
   g=gap(a,b,np.r_[axes,baxes]);pair=s['link']+'::'+label;minimum[pair]=min(minimum.get(pair,float('inf')),g)
   if g<=0:unresolved.append(dict(index=index,fraction=t,pair=pair,gap_m=g))
 for i,(s,a,axes) in enumerate(world):
  for ss,b,baxes in world[i+1:]:
   cross=s['isarm'] and ss['isarm'] and s['link'].startswith('left')!=ss['link'].startswith('left')
   distal=(s['isarm']!=ss['isarm']) and any(k in (s['link'] if s['isarm'] else ss['link']) for k in ['elbow','wrist'])
   if not (cross or distal):continue
   g=gap(a,b,np.r_[axes,baxes]);pair=s['link']+'::'+ss['link'];minimum[pair]=min(minimum.get(pair,float('inf')),g)
   if g<=0:unresolved.append(dict(index=index,fraction=t,pair=pair,gap_m=g))
 T=frames['right_wrist_roll_rubber_hand'];local=(T[:3,:3]@vertex+T[:3,3]-position)@Rt;interp_material.append(dict(index=index,fraction=t,material_error_m=float(np.linalg.norm(local-parcel_point))))
 if index%50==0 and t==1.:print('station',index,'unresolved',len(unresolved),flush=True)
layers={str(Path(l.realPath)):sha(Path(l.realPath)) for l in stage.GetUsedLayers() if l.realPath and Path(l.realPath).is_file()}
out=dict(scope=__doc__,source_report_sha256=sha(source),checker_sha256=sha(Path(__file__)),usd_layers_sha256=layers,urdf_sha256=sha(urdf),zero_pose_validation=validation,colliders=[{k:v for k,v in s.items() if k not in ['vertices','axes']} for s in shapes],sample_count=len(samples),pair_minimum_axis_gap_m=minimum,unresolved_samples=unresolved,all_sampled_pairs_separated=not unresolved,maximum_interpolation_material_error_m=max(v['material_error_m'] for v in interp_material),interpolation_material_rows=interp_material,training_ready=False)
(w/'ROTATION_ROUTE_ARM_GEOMETRY_CHECK.json').write_text(json.dumps(out,indent=2));print('done samples',len(samples),'unresolved',len(unresolved),'min gap',min(minimum.values()),'max material error',out['maximum_interpolation_material_error_m'],flush=True)
