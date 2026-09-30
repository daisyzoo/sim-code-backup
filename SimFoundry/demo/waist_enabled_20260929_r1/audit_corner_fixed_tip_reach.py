"""Whole convex-hand supporting point IK candidates; never directly execute."""
from pathlib import Path
import sys,re,ast
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
from scipy.spatial import ConvexHull
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.fingertip_bypass import side_surface_point,distal_mesh_vertex
asset=root.parents[1]/'assets/robots/g1_23dof_u1_rubber/g1_23dof_rev_1_0_u1_black/payloads/hand_collision.usda'
arrays=re.findall(r'point3f\[\] points = (\[.*?\])',asset.read_text());meshes={}
for side,a in zip(['left','right'],arrays):
 v=np.unique(np.array(ast.literal_eval(a)),axis=0);meshes[side]=v[ConvexHull(v).vertices]
def fk(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m
rng=np.random.default_rng(937);rows=[];lo[0]=-.98;hi[0]=.98
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 ep=root/'frontal_strict_descent_r1/case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());other='right' if side=='left' else 'left';anchor=np.array(j['plan']['inactive_anchor_override']['xyz']);key='mailer' if side=='left' else 'box';direction=1 if side=='left' else -1;size=np.array([.15,.145,.04] if side=='left' else [.14,.09,.045]);mesh=meshes[side]
 t=next(row['step'] for row in j['rows'] if row['mode']=='tip_press');z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');initial=z['q'][t,12:23];rot=Rotation.from_quat(ori[key][t]).as_matrix();center=tr[key][t];axis=int(np.argmax(abs(rot[1,:2])));sign=1 if -direction*rot[1,axis]>=0 else -1;n=sign*rot[:,axis];surface=side_surface_point(center,ori[key][t],size,direction)
 for angle_deg in [30,45,60,75]:
  local_front_inset=0.
  goal=np.array(surface);free=1-axis;sgn=-1 if rot[0,free]>=0 else 1;goal+=sgn*(.015-local_front_inset)*rot[:,free]
  theta=np.deg2rad(angle_deg);n=sign*rot[:,axis]*np.sin(theta)+sgn*rot[:,free]*np.cos(theta)
  def measure(q):
   d=dict(zip(names,q));m=fk(side,d);world=mesh@m[:3,:3].T+m[:3,3];signed=(world-goal)@n;tip=m[:3,:3]@distal_mesh_vertex(side)+m[:3,3];return d,world,tip
  def residual(q):
   d,world,tip=measure(q)
   return np.r_[tip-goal,palm(other,d)-anchor,4*max(0,.755-float(world[:,2].min())),4*max(0,-float(((world-goal)@n).min()))]
  best=None
  for start in [initial,np.zeros(11),*rng.uniform(lo,hi,(5,11))]:
   fit=least_squares(residual,np.clip(start,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=220);d,world,tip=measure(fit.x);err=float(np.linalg.norm(fit.fun))
   if best is None or err<best['error_m']:best=dict(error_m=err,point_error_m=float(np.linalg.norm(tip-goal)),q=fit.x.tolist(),vertex=list(distal_mesh_vertex(side)),world=tip.tolist(),min_hand_z=float(world[:,2].min()),min_signed_side_gap_m=float(((world-goal)@n).min()),waist=float(fit.x[0]))
  row=dict(side=side,frame=t,normal_angle_from_front_deg=angle_deg,front_inset_m=local_front_inset,target_world=goal.tolist(),normal_world=n.tolist(),best=best);rows.append(row);print(side,angle_deg,best['point_error_m'],best['min_hand_z'],best['waist'],best['vertex'],flush=True)
(root/'CORNER_FIXED_TIP_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Offline multistart position IK for convex-hand supporting vertex at front-side object corner, normal interpolated between front and side, with table-height penalty and inactive palm target. Fixed distal tip point objective and continuous maximum-plane-penetration penalty; table bound only hand, not forearm. No full-arm/self/other-object collisions, dynamics, camera or path guarantee. Not global infeasibility proof, never execute q directly.',training_ready=False),indent=2))
