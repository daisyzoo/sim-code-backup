"""Independent raw-pose front interval goal and original guard reconstruction.
Uses scipy rotations and numeric trace data, never candidate/controller imports.
Source admission, full COP commands, robot execution and quality stay separate.
"""
import numpy as np
from scipy.spatial.transform import Rotation

def verify_interval_rows(rows,plan,tr,ori,key,*,enabled):
 assert type(enabled) is bool and plan.get('front_route_selected') is True
 other='mailer' if key=='box' else 'box';sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
 assert key in sizes and rows
 radius={k:abs(Rotation.from_quat(ori[k]).as_matrix())@size/2 for k,size in sizes.items()};clear=plan['front_route_live_guards']['clearance_before_lateral_m'];assert clear==.012
 expected_config=dict(enabled=True,table_margin_m=.005,parcel_planning_clearance_m=clear,original_extra_reserve_m=.003,proposal='midpoint_only_when_original_infeasible',original_live_guards=True,latched_stop_preserved=True,training_ready=False)
 if enabled:assert plan.get('front_corridor_interval')==expected_config
 else:assert 'front_corridor_interval' not in plan
 front=next(x for x in plan['front_route_candidates']['candidates'] if x['route']=='front');fixed_x=front['waypoints_xy'][1][0]-.003
 last_stop=None;result=[];goals={};indices=[x['step'] for x in rows];assert indices==list(range(1,len(rows)+1))
 def near(actual,want):
  a,b=np.asarray(actual,float),np.asarray(want,float);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=2e-6
 for row in rows:
  t=row['step'];obj=np.asarray(tr[key][t],float);obstacle=np.asarray(tr[other][t],float);rad=radius[key][t];orr=radius[other][t]
  low=.285+rad[0];high=obstacle[0]-orr[0]-rad[0]-clear;original=min(fixed_x,high-.003);goal=original
  table=min(obj[0]-rad[0]-.28,.88-obj[0]-rad[0],obj[1]-rad[1]+.75,.75-obj[1]-rad[1]);gap_x=obstacle[0]-obj[0]-orr[0]-rad[0];gap_y=abs(obstacle[1]-obj[1])-orr[1]-rad[1]
  reason=None
  if np.linalg.norm(obstacle[:2]-np.asarray(plan['obstacle_initial_xyz'])[:2])>.01:reason='non_target_motion_10mm'
  elif table<.005:reason='target_table_margin_5mm'
  elif row['hand_obstacle_gap_m']<.005:reason='hand_obstacle_gap_5mm'
  protected=bool(reason or last_stop or max(gap_x,gap_y)<.01);changed=bool(enabled and not protected and not low<=original<=high and low<high)
  if changed:goal=(low+high)/2
  record=row.get('front_corridor_interval');assert (record is not None)==enabled
  if enabled:
   assert set(record)=={'enabled','original_goal_x','safe_interval_x','protected','changed','goal_x','table_margin_m','parcel_planning_clearance_m'}
   assert record['enabled'] is True and type(record['protected']) is bool and type(record['changed']) is bool
   assert record['protected']==protected and record['changed']==changed
   near(record['original_goal_x'],original);near(record['safe_interval_x'],[low,high]);near(record['goal_x'],goal)
   assert record['table_margin_m']==.005 and record['parcel_planning_clearance_m']==clear
   if changed:assert low<goal<high
  if goal-rad[0]<.285:reason='front_corridor_no_table_margin'
  if max(gap_x,gap_y)<.01:reason='parcel_clearance_10mm'
  expected_stop=last_stop or reason
  assert bool(expected_stop)==(row['mode']=='front_guard_lift'),(t,'guard bypass or unexpected stop')
  assert row.get('route_stop_reason')==expected_stop,(t,'stop reason/latch differs')
  if expected_stop:last_stop=expected_stop
  else:near(row['route_goal_x'],goal)
  goals[t]=float(goal);result.append(dict(step=t,changed=changed,protected=protected,goal_x=float(goal),original_goal_x=float(original),safe_interval_x=[float(low),float(high)],stop_reason=expected_stop))
 return dict(passed=True,frames=len(rows),changed_rows=sum(x['changed'] for x in result),goals=goals,records=result,training_ready=False)
