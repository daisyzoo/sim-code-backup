"""Bilateral inactive-five version; active side is taken from the verified scene.
Independent original-tolerance certificate for inactive-five proposals.
Frozen waist/left commands are equality bounds. Every hand support vertex is a
height inequality, so vertex ties are retained. Active parcel separating-axis
ambiguity is rejected; this draft only certifies strictly separated parcels.
Uses original 1e-6 stationarity and primal tolerances, no optimizer status trust.
"""
import numpy as np
from loaded_z_priority_checks import NativeCertificateGeometry
from loaded_z_priority_stationarity import certificate,planes
from audit_front_recontact_center_events import RecoveryEventAudit

def verify(record,task_inputs,*,root,stage,guard):
 q=np.array(record['current']);qp=np.array(record['previous_q']);prev=np.array(record['previous_command']);parent=np.array(record['parent_command']);x=np.array(record['command']);decay=np.array(record['decay']);scene=record['scene'];a=task_inputs
 active_side=scene['side'];inactive_side='right' if active_side=='left' else 'left';inactive_indices=np.arange(6,11) if active_side=='left' else np.arange(1,6);fixed_indices=np.setdiff1d(np.arange(11),inactive_indices)
 if not np.array_equal(x,x.astype(np.float32)) or not np.array_equal(x[fixed_indices],parent[fixed_indices]):raise ValueError('Changed active command or unrounded output')
 if scene['side'] not in ('left','right'):raise ValueError('Wrong side')
 for key,v in [('current',q),('previous',prev)]:
  if not np.allclose(a[key],v,atol=1e-7,rtol=0):raise ValueError('Stale original task')
 for key,v in [('lower',guard.lower),('upper',guard.upper),('step_limits',guard.limits)]:
  if not np.array_equal(np.array(a[key]),v):raise ValueError('Changed original bounds')
 bias=q-prev-decay*(qp-prev)
 if not np.allclose(record['causal_bias'],bias,atol=1e-12,rtol=0):raise ValueError('Changed response estimate')
 pred=(1-decay)*x+decay*q+bias
 if not np.array_equal(pred,np.array(record['predicted_q'])):raise ValueError('Changed predicted state')
 audit=RecoveryEventAudit(root,stage);geometry=NativeCertificateGeometry(guard)
 nominal_guard=guard.command(x,q,prev)
 pred_bounds=bool(np.all(pred>=guard.lower-2e-7) and np.all(pred<=guard.upper+2e-7));nominal_paths=record['sampled_paths']
 # Task preservation checked independently of the solver: inactive columns of
 # active position and normal rows must vanish, and active FK must match parent.
 J=np.array(a['jacobian']);e=np.array(a['error']);D=np.array(a['damping'])**2;prior=np.array(a['preferred_step']);assert J.shape==(9,11) and e.shape==(9,)
 if np.max(abs(J[np.ix_(np.r_[np.arange(0,3) if active_side=='left' else np.arange(3,6),6:9],inactive_indices)]))>1e-12:raise ValueError('Inactive columns affect active task')
 if not np.array_equal(audit.hand.fk(x,active_side),audit.hand.fk(parent,active_side)):raise ValueError('Active geometry changed')
 pred_elbow=geometry.gap(pred);pred_branch={}
 for i,side in enumerate(['left','right']):
  if pred_elbow[i]-.005<=1e-6:
   values=planes(geometry,pred,side);gaps=values.min(0);branch=int(gaps.argmax());separation=float(np.sort(gaps)[-1]-np.sort(gaps)[-2])
   if separation<=2e-6:return dict(passed=False,reason='ambiguous_predicted_elbow_axis')
   pred_branch[side]=branch
 def extra(u):
  v=(1-decay)*u+decay*q+bias;parts=[]
  for z in [u,v]:
   T=audit.hand.fk(z,inactive_side);points=audit.hand.vertices[inactive_side]@T[:3,:3].T+T[:3,3];parts.extend(points[:,2]-.8415)
  for i,side in enumerate(['left','right']):
   if side in pred_branch:parts.extend(planes(geometry,v,side)[:,pred_branch[side]]-.005)
   else:parts.append(geometry.gap(v)[i]-.005)
  parts.extend(v-guard.lower);parts.extend(guard.upper-v)
  return np.asarray(parts)
 for z in [x,pred]:
  T=audit.hand.fk(z,inactive_side)
  gaps=[audit.gap(inactive_side,T,scene['target_xyz'],scene['target_quat'],scene['core_size']),audit.gap(inactive_side,T,scene['other_xyz'],scene['other_quat'],scene['other_size'])]
  if min(gaps)-.01<=2e-6:return dict(passed=False,reason='active_parcel_constraint_not_certified',gaps=gaps)
 values=extra(x);grad_extra=np.empty((len(values),11));h=2e-7
 for j in range(11):
  step=np.eye(11)[j]*h;grad_extra[:,j]=(extra(x+step)-extra(x-step))/(2*h)
 lo=np.maximum.reduce([guard.lower,q-guard.limits,prev-.055]);hi=np.minimum.reduce([guard.upper,q+guard.limits,prev+.055]);lo[fixed_indices]=hi[fixed_indices]=parent[fixed_indices]
 delta=x-q;gradient=J.T@(J@delta-e)+D*(delta-prior);cert=certificate(geometry=geometry,x=x,gradient=gradient,lower=lo,upper=hi,extra_values=values,extra_jacobian=grad_extra)
 return dict(passed=bool(cert['passed'] and nominal_guard['accepted'] and pred_bounds and min(pred_elbow)>=.005-2e-7),nominal_command_guard=nominal_guard,predicted_joint_bounds=pred_bounds,predicted_elbow_gaps_m=pred_elbow.tolist(),height_all_vertices_checked=True,height_constraint_count=2*len(audit.hand.vertices[inactive_side]),certificate=cert,scope=__doc__,physical_success=False)
