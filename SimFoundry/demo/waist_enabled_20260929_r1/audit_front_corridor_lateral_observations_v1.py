"""Independent continuous pre-action route/guard/midpoint observation binding.
Does not establish source provenance, joint action execution or physical success.
Caller supplies original full trajectory or an explicitly labelled prefix fixture.
"""
import math
import numpy as np
from audit_front_corridor_lateral_record_v1 import verify,near

def radii(size,quat):
 # Match original Python-float observation arithmetic; independent of runtime
 # imports. The separate record verifier also checks normalized SciPy geometry.
 x,y,z,w=[float(v) for v in quat];norm=math.sqrt(x*x+y*y+z*z+w*w);x,y,z,w=x/norm,y/norm,z/norm,w/norm
 R=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)))
 return tuple(sum(abs(R[i][j])*size[j]/2 for j in range(3)) for i in range(2))

def inspect(rows,plan,tr,ori,*,enabled,expected_steps,lateral_y_enabled=False):
 assert type(lateral_y_enabled) is bool and (not lateral_y_enabled or enabled)
 assert type(enabled) is bool and [r['step'] for r in rows]==list(expected_steps)
 selected=bool(plan.get('front_route_selected'));cfg=plan.get('front_corridor_midpoint')
 if enabled and selected:
  assert cfg['enabled'] is True and cfg['phase']==('front_x_and_lateral_y' if lateral_y_enabled else 'front_x_only') and cfg['preserve_latched_stop'] is True and cfg['preserve_other_guards'] is True
  assert cfg['table_margin_m']==.005 and cfg['original_extra_reserve_m']==.003 and cfg['extra_reserve_may_be_replanned'] is True and cfg['require_axis_and_diagonal_paths'] is True and cfg['training_ready'] is False
 else:assert cfg is None
 if not selected:
  assert all('front_corridor_midpoint' not in r for r in rows)
  return dict(passed=True,selected=False,rows=0,goals={},changed_steps=[])
 direction=plan['direction'];assert direction in [-1,1];key='box' if direction==-1 else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]};size=sizes[key];osize=sizes[other];g=plan['front_route_live_guards'];clear=g['clearance_before_lateral_m'];assert g['recover_clearance'] is True and g['nominal_clearance_confirmation_frames']==3 and g['recovery_resume_extra_m']==.0005
 if enabled:assert cfg['parcel_planning_margin_m']==clear
 first=rows[0]['step'];tx=tr[key][first];ox=tr[other][first];rad=radii(size,ori[key][first]);orr=radii(osize,ori[other][first]);fixed=min(tx[0],ox[0]-orr[0]-rad[0]-clear)-.003
 # The plan was recorded at layout setup, before the first control observation.
 # Recompute the controller's fixed route from its first actual observation;
 # every subsequent emitted goal is checked below. Do not equate these times.
 chosen=next(r for r in plan['front_route_candidates']['candidates'] if r['route']=='front')
 setup_goal_difference=float(chosen['waypoints_xy'][1][0]-.003-fixed)
 stage='front_x';stop=None;stop_tip=None;safe=0;hold=plan['initial_target_xyz'][1];recoveries=0;goals={};changed=[];guards=0
 for row in rows:
  t=row['step'];target=np.asarray(tr[key][t]);obs=np.asarray(tr[other][t]);r=radii(size,ori[key][t]);o=radii(osize,ori[other][t]);parent=None
  if math.hypot(obs[0]-plan['obstacle_initial_xyz'][0],obs[1]-plan['obstacle_initial_xyz'][1])>.01:parent='non_target_motion_10mm'
  elif min(target[0]-r[0]-.28,.88-target[0]-r[0],target[1]-r[1]+.75,.75-target[1]-r[1])<.005:parent='target_table_margin_5mm'
  elif row['hand_obstacle_gap_m']<.005:parent='hand_obstacle_gap_5mm'
  goal=min(fixed,obs[0]-o[0]-r[0]-clear-.003)
  if enabled:
   record=row['front_corridor_midpoint'];proof=verify(record=record,original_goal_x=goal,route_stage=stage,target=target,obstacle=obs,size=size,other_size=osize,quat=ori[key][t],other_quat=ori[other][t],direction=direction,planning_margin=clear,initial_other=plan['obstacle_initial_xyz'],hand_obstacle_gap_m=row['hand_obstacle_gap_m'],parent_guard_reason=parent,prior_stop_reason=stop,lateral_y_enabled=lateral_y_enabled)
   goal=record['goal_x']
   if proof['changed']:changed.append(t)
  else:assert 'front_corridor_midpoint' not in row
  reason=parent
  if goal-r[0]<.285:reason='front_corridor_no_table_margin'
  gap_x=obs[0]-target[0]-o[0]-r[0];gap_y=abs(obs[1]-target[1])-o[1]-r[1]
  if max(gap_x,gap_y)<.01:reason='parcel_clearance_10mm'
  if reason or stop:
   if stop is None:stop=reason;stop_tip=row['observed_support_xyz']
   assert row['mode']=='front_guard_lift' and row['route_stop_reason']==stop and row['route_stage']==stage
   near(row['target_xyz'],[*stop_tip[:2],max(.91,stop_tip[2])]);guards+=1;continue
  assert row['mode']!='front_guard_lift' and row['route_stop_reason'] is None
  entered=False;resume=None
  if stage=='front_x':
   safe=safe+1 if gap_x>=clear else 0
   if gap_x>=clear+.0005:stage='lateral_y';resume='reserve_met'
   elif safe>=3:stage='lateral_y';resume='nominal_clearance_confirmed_3'
  elif gap_x<clear-g['recovery_hysteresis_m']:
   stage='front_x';hold=float(target[1]);recoveries+=1;entered=True;safe=0
  progress=row['clearance_progress'];assert row['route_stage']==stage and progress['route_stage']==stage
  assert progress['clearance_recovery_count']==recoveries and progress['clearance_recovery_entered'] is entered and progress['safe_clearance_observations']==safe and progress['clearance_resume_reason']==resume
  near(progress['front_hold_y'],hold);near(row['route_goal_x'],goal);near(row['measured_front_gap_m'],gap_x);goals[t]=float(goal)
 return dict(passed=True,selected=True,rows=len(rows),guard_rows=guards,changed_steps=changed,goals=goals,setup_vs_first_control_goal_m=setup_goal_difference)
