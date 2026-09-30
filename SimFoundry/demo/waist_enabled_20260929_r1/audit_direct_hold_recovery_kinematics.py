"""Offline feasibility of a top recontact after an unfinished direct hold."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]))
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian,skew
from simfoundry.data.top_contact_bypass import TopContactBypassState,top_surface_point
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.bounded_ik import bounded_damped_step
p=Path(sys.argv[1]).resolve();z=np.load(p/'raw.npz');tr=np.load(p/'trace.npz');ori=np.load(p/'parcel_orientation.npz');log=json.loads((p/'frontal_bypass.json').read_text());side='right' if 'push_box' in p.name else 'left';other_side='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other_key='mailer' if side=='right' else 'box'
size=np.array([.14,.09,.045] if side=='right' else [.15,.145,.04]);rows=log['rows'];start=int(sys.argv[2]) if len(sys.argv)>2 else 120;initial=z['q'][start,12:23].astype(float);target=tr[key][start].copy();obstacle=tr[other_key][start].copy();quat=ori[key][start].copy();rp=Rotation.from_quat(quat).as_matrix();normal=rp[:,2]
coord=next(r for r in json.loads((p/'coordination.json').read_text()) if r['step']>=start);anchor=np.array(coord['inactive_anchor']);vertices=np.array(json.loads((root.parents[1]/'assets/robots/g1_hand_support_vertices.json').read_text())['vertices'][side])
lo[0]=-.98;hi[0]=.98;limits=np.full(11,.04);limits[0]=.015;damping=np.full(11,.045);damping[0]=.12

def fk(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793];axes={}
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   if name in names:axes[names.index(name)]=(m[:3,3].copy(),m[:3,:3]@axis)
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*(q[names.index(name)] if name in names else 0.)).as_matrix();m=m@a
 jl=np.zeros((3,11));jw=np.zeros((3,11))
 for i,(origin,axis) in axes.items():jw[:,i]=axis;jl[:,i]=np.cross(axis,m[:3,3]-origin)
 return m,jl,jw

m,_,_=fk(side,initial)
check=np.linalg.norm(m[:3,3]+m[:3,:3]@np.array([.20,0,.007])-tr['palm_'+side][start])
assert check<1e-6,check
results=[]
for variant in ('projected_front20','projected_center','projected_front20_tol12','projected_front10'):
 q=initial.copy();s=TopContactBypassState(FrontalBypassState(log['plan']),side,tuple(size),guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.012 if variant=='projected_front20_tol12' else .010,front_inset_fraction=1. if variant=='projected_center' else (.01/(size[np.argmax(np.abs(rp[0,:2]))]/2) if variant=='projected_front10' else None))
 m,_,_=fk(side,q);ref=projected_support_reference(vertices,m[:3,:3],normal);s.top_mode='top_lift';s.start=tuple(m[:3,3]+m[:3,:3]@ref['reference_local']);history=[];previous=None;maxjump=0.
 for step in range(400):
  m,jl,jw=fk(side,q);r=m[:3,:3];ref=projected_support_reference(vertices,r,normal);offset=ref['reference_local'] if variant.startswith('projected') else ref['lowest_vertex_local'];point=m[:3,3]+r@offset
  ja=projected_support_jacobian(jl,jw,r,ref) if variant.startswith('projected') else jl-skew(r@offset)@jw
  mi,jli,jwi=fk(other_side,q);po=np.array([.20,0,.007]);pi=mi[:3,3]+mi[:3,:3]@po;ji=jli-skew(mi[:3,:3]@po)@jwi
  row=s.update(point,target,obstacle,.075,.075,tip=point,quat=quat,control_offset_local=offset,load_n=0.)
  surface=np.array(row['parcel_top_xyz']);error=point-surface
  actual_low=m[:3,3]+r@ref['lowest_vertex_local'];local=rp.T@(actual_low-target);margin=float(min(size[:2]/2-np.abs(local[:2])))
  heights=vertices@(r.T@normal);near=vertices[heights-heights.min()<=.0002];local_near=((m[:3,3]+near@r.T)-target)@rp
  scale=np.array([.96,.96] if side=='right' else [.90,.88]);core_margin=float(np.min(size[:2]*scale/2-np.abs(local_near[:,:2])))
  if previous is not None:maxjump=max(maxjump,float(np.linalg.norm(offset-previous)))
  previous=offset.copy()
  history.append(dict(step=step,mode=row['mode'],xy_error_m=float(np.max(abs(error[:2]))),reference_top_gap_m=float(normal@error),actual_lowest_vertex_face_margin_m=margin,near_support_0p2mm_collision_core_face_margin_m=core_margin,reference_local=offset.tolist(),q=q.tolist()))
  if row['mode']=='top_press':break
  jac=np.vstack([ja,ji]);err=np.r_[np.clip(.72*(np.array(row['target_xyz'])-point),-.035,.035),np.clip(.72*(anchor-pi),-.035,.035)]
  if variant=='vertex_angular_damping_0.10':jac=np.vstack([jac,.10*jw]);err=np.r_[err,[0.,0.,0.]]
  q+=bounded_damped_step(jac,err,q,lo,hi,limits,damping)
 result=dict(variant=variant,reached_press=history[-1]['mode']=='top_press',kinematic_steps=len(history),last=history[-1],max_reference_offset_jump_m=maxjump,history=history);results.append(result)
 print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
out=dict(rows=results,start_actual_frame=start,initial_actual_fk_error_m=float(check),raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),scope='Measured initial q/parcel/orientation/inactive anchor; exact cached URDF FK and analytic Jacobians; commanded joints applied instantly with no dynamics/forces/collision. Parcels fixed. Reaching press only tests kinematic approach, NOT physical contact or task success. Projected plane reference is virtual and may lie outside hand hull; report actual lowest vertex target-face margin separately. No active collector or frozen source modified.',training_ready=False)
(p/('DIRECT_HOLD_RECOVERY_KINEMATICS_frame'+str(start)+'.json')).write_text(json.dumps(out,indent=2))
