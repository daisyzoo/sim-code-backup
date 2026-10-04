"""Independent fractional-Z per-record decision audit, no runtime solver imports.
Checks unchanged as well as applied branches. The enclosing episode audit must
bind actual history, source, selection and original control/quality checks.
"""
import numpy as np
from audit_front_loaded_z_priority_parent import verify_parent,near
from audit_front_loaded_z_fraction_applied_v1 import verify_applied,verify_guard
from audit_front_loaded_z_fraction_task_v1 import verified_task
from front_loaded_z_priority_audit_geometry import evaluate,point,sweep


def verify_record(*,step,selected,metadata,coordinate,row,expert,current,previous_actual,output,side,elbows,bounded_solver,hand,geometry,capture_row,previous_packet,target_xyz,target_rotation,other_xyz,other_rotation,other_size,expected_fraction):
 assert type(expected_fraction) in (int,float) and np.isfinite(expected_fraction) and 0<expected_fraction<=1
 m=metadata;ctx=m['context'];q=np.asarray(current,float);prev=np.asarray(previous_actual,float);out=np.asarray(output,float);parent=np.asarray(ctx['parent_command'],float)
 assert type(step) is int and step>=0 and type(selected) is bool
 assert type(m['applied']) is bool and m['selected'] is ctx['selected'] is selected and m['step']==ctx['step']==step and m['training_ready'] is False
 for value in [q,prev,out,parent]:
  assert value.shape==(11,) and np.isfinite(value).all();near(value,value.astype(np.float32))
 near(ctx['current'],q);near(ctx['previous'],prev);near(m['output_command'],out)
 if coordinate is not None and 'front_loaded_z_priority' in coordinate:assert coordinate['front_loaded_z_priority']==m
 if step==0:
  assert np.max(abs(q))<1e-4;near(prev,np.zeros(11));near(out,np.zeros(11))
 if m['applied']:
  assert selected and step>0
  result=verify_applied(metadata=m,coordinate=coordinate,row=row,expert=expert,current=q,previous_actual=prev,output=out,side=side,elbows=elbows,bounded_solver=bounded_solver,hand=hand,geometry=geometry,capture_row=capture_row,previous_packet=previous_packet,target_xyz=target_xyz,target_rotation=target_rotation,other_xyz=other_xyz,other_rotation=other_rotation,other_size=other_size,expected_fraction=expected_fraction)
  return dict(step=step,passed=True,applied=True,reason=m['reason'],proof=result)
 near(out,parent)
 def unchanged(reason,**proof):
  assert m['reason']==reason,('incorrect fallback',step,m['reason'],reason)
  if reason not in ['nominal_certificate_or_table_rejected','exact_support_motion_not_downward','exact_support_tracking_not_improved','nominal_non_target_path_rejected']:assert 'reduced_z_task' not in m and 'solver' not in m
  return dict(step=step,passed=True,applied=False,reason=reason,proof=proof)
 if not selected or step==0:return unchanged('not_captured_front_context')
 assert row['step']==coordinate['step']==capture_row['step']==step and capture_row['center_local_after'] is not None
 assert ctx['side']==side and ctx['mode']==row['mode']
 assert ctx['observed_vertical_load_n']==row.get('contact_load',{}).get('observed_vertical_load_n')
 if row['mode']!='top_push':return unchanged('not_top_push')
 assert previous_packet['after_action_step']==step-1
 actor='parcel_box' if side=='right' else 'mailer';key='box' if side=='right' else 'mailer';load=0.
 near(previous_packet['post_action_pose'][key],target_xyz,2e-6)
 for contact in previous_packet['parcel_contacts']:
  if any(side+'_wrist_roll' in s for s in contact['shapes']) and any('/'+actor+'/' in s for s in contact['shapes']):
   force=np.asarray(contact['force_world_N'],float);assert force.shape==(3,) and np.isfinite(force).all();load+=abs(float(force[2]))
 near(ctx['observed_vertical_load_n'],load,1e-10)
 if load<.3:return unchanged('last_observed_vertical_load_below0.3N',last_solved_vertical_load_n=load)
 if row.get('hand_guard_saturated'):return unchanged('original_hand_guard_saturated')
 c=coordinate
 if c.get('terminal_joint_hold'):return unchanged('original_terminal_hold')
 a=c.get('task_inputs');normal=c.get('contact_normal_tracking')
 if a is None or normal is None:return unchanged('no_original_task_or_normal')
 req=float(a['error'][5 if side=='right' else 2]);assert np.isfinite(req)
 if req>=0:return unchanged('no_original_downward_task_request')
 if any(isinstance(v,dict) and (v.get('override') is True or v.get('changed') is True) for k,v in c.items() if k not in ['task_inputs','self_clearance_task']):return unchanged('other_actual_post_task_override')
 original=verify_parent(coordinate=c,row=row,expert=expert,current=q,previous_actual=prev,parent=parent,side=side,elbows=elbows,bounded_solver=bounded_solver)
 # Original guard rejection cannot be an actually executed accepted row: the
 # unchanged final guard must stop before stepping physics in that case.
 verify_guard(m['parent_final_guard'],parent,q,prev,a,elbows)
 R=np.asarray(target_rotation,float);OR=np.asarray(other_rotation,float);size=np.asarray(other_size,float)
 for rot in [R,OR]:
  assert rot.shape==(3,3) and np.isfinite(rot).all();near(rot.T@rot,np.eye(3),1e-6);assert np.linalg.det(rot)>.999999
 assert size.shape==(3,) and np.isfinite(size).all() and min(size)>0
 conservative=np.maximum(size,np.nextafter(size.astype(np.float32),np.float32(np.inf)).astype(float))
 for name,value in [('target_rotation',R),('other_rotation',OR),('other_xyz',other_xyz),('other_size',size),('conservative_other_size',conservative),('center_local',capture_row['center_local_after']),('requested_z_m',req)]:near(ctx[name],value)
 center=np.asarray(capture_row['center_local_after']);near(c['active_support_reference']['center_local'],center);near(c['active_support_reference']['world_normal'],R[:,2],2e-6)
 observed=point(hand,q,side,R[:,2],center);near(observed,c['control_point_positions'][side],2e-6);near(observed,row['observed_support_xyz'],2e-6)
 dp=float(point(hand,parent,side,R[:,2],center)[2]-observed[2]);near(m['parent_exact_support_delta_z_m'],dp,2e-12)
 if dp<=req:return unchanged('original_already_meets_requested_nominal_downward_step',parent_checked=True)
 achieved=float(np.asarray(a['jacobian'])[5 if side=='right' else 2]@(parent-q))
 if expected_fraction<1 and achieved<=req:return unchanged('parent_linear_z_already_meets_original_request',parent_checked=True)
 modified=verified_task(a,m,expected_fraction)
 solver=m['solver'];x=np.asarray(solver['candidate_command'],float)
 assert x.shape==(11,) and np.isfinite(x).all();near(x,x.astype(np.float32));near(solver['parent_command'],parent)
 assert type(solver['solver_status']) is int and 0<=solver['solver_status']<=9 and type(solver['solver_success']) is bool
 assert solver['solver_success']==(solver['solver_status']==0) and type(solver['iterations']) is int and 0<solver['iterations']<=150
 ev=evaluate(modified,c,x,parent,hand,elbows,geometry,side)
 if not ev['passed']:
  assert m['nominal_verification']['passed'] is False
  return unchanged('nominal_certificate_or_table_rejected',independent_nominal_passed=False,parent_checked=True)
 assert m['nominal_verification']['passed'] is True
 dx=float(point(hand,x,side,R[:,2],center)[2]-observed[2]);near(m['candidate_exact_support_delta_z_m'],dx,2e-12)
 if dx>=0:return unchanged('exact_support_motion_not_downward',nominal_support_delta_z_m=dx,parent_checked=True)
 if abs(dx-req)>=abs(dp-req):return unchanged('exact_support_tracking_not_improved',nominal_support_delta_z_m=dx,parent_checked=True)
 paths={s:sweep(geometry,hand,q,x,s,np.asarray(other_xyz),OR,conservative) for s in ['left','right']}
 for s,p in paths.items():
  assert p['certified'] is m['nominal_hands_non_target_paths'][s]['certified']
  if p['certified']:near(p['minimum_certified_gap_lower_bound_m'],m['nominal_hands_non_target_paths'][s]['minimum_certified_gap_lower_bound_m'],2e-12)
 if not all(p['certified'] for p in paths.values()):return unchanged('nominal_non_target_path_rejected',parent_checked=True)
 # A valid candidate must be issued; do not silently accept an invented fallback.
 verify_guard(m['candidate_final_guard'],x,q,prev,a,elbows)
 raise AssertionError(('valid_candidate_not_applied',step))
