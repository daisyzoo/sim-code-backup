"""Rigid-pose convex collision-envelope diagnostic, not an executable arm path."""
from pathlib import Path
import sys,re,ast,hashlib
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
from scipy.spatial import ConvexHull
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.fingertip_bypass import distal_mesh_vertex,side_surface_point
run=root/'frontal_strict_descent_r1'
asset=root.parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/hand_collision.usda'
arrays=re.findall(r'point3f\[\] points = (\[.*?\])',asset.read_text())
assert len(arrays)==2
meshes={side:np.unique(np.array(ast.literal_eval(a)),axis=0) for side,a in zip(['left','right'],arrays)}
def fk(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);half=size/2
 z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');log=json.loads((ep/'frontal_bypass.json').read_text())['rows'];forces=json.loads((run/'CONTACT_FACE_AUDIT.json').read_text())['rows'];contacts=next(r['contacts'] for r in forces if r['episode']==ep.name)
 firstpress=next(r['step'] for r in log if r['mode']=='tip_press');firstcontact=next(r['step'] for r in contacts if r['phase'] in ['tip_press','tip_sweep'])
 for label,t in [('descent_start',firstpress),('contact_pose',firstcontact)]:
  m=fk(side,dict(zip(names,z['q'][t,12:23])));R=Rotation.from_quat(ori[key][t]).as_matrix();target=tr[key][t];surface=np.array(side_surface_point(target,ori[key][t],size,direction));off=np.array(distal_mesh_vertex(side));v=(meshes[side]-off)@m[:3,:3].T@R;h=ConvexHull(v);v=v[h.vertices]
  hull=ConvexHull(v);edges=set()
  for tri in hull.simplices:
   for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:edges.add(tuple(sorted((a,b))))
  dirs=np.array([v[a]-v[b] for a,b in edges]);axes=np.concatenate([np.eye(3),hull.equations[:,:3],np.cross(dirs[:,None,:],np.eye(3)[None,:,:]).reshape(-1,3)])
  axes=axes[np.linalg.norm(axes,axis=1)>1e-9];axes/=np.linalg.norm(axes,axis=1)[:,None];axes=np.unique(np.round(axes,9),axis=0)
  projections=v@axes.T;mn=projections.min(axis=0);mx=projections.max(axis=0);radius=abs(axes)@half
  def separation(point):
   shift=((point-target)@R)@axes.T
   gaps=np.maximum(mn+shift-radius,-radius-mx-shift);i=np.argmax(gaps)
   return float(gaps[i]),(R@axes[i]).tolist()
  candidates=[]
  for outside in [.012,.025,.04,.06,.08]:
   points=[np.array([surface[0],surface[1]-direction*outside,zv]) for zv in np.linspace(.92,surface[2],100)]
   gaps=[separation(p)[0] for p in points];hit=next((i for i,g in enumerate(gaps) if g<=0),None)
   candidates.append(dict(outside_world_y_m=outside,min_separation_axis_gap_m=min(gaps),first_overlap_control_z=None if hit is None else float(points[hit][2]),overlap_samples=sum(g<=0 for g in gaps),fixed_orientation=True))
  rows.append(dict(episode=ep.name,frame=t,orientation_source=label,mesh_vertices=len(meshes[side]),convex_vertices=len(v),surface_world=surface.tolist(),candidates=candidates));print(ep.name,label,[(c['outside_world_y_m'],round(c['min_separation_axis_gap_m'],5),c['first_overlap_control_z']) for c in candidates],flush=True)
report=dict(rows=rows,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),scope='SAT of convex hull of exact clipped-hand USD points versus recorded oriented parcel cuboid, rigid hand orientation held fixed during hypothetical descent. Positive separating-axis gap certifies these ideal convex bodies disjoint; overlap does not certify engine force or real collision inflation. Omits arm reach/orientation changes/table/other object, is not an executable trajectory or full-arm safety proof.',training_ready=False)
(root/'HAND_DESCENT_GEOMETRY_AUDIT.json').write_text(json.dumps(report,indent=2))
