"""Independent observed-object corridor record check, not whole-robot dynamics.
No runtime selector or corner-planner imports. Segment minima use linear programs
rather than the runtime's line-intersection enumeration. Original gates retained.
Caller must independently bind observations, previous route stage/latched state,
collector provenance and emitted commands; this interface alone is not admission.
"""
import numpy as np
from scipy.optimize import linprog
from scipy.spatial.transform import Rotation

def near(a,b,tol=1e-12):
 a=np.asarray(a,float);b=np.asarray(b,float)
 assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
 assert np.max(abs(a-b),initial=0)<=tol,'record value mismatch'

def verify(*,record,original_goal_x,route_stage,target,obstacle,size,other_size,quat,other_quat,direction,planning_margin,initial_other,hand_obstacle_gap_m,parent_guard_reason,prior_stop_reason,lateral_y_enabled=False):
 assert type(lateral_y_enabled) is bool
 r=record;target,obstacle,size,other_size,initial_other=[np.asarray(x,float) for x in [target,obstacle,size,other_size,initial_other]]
 assert all(x.shape==(3,) and np.isfinite(x).all() for x in [target,obstacle,size,other_size,initial_other]);assert min(*size,*other_size)>0
 assert direction in [-1,1] and route_stage in ['front_x','lateral_y'] and .012<=planning_margin<=.03
 assert np.isfinite([original_goal_x,planning_margin,hand_obstacle_gap_m]).all()
 for q in [quat,other_quat]:
  q=np.asarray(q,float);assert q.shape==(4,) and np.isfinite(q).all() and abs(q@q-1)<=2e-6
 tr=np.abs(Rotation.from_quat(quat).as_matrix())@size/2;other=np.abs(Rotation.from_quat(other_quat).as_matrix())@other_size/2
 lo=.285+tr[0];hi=obstacle[0]-other[0]-tr[0]-planning_margin
 table=min(target[0]-tr[0]-.28,.88-target[0]-tr[0],target[1]-tr[1]+.75,.75-target[1]-tr[1]);gap=max(obstacle[0]-target[0]-other[0]-tr[0],abs(obstacle[1]-target[1])-other[1]-tr[1])
 guard=bool(parent_guard_reason is not None or np.linalg.norm((obstacle-initial_other)[:2])>.01 or table<.005 or hand_obstacle_gap_m<.005 or gap<.01)
 assert r['enabled'] is True and r['training_ready'] is False and type(r['changed']) is bool
 assert r['route_stage']==route_stage and r['prior_stop_reason']==prior_stop_reason and r['other_guard_active'] is guard
 for key,value in [('original_goal_x',original_goal_x),('safe_interval_x',[lo,hi]),('target_radii_xy',tr[:2]),('other_radii_xy',other[:2]),('current_table_margin_m',table),('current_parcel_axis_gap_m',gap),('original_planning_margin_m',planning_margin),('original_table_margin_m',.005),('original_extra_x_reserve_m',.003)]:near(r[key],value)
 reason=None;eligible=None;proof=[];goal=original_goal_x
 if guard or prior_stop_reason is not None:reason='preserve_other_guard_or_latched_stop'
 elif route_stage!='front_x' and not lateral_y_enabled:reason='preserve_outside_front_x'
 elif lo<=original_goal_x<=hi:reason='preserve_valid_original'
 elif lo>=hi:reason='no_positive_width_original_margin_interval'
 else:
  candidate=(lo+hi)/2;goal_y=direction*max(.205,direction*target[1]+.16);near_y=obstacle[1]-direction*(tr[1]+other[1]+planning_margin+.003);corner_y=target[1]+direction*np.clip(direction*(near_y-target[1]),0,direction*(goal_y-target[1]))
  paths={'axis':[target[:2],[candidate,target[1]],[candidate,goal_y]],'diagonal':[target[:2],[candidate,corner_y],[candidate,goal_y]]};routes=r['candidate_routes']['routes'];assert [v['route'] for v in routes]==list(paths)
  for row in routes:
   points=np.asarray(paths[row['route']]);near(row['points'],points);segments=[]
   for aa,bb in zip(points,points[1:]):
    start=aa-obstacle[:2];delta=bb-aa;intercepts=np.r_[start-(tr+other)[:2],-start-(tr+other)[:2]];slopes=np.r_[delta,-delta]
    lp=linprog([0,1],A_ub=np.column_stack([slopes,-np.ones(4)]),b_ub=-intercepts,bounds=[(0,1),(None,None)],method='highs');assert lp.success
    segments.append(float(lp.fun))
   tm=float(min(min(x-tr[0]-.28,.88-x-tr[0],y-tr[1]+.75,.75-y-tr[1]) for x,y in points));length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
   near(row['minimum_axis_gap_m'],min(segments));near(row['minimum_table_margin_m'],tm);near(row['length_m'],length)
   assert len(row['segments'])==len(segments)
   for seg,value,aa,bb in zip(row['segments'],segments,points,points[1:]):
    near(seg['minimum_axis_gap_m'],value);t=seg['at_fraction'];assert 0<=t<=1;at=aa+t*(bb-aa);near(max(abs(at-obstacle[:2])-(tr+other)[:2]),value)
   ok=bool(tm>=.005-1e-10 and min(segments)>=planning_margin-1e-10);assert row['eligible'] is ok;proof.append(dict(route=row['route'],eligible=ok,minimum_axis_gap_m=min(segments),minimum_table_margin_m=tm))
  eligible=all(x['eligible'] for x in proof)
  if eligible:goal=candidate;reason='midpoint_preserves_original_margins_and_nominal_segments'
  else:reason='nominal_axis_or_diagonal_path_rejected'
 if eligible is None:assert 'candidate_routes' not in r
 assert r['changed'] is (eligible is True) and r['reason']==reason;near(r['goal_x'],goal)
 return dict(passed=True,changed=r['changed'],reason=reason,independent_segment_linear_programs=proof,observed_object_geometry_only=True)
