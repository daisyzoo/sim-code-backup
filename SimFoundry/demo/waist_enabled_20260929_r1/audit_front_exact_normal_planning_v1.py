"""Independent all-support-vertex joint11 certificate; original tolerances.
Rejects ambiguous active elbow axes and uncertified active parcel constraints.
Replaces parent Z equality explicitly; physical/contact/full-stream audits remain separate.
"""
import numpy as np
from loaded_z_priority_checks import NativeCertificateGeometry,check
from loaded_z_priority_solver import up_and_jacobian
from loaded_z_priority_stationarity import certificate,planes
from recontact_scene import RecontactScene

def verify(command,coordinate,*,guard,prediction_policy='original_nondegradation'):
 if prediction_policy not in ('original_nondegradation','absolute_nonseparation'):raise ValueError('Unknown explicit planning policy')
 old=coordinate['joint_transport_clearance'];tc=old['collector_context'];task=coordinate['task_inputs'];elbow_reserve_m=.0015
 q0=np.asarray(tc['current'],float);qp0=np.asarray(tc['previous_q'],float);p0=np.asarray(tc['previous_command'],float);a0=np.asarray(tc['decay'],float);u0=np.asarray(command,float);bias0=q0-p0-a0*(qp0-p0)
 record=dict(current=q0,previous_q=qp0,previous_command=p0,parent_command=old['parent_command'],decay=a0,command=u0,side=tc['scene']['side'],scene=tc['scene'],causal_bias=bias0,predicted_q=(1-a0)*u0+a0*q0+bias0)
 if coordinate['front_loaded_z_priority']['context']['observed_vertical_load_n']<.3:raise ValueError('Unloaded context requires separate recovery strategy')
 G=guard;geo=NativeCertificateGeometry(G)
 q,qp,prev,parent,decay=[np.asarray(record[k],float) for k in ['current','previous_q','previous_command','parent_command','decay']];u=np.asarray(record['command'],float);side=record['side'];inactive='right' if side=='left' else 'left';zr=2 if side=='left' else 5
 for v in [q,qp,prev,parent,decay,u]:
  if v.shape!=(11,) or not np.isfinite(v).all():raise ValueError('Invalid finite11 verification')
 if side not in ('left','right') or record['scene']['side']!=side or np.any(decay<0) or np.any(decay>.95):raise ValueError('Invalid side/response')
 if not np.array_equal(u,u.astype(np.float32)) or not np.array_equal(parent,parent.astype(np.float32)):raise ValueError('Non-float32 command')
 if coordinate['task_inputs']!=task:raise ValueError('Task binding mismatch')
 for key,v in [('current',q),('previous',prev)]:
  if not np.allclose(task[key],v,atol=1e-7,rtol=0):raise ValueError('Stale task context')
 for key,v in [('lower',G.lower),('upper',G.upper),('step_limits',G.limits)]:
  if not np.array_equal(task[key],v):raise ValueError('Changed original bounds')
 bias=q-prev-decay*(qp-prev)
 if not np.allclose(bias,record['causal_bias'],atol=1e-12,rtol=0):raise ValueError('Changed causal bias')
 predicted=(1-decay)*u+decay*q+bias
 if not np.array_equal(predicted,record['predicted_q']):raise ValueError('Changed predicted state')
 def predict(x):return (1-decay)*x+decay*q+bias
 z=record['scene'];scene=RecontactScene(G,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);c=coordinate;J=np.array(task['jacobian']);e=np.array(task['error']);reg=np.array(task['damping'])**2;prior=np.array(task['preferred_step']);target=np.array(c['contact_normal_tracking']['target_local_up']);target/=np.linalg.norm(target);pn=np.linalg.norm(J[6:]@(parent-q)-e[6:]);parent_up,_=up_and_jacobian(G.model,parent,side);pe=np.linalg.norm(parent_up-target)
 nodes=[(kind,alpha) for kind in ['nominal','predicted'] for alpha in [.25,.5,.75,1.]];branches={};ambiguous=[]
 for kind,alpha in nodes:
  state=q+alpha*((u if kind=='nominal' else predict(u))-q)
  for elbow_side,i in [('left',0),('right',1)]:
   gap=geo.gap(state)[i]
   if gap-(.005+(elbow_reserve_m if alpha==1 else 0.))<=1e-6:
    values=planes(geo,state,elbow_side);gaps=values.min(0);branch=int(gaps.argmax());sep=float(np.sort(gaps)[-1]-np.sort(gaps)[-2]);assert abs(gaps[branch]-gap)<1e-12
    if sep<=2e-6:ambiguous.append(dict(kind=kind,alpha=alpha,side=elbow_side,separation=sep))
    branches[kind,alpha,elbow_side]=branch
  details=scene.details(state)
  for name in ['inactive_target','inactive_other','active_other']:
   if details['gaps'][name]-.01<=2e-6:ambiguous.append(dict(kind=kind,alpha=alpha,parcel=name,reason='active_parcel_separating_axis_not_certified'))
 if ambiguous:
  return dict(passed=False,reason='ambiguous_or_unverified_active_branch',details=ambiguous)
 from independent_cross_track_assets_v1 import independent_hand_model
 from scipy.spatial.transform import Rotation
 hand=independent_hand_model(G)
 normal=Rotation.from_quat(z['target_quat']).as_matrix()[:,2];center=np.array(c['active_support_reference']['center_local']);xyrows=slice(0,2) if side=='left' else slice(3,5);directions=np.sign(e[xyrows])
 if np.any(directions==0):raise ValueError('Both original task directions required')
 def independent_point(v):
  T=hand.fk(v,side);n=T[:3,:3].T@normal;off=center+n*(min(hand.vertices[side]@n)-center@n);return T[:3,3]+T[:3,:3]@off
 p_ref=independent_point(q)
 def displacement(v):return independent_point(v)-p_ref
 lower_normal=float(normal@displacement(parent))
 if lower_normal>=0:raise ValueError('Original inward parent required')
 predicted_limit=float(normal@displacement(predict(np.asarray(old['output_command'],float)))) if prediction_policy=='original_nondegradation' else 0.
 # Finite-difference certificate is valid only with a stable support vertex.
 support_branches=[]
 for kind,transform in [('nominal',lambda x:x),('predicted',predict)]:
  ids=[]
  for perturb in [np.zeros(11)]+[v for j in range(11) for v in [np.eye(11)[j]*2e-7,-np.eye(11)[j]*2e-7]]:
   T=hand.fk(transform(u+perturb),side);scores=hand.vertices[side]@(T[:3,:3].T@normal);ids.append(int(np.argmin(scores)))
  support_branches.append(dict(kind=kind,indices=ids,stable=len(set(ids))==1))
 if not all(r['stable'] for r in support_branches):return dict(passed=False,reason='support_vertex_changes_under_certificate_difference',support_branches=support_branches)
 def extra(x):
  pred=predict(x);err=J@(x-q)-e;up,_=up_and_jacobian(G.model,x,side);parts=[pn-np.linalg.norm(err[6:]),pe-np.linalg.norm(up-target)];parts.extend(pred-G.lower);parts.extend(G.upper-pred)
  for kind,alpha in nodes:
   state=q+alpha*((x if kind=='nominal' else pred)-q);T,_,_=G.model.fk(inactive,state);points=G.model.vertices[inactive]@T[:3,:3].T+T[:3,3];floor=.8415 if alpha==1 else .84;parts.extend(points[:,2]-floor);details=scene.details(state)
   parts.extend(details['gaps'][name]-.01 for name in ['inactive_target','inactive_other','active_other'])
   for elbow_side,i in [('left',0),('right',1)]:
    if (kind,alpha,elbow_side) in branches:parts.extend(planes(geo,state,elbow_side)[:,branches[kind,alpha,elbow_side]]-(.005+(elbow_reserve_m if alpha==1 else 0.)))
    else:parts.append(geo.gap(state)[i]-(.005+(elbow_reserve_m if alpha==1 else 0.)))
  dn=displacement(x);dp=displacement(pred);return np.r_[parts,directions*dn[:2],directions*dp[:2],normal@dn-lower_normal,-normal@dn,predicted_limit-normal@dp]
 values=extra(u);jac=np.empty((len(values),11));h=2e-7
 for j in range(11):
  offset=np.eye(11)[j]*h;jac[:,j]=(extra(u+offset)-extra(u-offset))/(2*h)
 lo=np.maximum.reduce([G.lower,q-G.limits,prev-.055]);hi=np.minimum.reduce([G.upper,q+G.limits,prev+.055]);delta=u-q;gradient=J.T@(J@delta-e)+reg*(delta-prior);cert=certificate(geometry=geo,x=u,gradient=gradient,lower=lo,upper=hi,extra_values=values,extra_jacobian=jac)
 nominal=G.command(u,q,prev)
 nom_delta=displacement(u);pred_delta=displacement(predicted)
 point_checks=dict(nominal_xy_nonreversal=bool(min(directions*nom_delta[:2])>=-2e-7),predicted_xy_nonreversal=bool(min(directions*pred_delta[:2])>=-2e-7),exact_normal_band=bool(lower_normal-2e-7<=normal@nom_delta<=2e-7),predicted_normal_bound=bool(normal@pred_delta<=predicted_limit+2e-7))
 checks=dict(**point_checks,all_reconstructed_primal=bool(values.min()>=-2e-7),stationarity=bool(cert['passed']),original_command_guard=bool(nominal['accepted']))
 return dict(passed=bool(all(checks.values())),checks=checks,certificate=cert,nominal_command_guard=nominal,nominal_delta_m=nom_delta.tolist(),predicted_delta_m=pred_delta.tolist(),normal_lower_m=lower_normal,predicted_normal_limit_m=predicted_limit,support_branches=support_branches,prediction_policy=prediction_policy,scope='Independent command/context reconstruction with original numerical thresholds and declared new exact-normal planning interval. No original parent-Z-equality claim; no physical success.',physical_success=False)
