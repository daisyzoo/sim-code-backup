"""Offline actual distal mesh-point reach; no force, collision or trajectory certificate."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
import struct
rng=np.random.default_rng(933);rows=[]
def point(side,q,offset):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m[:3,:3]@offset+m[:3,3]
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 b=(urdf.parent/'meshes'/f'{side}_wrist_roll_rubber_hand.STL').read_bytes();dtype=np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attr','<u2')]);verts=np.frombuffer(b[84:],dtype=dtype)['vertices'].reshape(-1,3);offset=verts[np.argmax(verts[:,0])].astype(float)
 ep=root/'frontal_follow_y_smoke_r1/case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());transition=next(x for x in j['rows'] if x['mode']=='bypass_sweep');t=transition['step'];other='right' if side=='left' else 'left';target='box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1
 with np.load(ep/'raw.npz') as z:initial=z['q'][t,12:23].copy()
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[target][t]).as_matrix()
 xyz=np.array(transition['observed_target']);size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);anchor=np.array(j['plan']['inactive_anchor_override']['xyz'])
 for inward_x in [.015,.03,.05]:
  local=np.array([-size[0]/2+inward_x,-direction*size[1]/2,.005]);target_point=xyz+rot@local
  for kind,off in [('distal_mesh_vertex',offset),('palm_proxy',np.array([.2,0,.007]))]:
   def residual(q):
    d=dict(zip(names,q));return np.r_[point(side,d,off)-target_point,palm(other,d)-anchor]
   best=None
   for q in [initial,np.zeros(11),*rng.uniform(lo,hi,(3,11))]:
    fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=180);v=float(np.linalg.norm(fit.fun))
    if best is None or v<best['error_m']:best=dict(error_m=v,q=fit.x.tolist(),actual_point=point(side,dict(zip(names,fit.x)),off).tolist(),actual_palm=palm(side,dict(zip(names,fit.x))).tolist())
   rows.append(dict(side=side,kind=kind,local_control_point=off.tolist(),parcel_local_contact=local.tolist(),target_world=target_point.tolist(),best=best));print(side,kind,inward_x,v if best is None else best['error_m'],flush=True)
(root/'FINGERTIP_CONTACT_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Static multi-start contact-point position+inactive palm only. Actual STL extremal vertex used, not arbitrary extended tool. No object/arm collision, orientation, dynamics or force guarantee; low residual is candidate only; high residual not impossibility proof. Do not directly execute joint solutions.',training_ready=False),indent=2))
