"""Independent row binding for an applied declared fractional-Z refinement.
Output is checked against the command supplied by the caller (actual raw action
in an episode, explicitly unissued proposal in replay tests). This function does
not establish that a proposal was physically issued. Full source/trajectory,
Jacobian/normal, selection lifecycle and fallback audits remain mandatory.
"""
import numpy as np
from audit_front_loaded_z_priority_parent import verify_parent,near
from front_loaded_z_priority_audit_geometry import evaluate,point,sweep
from audit_front_loaded_z_fraction_task_v1 import verified_task


def verify_guard(record,command,q,previous,a,elbows):
 gaps=elbows.gap(command)
 checks=dict(joint_bounds=bool(np.all(command>=np.asarray(a['lower'])-2e-7) and np.all(command<=np.asarray(a['upper'])+2e-7)),measured_step=bool(np.all(abs(command-q)<=np.asarray(a['step_limits'])+2e-7)),previous_slew=bool(np.max(abs(command-previous))<=.0550002),nominal_margin=bool(min(gaps)>=.005-2e-7),first_zero=True)
 assert record['checks']==checks and all(checks.values()) and record['accepted'] is True and record['first'] is False
 for name,value in [('command',command),('current',q),('previous',previous)]:near(record[name],value)
 near(record['gaps_m'],gaps,2e-10)


def verify_applied(*,metadata,coordinate,row,expert,current,previous_actual,output,side,elbows,bounded_solver,hand,geometry,capture_row,previous_packet,target_xyz,target_rotation,other_xyz,other_rotation,other_size,expected_fraction):
 m=metadata;c=coordinate;ctx=m['context'];t=c['step'];q=np.asarray(current,float);prev=np.asarray(previous_actual,float);x=np.asarray(output,float)
 assert m['step']==ctx['step']==capture_row['step']==t and t>0
 assert m['applied'] is True and m['selected'] is ctx['selected'] is True and m['training_ready'] is False
 assert m['reason']==('verified_nominal_downward_tracking_improvement' if expected_fraction==1 else 'verified_reduced_z_task_nominal_improvement')
 assert capture_row['center_local_after'] is not None and ctx['side']==side and ctx['mode']==row['mode']=='top_push'
 if 'front_loaded_z_priority' in c:assert c['front_loaded_z_priority']==m
 assert x.shape==(11,) and np.isfinite(x).all();near(x,x.astype(np.float32));near(m['output_command'],x)
 near(ctx['current'],q);near(ctx['previous'],prev)
 parent=np.asarray(ctx['parent_command'],float)
 original=verify_parent(coordinate=c,row=row,expert=expert,current=q,previous_actual=prev,parent=parent,side=side,elbows=elbows,bounded_solver=bounded_solver)
 assert not row.get('hand_guard_saturated')
 # This is the last solved packet of the preceding action, not its integral.
 assert previous_packet['after_action_step']==t-1
 key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer'
 near(previous_packet['post_action_pose'][key],target_xyz,2e-6)
 load=0.
 for contact in previous_packet['parcel_contacts']:
  if any(side+'_wrist_roll' in s for s in contact['shapes']) and any('/'+actor+'/' in s for s in contact['shapes']):
   force=np.asarray(contact['force_world_N'],float);assert force.shape==(3,) and np.isfinite(force).all();load+=abs(float(force[2]))
 near(ctx['observed_vertical_load_n'],load,1e-10);near(row['contact_load']['observed_vertical_load_n'],load,1e-10);assert load>=.3
 R=np.asarray(target_rotation,float);OR=np.asarray(other_rotation,float);size=np.asarray(other_size,float)
 for rot in [R,OR]:
  assert rot.shape==(3,3) and np.isfinite(rot).all();near(rot.T@rot,np.eye(3),1e-6);assert np.linalg.det(rot)>.999999
 assert size.shape==(3,) and np.isfinite(size).all() and min(size)>0
 conservative=np.maximum(size,np.nextafter(size.astype(np.float32),np.float32(np.inf)).astype(float))
 for name,value in [('target_rotation',R),('other_rotation',OR),('other_xyz',other_xyz),('other_size',size),('conservative_other_size',conservative),('center_local',capture_row['center_local_after'])]:near(ctx[name],value)
 a=c['task_inputs'];center=np.asarray(capture_row['center_local_after']);near(c['active_support_reference']['center_local'],center);near(c['active_support_reference']['world_normal'],R[:,2],2e-6)
 observed=point(hand,q,side,R[:,2],center);near(observed,c['control_point_positions'][side],2e-6);near(observed,row['observed_support_xyz'],2e-6)
 req=float(a['error'][5 if side=='right' else 2]);near(ctx['requested_z_m'],req);assert req<0
 verify_guard(m['parent_final_guard'],parent,q,prev,a,elbows)
 solver=m['solver'];near(solver['parent_command'],parent);near(solver['candidate_command'],x)
 assert type(solver['solver_status']) is int and 0<=solver['solver_status']<=9 and type(solver['solver_success']) is bool
 assert solver['solver_success']==(solver['solver_status']==0) and type(solver['iterations']) is int and 0<solver['iterations']<=150
 modified=verified_task(a,m,expected_fraction)
 proof=evaluate(modified,c,x,parent,hand,elbows,geometry,side);assert proof['passed'] and m['nominal_verification']['passed'] is True
 dp=float(point(hand,parent,side,R[:,2],center)[2]-observed[2]);dx=float(point(hand,x,side,R[:,2],center)[2]-observed[2])
 near(m['parent_exact_support_delta_z_m'],dp,2e-12);near(m['candidate_exact_support_delta_z_m'],dx,2e-12)
 assert dp>req and dx<0 and abs(dx-req)<abs(dp-req)
 paths={s:sweep(geometry,hand,q,x,s,np.asarray(other_xyz),OR,conservative) for s in ['left','right']}
 for s,p in paths.items():
  assert p['certified'] and m['nominal_hands_non_target_paths'][s]['certified'] is True
  near(p['minimum_certified_gap_lower_bound_m'],m['nominal_hands_non_target_paths'][s]['minimum_certified_gap_lower_bound_m'],2e-12)
 verify_guard(m['candidate_final_guard'],x,q,prev,a,elbows)
 return dict(passed=True,step=t,parent_max_action_error_rad=original['parent_reconstruction']['max_action_error_rad'],original_task_override=original['original_task_override'],stationarity_residual=proof['certificate']['stationarity_residual'],last_solved_vertical_load_n=load,nominal_support_delta_z_m=dx,minimum_nominal_path_gap_m=min(p['minimum_certified_gap_lower_bound_m'] for p in paths.values()),solver_success=solver['solver_success'])
