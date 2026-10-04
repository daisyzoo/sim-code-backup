"""Independent all-support-vertex joint11 certificate; original tolerances.
Rejects ambiguous active elbow axes and uncertified active parcel constraints.
Original parent loaded-contact and full actual stream audits remain separate.
"""
import numpy as np
from loaded_z_priority_checks import NativeCertificateGeometry,check
from loaded_z_priority_solver import up_and_jacobian
from loaded_z_priority_stationarity import certificate,planes
from recontact_scene import RecontactScene

def verify(record,task,coordinate,*,guard,elbow_reserve_m,quarter_enabled=False):
 if elbow_reserve_m not in (0.,.0015) or record['elbow_reserve_m']!=elbow_reserve_m or record['nominal_predicted_elbow_floor_m']!=.005+elbow_reserve_m:raise ValueError('Changed reserve policy')
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
 def extra(x):
  pred=predict(x);err=J@(x-q)-e;up,_=up_and_jacobian(G.model,x,side);height=float(J[zr]@(x-parent));parts=[height,-height,pn-np.linalg.norm(err[6:]),pe-np.linalg.norm(up-target)];parts.extend(pred-G.lower);parts.extend(G.upper-pred)
  for kind,alpha in nodes:
   state=q+alpha*((x if kind=='nominal' else pred)-q);T,_,_=G.model.fk(inactive,state);points=G.model.vertices[inactive]@T[:3,:3].T+T[:3,3];floor=.8415 if alpha==1 else .84;parts.extend(points[:,2]-floor);details=scene.details(state)
   parts.extend(details['gaps'][name]-.01 for name in ['inactive_target','inactive_other','active_other'])
   for elbow_side,i in [('left',0),('right',1)]:
    if (kind,alpha,elbow_side) in branches:parts.extend(planes(geo,state,elbow_side)[:,branches[kind,alpha,elbow_side]]-(.005+(elbow_reserve_m if alpha==1 else 0.)))
    else:parts.append(geo.gap(state)[i]-(.005+(elbow_reserve_m if alpha==1 else 0.)))
  return np.array(parts)
 values=extra(u);jac=np.empty((len(values),11));h=2e-7
 for j in range(11):
  offset=np.eye(11)[j]*h;jac[:,j]=(extra(u+offset)-extra(u-offset))/(2*h)
 lo=np.maximum.reduce([G.lower,q-G.limits,prev-.055]);hi=np.minimum.reduce([G.upper,q+G.limits,prev+.055]);delta=u-q;gradient=J.T@(J@delta-e)+reg*(delta-prior);cert=certificate(geometry=geo,x=u,gradient=gradient,lower=lo,upper=hi,extra_values=values,extra_jacobian=jac)
 from effective_loaded_contact_task_v1 import resolve
 contact_task,binding=resolve(coordinate,side=side,current=q,parent_command=parent,quarter_enabled=quarter_enabled)
 nominal=G.command(u,q,prev);contact=check(G,geo,contact_task,coordinate,parent,u,side);loaded=bool(coordinate['front_loaded_z_priority']['applied']);height_error=float(J[zr]@(u-parent))
 checks=dict(stationarity=bool(cert['passed']),original_command_guard=bool(nominal['accepted']),parent_height_preserved=abs(height_error)<=2e-7,loaded_height_original_gate=(not loaded or abs(contact['z_error_mm'])<=.0002),linear_normal_non_degradation=contact['linear_attitude_delta_mm']<=.0002,exact_normal_non_degradation=contact['exact_attitude_delta']<=1e-6,original_table_margin=min(contact['nominal_table_margins_m'])>=0)
 return dict(passed=bool(all(checks.values())),checks=checks,certificate=cert,nominal_command_guard=nominal,parent_height_error_m=height_error,original_contact_primal=contact,scope=__doc__,effective_loaded_contact_binding=binding,physical_success=False)
