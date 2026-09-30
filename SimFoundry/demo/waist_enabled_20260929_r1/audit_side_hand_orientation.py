"""Position plus hand-face orientation candidates. Not executable trajectories."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
import sys
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.fingertip_bypass import side_surface_point
rng=np.random.default_rng(935);rows=[]
def mat(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 ep=root/'frontal_tip_side_smoke_r1/case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());t=next(v['step'] for v in j['rows'] if v['mode']=='tip_cross');other='right' if side=='left' else 'left';target='mailer' if side=='left' else 'box';direction=1 if side=='left' else -1;size=(.15,.145,.04) if side=='left' else (.14,.09,.045);off=np.array([.2377435714006424,.0004926625406369567 if side=='left' else -.0004926625406369567,.00818553939461708]);anchor=np.array(j['plan']['inactive_anchor_override']['xyz'])
 b=(urdf.parent/'meshes'/f'{side}_wrist_roll_rubber_hand.STL').read_bytes();verts=np.unique(np.frombuffer(b[84:],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')]))['v'].reshape(-1,3),axis=0)
 z=np.load(ep/'raw.npz');tr=np.load(ep/'trace.npz');ori=np.load(ep/'parcel_orientation.npz');initial=z['q'][t,12:23].copy();point=np.array(side_surface_point(tr[target][t],ori[target][t],size,direction));normal=np.array([0,direction,0])
 for bound in [.78,.98]:
  lo[0]=-bound;hi[0]=bound
  def residual(q):
   d=dict(zip(names,q));m=mat(side,d);return np.r_[m[:3,:3]@off+m[:3,3]-point,palm(other,d)-anchor,.15*(m[:3,2]-normal)]
  best=None
  for q in [initial,np.zeros(11),*rng.uniform(lo,hi,(5,11))]:
   fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=300);v=float(np.linalg.norm(fit.fun))
   if best is None or v<best['weighted_error']:
    m=mat(side,dict(zip(names,fit.x)));world=verts@m[:3,:3].T+m[:3,3];over=(world[:,0]>=.28)&(world[:,0]<=.88)&(abs(world[:,1])<=.74)
    best=dict(weighted_error=v,point_error_m=float(np.linalg.norm(fit.fun[:3])),inactive_error_m=float(np.linalg.norm(fit.fun[3:6])),normal_angle_deg=float(np.rad2deg(np.arccos(np.clip(m[:3,2]@normal,-1,1)))),waist=float(fit.x[0]),min_hand_vertex_z_over_table=float(world[over,2].min()) if over.any() else None,q=fit.x.tolist())
  rows.append(dict(side=side,frame=t,bound=bound,control_offset=off.tolist(),target_point=point.tolist(),target_hand_normal=normal.tolist(),best=best));print(side,bound,best,flush=True)
(root/'SIDE_HAND_ORIENTATION_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Static weighted position+hand-local-Z direction IK; actual STL vertex minZ sampled over table, not full surface/forearm/self/non-target collision proof. Do not execute solutions directly.',training_ready=False),indent=2))
