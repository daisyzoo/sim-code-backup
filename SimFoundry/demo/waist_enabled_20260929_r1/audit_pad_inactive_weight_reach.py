"""Actual new-route poses: distinguish local tracking failure from range limits."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'audit_terminal_reach.py').read_text()
exec(compile(source.split('results=[];rng')[0],'<validated_cached_fk_setup>','exec'))
import sys
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.fingertip_bypass import contact_pad_mesh_vertex,side_surface_point
rng=np.random.default_rng(934);rows=[]
def point(side,q,offset):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,orig,axis in chains[side]:
  m=m@orig
  if axis is not None:r=np.eye(4);r[:3,:3]=Rotation.from_rotvec(axis*q.get(name,0)).as_matrix();m=m@r
 return m[:3,:3]@offset+m[:3,3]
for side,task in [('left','nudge_mailer_to_bin'),('right','push_box_to_bin')]:
 ep=root/'frontal_contact_pad_r1/case_62000'/f'layout_62000_{task}';j=json.loads((ep/'frontal_bypass.json').read_text());other='right' if side=='left' else 'left';anchor=np.array(j['plan']['inactive_anchor_override']['xyz']);target='mailer' if side=='left' else 'box';direction=1 if side=='left' else -1;size=(.15,.145,.04) if side=='left' else (.14,.09,.045);off=np.array(contact_pad_mesh_vertex(side))
 z=np.load(ep/'raw.npz');ori=np.load(ep/'parcel_orientation.npz');tr=np.load(ep/'trace.npz');phases=j['rows'];first=next((v['step'] for v in phases if v['mode']=='tip_sweep'),phases[-1]['step'])
 for t in [319]:
  initial=z['q'][t,12:23].copy();target_point=np.array(side_surface_point(tr[target][t],ori[target][t],size,direction));target_point[1]+=direction*.004
  for weight in [1.,.2,0.]:
   bound=.98
   lo[0]=-bound;hi[0]=bound
   def residual(q):
    d=dict(zip(names,q));return np.r_[point(side,d,off)-target_point,weight*(palm(other,d)-anchor)]
   best=None;from_recorded=None
   for i,q in enumerate([initial,np.zeros(11),*rng.uniform(lo,hi,(3,11))]):
    fit=least_squares(residual,np.clip(q,lo+1e-6,hi-1e-6),bounds=(lo,hi),max_nfev=200);v=float(np.linalg.norm(fit.fun))
    if i==0:from_recorded=v
    if best is None or v<best['error_m']:best=dict(error_m=v,waist=float(fit.x[0]),q=fit.x.tolist(),actual_point=point(side,dict(zip(names,fit.x)),off).tolist(),active_error_m=float(np.linalg.norm(fit.fun[:3])),inactive_displacement_from_anchor_m=float(np.linalg.norm(palm(other,dict(zip(names,fit.x)))-anchor)))
   rows.append(dict(side=side,frame=t,inactive_weight=weight,waist_command_bound=bound,target_world=target_point.tolist(),from_recorded_start_error_m=from_recorded,best=best));print(side,t,weight,best['error_m'],best['waist'],flush=True)
(root/'PAD_INACTIVE_WEIGHT_REACH_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Offline candidates only. Wider bounds are not yet physically tested/approved. Diagnostic bounds already preflighted, solutions not executed. No self/arm/object collision, orientation or force guarantee. High residual is not global infeasibility proof. No joint solution may be executed directly.',training_ready=False),indent=2))
