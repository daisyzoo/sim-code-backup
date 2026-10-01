"""Actual failed states: position IK with original calibrated camera constraints."""
from pathlib import Path
import sys,ast,json,hashlib,itertools
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
source=(root/'audit_terminal_reach.py').read_text();exec(compile(source.split("p=root/'contact_x_ablation")[0],'<cached_fk_only>','exec'))
from simfoundry.data.top_contact_visibility import camera_grid
from simfoundry.data.hand_obstacle_clearance import hand_face_separation
from simfoundry.data.top_contact_bypass import rotation_xyzw
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ['U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI']:
  globals()[node.target.id]=np.array(ast.literal_eval(node.value))[12:]
lo=U1_JOINT_LIMIT_LO.copy();hi=U1_JOINT_LIMIT_HI.copy();lo[0]=-.98;hi[0]=.98

def transform(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q[names.index(name)]).as_matrix();m=m@a
 return m

def camera_fraction(center,quat,size,intr,width,height):
 yaws,positions,rotations=camera_grid(.98)
 corners=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(size)/2
 world=corners@np.array(rotation_xyzw(quat)).T+center
 camera=np.einsum('nki,nij->nkj',world[None]-positions[:,None],rotations)
 fx,fy,cx,cy=intr;depth=camera[:,:,2];uv=np.stack([fx*camera[:,:,0]/depth+cx,fy*camera[:,:,1]/depth+cy],axis=-1)
 low,high=uv.min(1),uv.max(1);area=np.prod(high-low,axis=1);intersection=np.maximum(0,np.minimum(high,[width,height])-np.maximum(low,[0,0]))
 return yaws,np.where((depth>0).all(1),np.prod(intersection,axis=1)/np.maximum(area,1e-12),0.)

run=root/'fresh_lateral_00_pilot_r1';results=[];rng=np.random.default_rng(20260930)
for ep in sorted(run.glob('case_840001/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:qs=z['q'];intr=z['intrinsics'];rgbshape=z['rgb'].shape
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 controls=json.loads((ep/'expert_control.json').read_text());coords=json.loads((ep/'coordination.json').read_text());t=1199;record=coords[-1];q0=qs[t,12:].astype(float);offset=np.array(record['active_point_offset_local'] or [.20,0,.007]);goal=np.array(controls[t]['target_xyz']);anchor=np.array(record['inactive_anchor'])
 fkerrors={s:float(np.linalg.norm(transform(s,q0)[:3,:3]@np.array([.20,0,.007])+transform(s,q0)[:3,3]-tr['palm_'+s][t])) for s in ('left','right')};assert max(fkerrors.values())<.0001,fkerrors
 yaws,fractions=camera_fraction(tr[key][t],ori[key][t],size,intr,rgbshape[3],rgbshape[2]);allowed=np.flatnonzero(fractions>=.5);assert len(allowed)>1 and np.all(np.diff(allowed)==1)
 window=[float(yaws[allowed[0]]),float(yaws[allowed[-1]])];rows=[]
 for visible in (False,True):
  for keep_inactive in (True,False):
   lower=lo.copy();upper=hi.copy()
   if visible:lower[0],upper[0]=window
   def residual(q):
    a=transform(side,q);b=transform(inactive,q);active=a[:3,:3]@offset+a[:3,3]-goal
    return np.r_[active,b[:3,:3]@np.array([.20,0,.007])+b[:3,3]-anchor] if keep_inactive else active
   best=None
   starts=[q0,np.zeros(11),*rng.uniform(lower,upper,(3,11))]
   for start in starts:
    fit=least_squares(residual,np.clip(start,lower+1e-6,upper-1e-6),bounds=(lower,upper),max_nfev=200,ftol=1e-10,xtol=1e-10,gtol=1e-10)
    if best is None or np.linalg.norm(fit.fun)<np.linalg.norm(best.fun):best=fit
   q=best.x;a=transform(side,q);b=transform(inactive,q);active_error=float(np.linalg.norm(a[:3,:3]@offset+a[:3,3]-goal));inactive_error=float(np.linalg.norm(b[:3,:3]@np.array([.20,0,.007])+b[:3,3]-anchor))
   gap=hand_face_separation(side).gap(a[:3,3],Rotation.from_matrix(a[:3,:3]).as_quat(),tr[other][t],ori[other][t],other_size)
   row=dict(camera_constraint=visible,inactive_anchor_constraint=keep_inactive,active_position_error_m=active_error,inactive_anchor_error_m=inactive_error,waist_rad=float(q[0]),projected_bbox_fraction=float(np.interp(q[0],yaws,fractions)),active_hand_other_face_gap_m=gap,q=q.tolist());rows.append(row);print(ep.name,{k:v for k,v in row.items() if k!='q'},flush=True)
 results.append(dict(episode=ep.name,recorded_fk_errors_m=fkerrors,measured_active_point_goal=goal.tolist(),recorded_waist_rad=float(q0[0]),visible_waist_window=window,rows=rows,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
(run/'CAMERA_REACH_SCREEN.json').write_text(json.dumps(dict(results=results,scope='Offline bounded multistart position IK on two actual failed terminal states; saved fixed active local point and inactive anchor. Original camera and literal current working arm bounds.50% projected bbox constraint is a diagnostic screen, not new quality gate. No orientation, all-arm/table collision, continuous path, real contact or dynamics proof; inactive-free solves are hypotheses only and must not be executed directly. Failure is not global infeasibility proof.',training_ready=False),indent=2))
