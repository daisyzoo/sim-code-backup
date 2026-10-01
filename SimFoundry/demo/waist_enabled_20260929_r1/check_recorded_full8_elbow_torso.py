"""Independent LP overlap witness for actual USD elbow versus torso convex bodies on prescribed contact route and interpolation.
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
 # Positive world-axis separation is already a rigorous separating-axis certificate.
 quick=float(np.maximum(a.min(0)-b.max(0),b.min(0)-a.max(0)).max())
 if quick>0:return quick
 pa=a@axes.T;pb=b@axes.T;return float(np.maximum(pa.min(0)-pb.max(0),pb.min(0)-pa.max(0)).max())

from scipy.optimize import linprog
import collections
body=next(s for s in shapes if s['path'].endswith('/torso_link_23dof_rev_1_0'));torso_h=ConvexHull(body['vertices']).equations
arm_shapes={side:next(s for s in shapes if s['link']==side+'_elbow_link') for side in ['left','right']};arm_h={side:ConvexHull(s['vertices']).equations for side,s in arm_shapes.items()};answers=[]
for cid in [840000,840001,840004,840005]:
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  episode=w/f'joint_edge_retry_groups_r1/case_{cid}/layout_{cid}_{task}'
  with np.load(episode/'raw.npz') as z:recorded=z['q'][:,12:23].astype(float)
  samples=[]
  for step in sorted(set(range(len(recorded)))|{len(recorded)-1}):
   q=recorded[step];Ttorso=fk('torso_link',q)
   for side,shape in arm_shapes.items():
    T=np.linalg.inv(Ttorso)@fk(shape['link'],q);pts=shape['vertices']@T[:3,:3].T+T[:3,3];b=body['vertices'];quick=float(np.maximum(pts.min(0)-b.max(0),b.min(0)-pts.max(0)).max())
    if quick>0:samples.append(dict(step=step,side=side,certified_separated=True,world_axis_gap_in_torso_frame_m=quick));continue
    ah=arm_h[side];normals=ah[:,:3]@T[:3,:3].T;offset=ah[:,3]-normals@T[:3,3];H=np.r_[np.c_[normals,offset],torso_h];result=linprog([0,0,0,-1],A_ub=np.c_[H[:,:3],np.ones(len(H))],b_ub=-H[:,3],bounds=[(None,None)]*4,method='highs');assert result.success;point=result.x[:3];radius=float(result.x[3]);res=float(np.max(H[:,:3]@point+H[:,3]+radius));assert res<1e-7;samples.append(dict(step=step,side=side,certified_separated=radius<0,intersects=radius>1e-7,common_inscribed_radius_m=radius,witness_in_torso=point.tolist(),residual=res))
  overlaps=[s for s in samples if s.get('intersects')];answers.append(dict(episode=episode.name,sample_stride=1,sampled_frames=len(samples)//2,side_samples=len(samples),intersection_samples=len(overlaps),maximum_common_radius_m=max((s['common_inscribed_radius_m'] for s in overlaps),default=0.),samples=samples,raw_sha256=sha(episode/'raw.npz'),provenance_sha256=sha(episode.parent/'provenance.json')));print(episode.name,'intersections',len(overlaps),'/',len(samples),'max radius mm',1000*answers[-1]['maximum_common_radius_m'],flush=True)
out=dict(scope='Recorded measured joints checked every frame, including endpoints, versus current actual USD elbow/torso convex shapes. Current USD root layers not all archived in original run; hash bound here. No claim about unsampled states or contact force dynamics.',rows=answers,checker_sha256=sha(Path(__file__)),usd_layers_sha256={str(Path(l.realPath)):sha(Path(l.realPath)) for l in stage.GetUsedLayers() if l.realPath and Path(l.realPath).is_file()},urdf_sha256=sha(urdf),training_ready=False)
(w/'RECORDED_FULL8_ELBOW_TORSO_CHECK.json').write_text(json.dumps(out,indent=2))
