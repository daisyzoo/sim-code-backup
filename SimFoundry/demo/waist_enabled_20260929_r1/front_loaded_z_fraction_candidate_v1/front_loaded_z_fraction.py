"""Default-off front loaded task refinement; no state/force mutation.
Only verified nominal proposals may replace the original already guarded command.
Original Cartesian state machine/pressure remain unchanged, final guard follows.
Fraction1 exactly retains the parent implementation; fraction<1 explicitly
changes the candidate Z objective/equality. This isolated candidate is unwired.
Every rejected or inapplicable proposal returns the original float32 command.
"""
import numpy as np
from loaded_z_priority_solver import solve
from loaded_z_priority_checks import NativeCertificateGeometry,check,support_point,nominal_separation_path

def finite(value,shape,name):
 x=np.asarray(value,dtype=float)
 if x.shape!=shape or not np.isfinite(x).all():raise ValueError('Invalid '+name)
 return x

def near(a,b,tol,name):
 if np.asarray(a).shape!=np.asarray(b).shape or np.max(np.abs(np.asarray(a)-np.asarray(b)),initial=0)>tol:raise ValueError('Mismatched '+name)

class FrontLoadedZFraction:
 def __init__(self,guard,fraction=1.):
  if isinstance(fraction,(bool,np.bool_)) or not np.isfinite(fraction) or not 0.<fraction<=1.:raise ValueError('Invalid Z refinement fraction')
  self.fraction=float(fraction);self.guard=guard;self.geometry=NativeCertificateGeometry(guard)
 def refine(self,*,step,selected,row,coordinate,current,previous,parent_command,target_rotation=None,other_xyz=None,other_rotation=None,other_size=None):
  if type(step) is not int or step<0 or type(selected) is not bool:raise ValueError('Invalid step/selection')
  q=finite(current,(11,),'current');prev=finite(previous,(11,),'previous');parent=finite(parent_command,(11,),'parent');near(parent,parent.astype(np.float32),0.,'float32 parent')
  context=dict(step=step,selected=selected,current=q.tolist(),previous=prev.tolist(),parent_command=parent.tolist())
  meta=dict(step=step,selected=selected,applied=False,context=context,training_ready=False)
  def unchanged(reason):return parent.copy(),dict(meta,reason=reason,output_command=parent.tolist())
  if not selected or step==0:return unchanged('not_captured_front_context')
  if not isinstance(row,dict) or not isinstance(coordinate,dict) or row.get('step')!=step or coordinate.get('step')!=step:raise ValueError('Missing current parent records')
  side=coordinate.get('active_side')
  # Parent records do not always include sampled active_side; task is provided by
  # the active support reference position, supplied explicitly by collector.
  side=coordinate.get('front_loaded_z_priority_side',side)
  if side not in ('left','right'):raise ValueError('Missing active side')
  context.update(side=side,mode=row['mode'],observed_vertical_load_n=row.get('contact_load',{}).get('observed_vertical_load_n'))
  if row['mode']!='top_push':return unchanged('not_top_push')
  if row['contact_load']['observed_vertical_load_n']<.3:return unchanged('last_observed_vertical_load_below0.3N')
  if row.get('hand_guard_saturated'):return unchanged('original_hand_guard_saturated')
  if coordinate.get('terminal_joint_hold'):return unchanged('original_terminal_hold')
  a=coordinate.get('task_inputs');normal_record=coordinate.get('contact_normal_tracking')
  if a is None or normal_record is None:return unchanged('no_original_task_or_normal')
  if a['error'][5 if side=='right' else 2]>=0:return unchanged('no_original_downward_task_request')
  if any(isinstance(v,dict) and (v.get('override') is True or v.get('changed') is True) for k,v in coordinate.items() if k not in ['task_inputs','self_clearance_task']):return unchanged('other_actual_post_task_override')
  J=finite(a['jacobian'],(9,11),'jacobian');finite(a['error'],(9,),'error');finite(a['damping'],(11,),'damping');finite(a['preferred_step'],(11,),'prior')
  near(a['current'],q,1e-7,'actual current');near(a['previous'],prev,1e-7,'actual previous');near(a['lower'],self.guard.lower,0.,'lower');near(a['upper'],self.guard.upper,0.,'upper');near(a['step_limits'],self.guard.limits,0.,'step limits')
  if np.min(a['damping'])<=0:raise ValueError('Invalid damping')
  R=finite(target_rotation,(3,3),'target rotation');OR=finite(other_rotation,(3,3),'other rotation');xyz=finite(other_xyz,(3,),'other position');size=finite(other_size,(3,),'other size')
  for rot in [R,OR]:
   if not np.allclose(rot.T@rot,np.eye(3),atol=1e-6) or np.linalg.det(rot)<.999999:raise ValueError('Invalid rotation')
  if min(size)<=0:raise ValueError('Invalid other size')
  conservative_size=np.maximum(size,np.nextafter(size.astype(np.float32),np.float32(np.inf)).astype(float))
  reference=coordinate['active_support_reference'];center=finite(reference['center_local'],(3,),'center');n=R[:,2];near(reference['world_normal'],n,2e-6,'object normal');observed=support_point(self.guard.model,q,side,n,center)
  near(observed,coordinate['control_point_positions'][side],2e-6,'observed control point');near(observed,row['observed_support_xyz'],2e-6,'observed support')
  context.update(target_rotation=R.tolist(),other_xyz=xyz.tolist(),other_rotation=OR.tolist(),other_size=size.tolist(),conservative_other_size=conservative_size.tolist(),center_local=center.tolist(),requested_z_m=float(a['error'][5 if side=='right' else 2]))
  original_guard=self.guard.command(parent,q,prev);meta['parent_final_guard']=original_guard
  if not original_guard['accepted']:return unchanged('original_parent_guard_rejected')
  dz_parent=float(support_point(self.guard.model,parent,side,n,center)[2]-observed[2]);req=context['requested_z_m'];meta['parent_exact_support_delta_z_m']=dz_parent
  if dz_parent<=req:return unchanged('original_already_meets_requested_nominal_downward_step')
  # Keep the unmodified parent task in metadata. Only the candidate Z task
  # changes, and the caller's original coordinate/history remain untouched.
  if self.fraction<1.:
   import copy
   original_task=a;zr=5 if side=='right' else 2
   achieved=float(J[zr]@(parent-q))
   if achieved<=req:return unchanged('parent_linear_z_already_meets_original_request')
   a=copy.deepcopy(original_task);a['error'][zr]=achieved+self.fraction*(req-achieved)
   meta['reduced_z_task']=dict(fraction=self.fraction,original_task=original_task,modified_task=a,parent_linear_z_m=achieved,modified_requested_z_m=a['error'][zr],original_requested_z_m=req)
  x,solver=solve(a,parent=parent,side=side,target_up=normal_record['target_local_up'],hand=self.guard.model,elbows=self.geometry);meta['solver']=solver
  candidate=finite(x,(11,),'candidate');verified=check(self.guard,self.geometry,a,coordinate,parent,candidate,side);meta['nominal_verification']=verified
  if not verified['passed']:return unchanged('nominal_certificate_or_table_rejected')
  dz=float(support_point(self.guard.model,candidate,side,n,center)[2]-observed[2]);meta['candidate_exact_support_delta_z_m']=dz
  if dz>=0:return unchanged('exact_support_motion_not_downward')
  if abs(dz-req)>=abs(dz_parent-req):return unchanged('exact_support_tracking_not_improved')
  paths={s:nominal_separation_path(self.guard.model,q,candidate,s,xyz,OR,conservative_size) for s in ['left','right']};meta['nominal_hands_non_target_paths']=paths
  if not all(p['certified'] for p in paths.values()):return unchanged('nominal_non_target_path_rejected')
  guard=self.guard.command(candidate,q,prev);meta['candidate_final_guard']=guard
  if not guard['accepted']:return unchanged('candidate_final_guard_rejected')
  return candidate,dict(meta,applied=True,reason='verified_nominal_downward_tracking_improvement' if self.fraction==1. else 'verified_reduced_z_task_nominal_improvement',output_command=candidate.tolist())
