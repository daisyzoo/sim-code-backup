"""Fixed-waist top-contact IK feasibility; no candidate directly executed."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.top_contact_bypass import support_mesh,top_surface_point
meshes={s:np.array(v) for s,v in support_mesh().items()}
def fk(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m
rng=np.random.default_rng(529);rows=[]
run_name=sys.argv[1] if len(sys.argv)>1 else 'frontal_top_load5_r1';min_step=int(sys.argv[2]) if len(sys.argv)>2 else 0;side_filter=sys.argv[3] if len(sys.argv)>3 else None
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 if side_filter and side!=side_filter:continue
 ep=root/run_name/'case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());other='right' if side=='left' else 'left';anchor=np.array(j['plan']['inactive_anchor_override']['xyz']);key='mailer' if side=='left' else 'box';size=np.array([.15,.145,.04] if side=='left' else [.14,.09,.045]);mesh=meshes[side]
 t=next(row['step'] for row in j['rows'] if row['mode']=='top_push' and row['step']>=min_step);z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');initial=z['q'][t,12:23];rot=Rotation.from_quat(ori[key][t]).as_matrix();center=tr[key][t];goal=np.array(top_surface_point(center,ori[key][t],size));n=rot[:,2]
 for fixed_waist in [0.,.2,.4,.6,.8]:
  fixed_waist*=(-1 if side=='left' else 1)
  def measure(arms):
   q=np.r_[fixed_waist,arms];d=dict(zip(names,q));m=fk(side,d);world=mesh@m[:3,:3].T+m[:3,3];idx=int(np.argmin((world-goal)@n));return q,d,world,idx
  def residual(arms):
   q,d,world,idx=measure(arms)
   return np.r_[world[idx]-goal,palm(other,d)-anchor,4*max(0,.755-float(world[:,2].min()))]
  best=None
  for start in [initial[1:],np.zeros(10),*rng.uniform(lo[1:],hi[1:],(2,10))]:
   fit=least_squares(residual,np.clip(start,lo[1:]+1e-6,hi[1:]-1e-6),bounds=(lo[1:],hi[1:]),max_nfev=160);q,d,world,idx=measure(fit.x);err=float(np.linalg.norm(fit.fun))
   if best is None or err<best['error_m']:best=dict(error_m=err,point_error_m=float(np.linalg.norm(world[idx]-goal)),inactive_palm_error_m=float(np.linalg.norm(palm(other,d)-anchor)),q=q.tolist(),min_hand_z=float(world[:,2].min()))
  row=dict(side=side,frame=t,waist_rad=fixed_waist,recorded_waist_rad=float(initial[0]),target_world=goal.tolist(),best=best);rows.append(row);print(side,fixed_waist,best['point_error_m'],best['inactive_palm_error_m'],flush=True)
(root/f'LOW_WAIST_TOP_REACH_{run_name}_AFTER_{min_step}_{side_filter or "both"}.json').write_text(json.dumps(dict(rows=rows,scope='Static multistart fixed-waist endpoint IK using actual first-push target pose, convex-hand top support and inactive palm anchor. No path/dynamics/full-arm/other-object/visual proof; failure is not global infeasibility. Candidate q never executed.',training_ready=False),indent=2))
