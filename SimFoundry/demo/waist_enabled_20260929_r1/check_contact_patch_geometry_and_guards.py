"""Measured palm agreement, numerical Jacobians and unsafe-input refusal."""
from pathlib import Path
import sys,json,hashlib,numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_contact_patch_approach';sys.path[:0]=[str(stage),str(repo)]
from articulated_hand_geometry import ArticulatedHandGeometry
from contact_patch_approach import contact_patch_step
from scipy.spatial.transform import Rotation
import ast
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
limits={}
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ['U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI']:limits[node.target.id]=np.array(ast.literal_eval(node.value))[12:]
lo=limits['U1_JOINT_LIMIT_LO'];hi=limits['U1_JOINT_LIMIT_HI'];lo[0]=-.98;hi[0]=.98;step=np.full(11,.04);step[0]=.015;damping=np.full(11,.045);damping[0]=.12
cases=[(w/'contact_bout_yaw_groups_r1/case_898001/layout_898001_push_box_to_bin',117),(w/'fresh_diagonal_02_trial_v2_r1/case_840004/layout_840004_nudge_mailer_to_bin',100)];reports=[]
for ep,t in cases:
 side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:trace={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 errors=[]
 for frame in sorted(set([0,t,1199]+list(range(0,1200,60)))):
  for hand in ['left','right']:
   mat,_,_=model.fk(hand,qs[frame]);error=float(np.linalg.norm(mat[:3,3]+mat[:3,:3]@np.array([.20,0,.007])-trace['palm_'+hand][frame]));assert error<.0001;errors.append(error)
 q=qs[t];mat,jl,jw=model.fk(side,q);jerrors=[]
 for i in range(11):
  d=np.zeros(11);d[i]=1e-6;plus=model.fk(side,q+d)[0];minus=model.fk(side,q-d)[0];numeric_linear=(plus[:3,3]-minus[:3,3])/2e-6;numeric_angular=Rotation.from_matrix(plus[:3,:3]@minus[:3,:3].T).as_rotvec()/2e-6;jerrors.extend([float(np.max(abs(numeric_linear-jl[:,i]))),float(np.max(abs(numeric_angular-jw[:,i])))])
 assert max(jerrors)<1e-7
 anchor=np.array(next(x for x in json.loads((ep/'coordination.json').read_text()) if x['step']==t)['inactive_anchor'])
 def geometry(q):return model.scene_geometry(side,q,target_xyz=trace[key][t],target_quat=ori[key][t],other_xyz=trace[other][t],other_quat=ori[other][t],other_size=other_size)
 kw=dict(lower=lo,upper=hi,step_limits=step,damping=damping,target_size=size,inactive_anchor=anchor)
 def changed(q,kind):
  g=geometry(q)
  if kind=='other_collision':g['hand_other_gap_m']=.004
  if kind=='outside_target':g['target_xyz']=g['target_xyz']+np.array([1.,0,0])
  if kind=='nonfinite_geometry':g['hand_xyz']=np.array([float('nan'),0,0])
  if kind=='bad_jacobian':g['angular_jacobian']=np.zeros((2,11))
  if kind=='already_contacting':
   normal=g['target_rotation'][:,2];world=g['vertices']@g['hand_rotation'].T+g['hand_xyz'];height=float(((world-g['target_xyz'])@normal).min()-size[2]/2);g['target_xyz']=g['target_xyz']+normal*(height-.001)
  return g
 negative=[]
 for kind in ['other_collision','outside_target','nonfinite_geometry','bad_jacobian','already_contacting','outside_joint_bounds']:
  badq=q.copy()
  if kind=='outside_joint_bounds':badq[0]=lo[0]-.01
  try:r=contact_patch_step(badq,lambda q:changed(q,kind),**kw);assert not r['accepted'];reason=r['reason']
  except ValueError as e:reason=str(e)
  negative.append(dict(case=kind,rejected=True,reason=reason))
 reports.append(dict(episode=ep.name,recorded_palm_samples=len(errors),max_actual_palm_error_m=max(errors),max_numerical_jacobian_error=max(jerrors),negative_cases=negative))
out=dict(rows=reports,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [stage/'contact_patch_approach.py',stage/'articulated_hand_geometry.py',Path(__file__)]},scope='Actual recorded FK crosscheck and independent central-difference Jacobians; constructed unsafe inputs for refusal checks only, not physical demonstrations or training data.',training_ready=False)
(stage/'GEOMETRY_AND_GUARD_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(reports,indent=2))
