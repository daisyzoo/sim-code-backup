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
arm_report_file=w/'ROTATION_ROUTE_ARM_GEOMETRY_CHECK_V2.json';arm_report=json.loads(arm_report_file.read_text());bad=arm_report['unresolved_samples'];queries=[bad[0],next(s for s in bad if s['index']==160 and s['fraction']==1.),min(bad,key=lambda s:s['gap_m'])];answers=[]
for query in queries:
 index=query['index'];f=query['fraction'];old=r['rows'][index-1];current=r['rows'][index];q=(1-f)*np.array(old['command'])+f*np.array(current['command']);elbow=next(s for s in shapes if s['link']=='right_elbow_link');others=[s for s in shapes if s['link']=='torso_link'];aT=fk(elbow['link'],q);a=elbow['vertices']@aT[:3,:3].T+aT[:3,3]
 for other_shape in others:
  T=fk(other_shape['link'],q);b=other_shape['vertices']@T[:3,:3].T+T[:3,3];ha=ConvexHull(a).equations;hb=ConvexHull(b).equations;H=np.r_[ha,hb];result=linprog([0,0,0,-1],A_ub=np.c_[H[:,:3],np.ones(len(H))],b_ub=-H[:,3],bounds=[(None,None)]*4,method='highs');assert result.success,result.message;point=result.x[:3];radius=float(result.x[3]);residual=float(np.max(H[:,:3]@point+H[:,3]+radius));assert residual<1e-7
  answer=dict(index=index,fraction=f,elbow_collider=elbow['path'],torso_collider=other_shape['path'],largest_common_inscribed_radius_m=radius,intersects=radius>1e-7,witness_world=point.tolist(),halfspace_residual=residual,halfspace_count=len(H));answers.append(answer);print(index,f,other_shape['path'].split('/')[-1],'common radius mm',radius*1000,flush=True)
out=dict(scope='Linear-program intersection witness for convex colliders, not dynamics or clearance tolerance relaxation.',source_sha256={source.name:sha(source),arm_report_file.name:sha(arm_report_file)},usd_layers_sha256=arm_report['usd_layers_sha256'],urdf_sha256=sha(urdf),checker_sha256=sha(Path(__file__)),answers=answers,any_certified_overlap=any(a['intersects'] for a in answers),path_accepted=False,training_ready=False)
(w/'ROTATION_ELBOW_TORSO_INTERSECTION.json').write_text(json.dumps(out,indent=2))
