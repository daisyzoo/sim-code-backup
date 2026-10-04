"""Current-observation front corridor proposal, never a dynamics certificate.
Opt-in lateral_y coverage extension. Geometry proposal only.
Keep table5mm, parcel-planning12mm or stricter configured margin, all other
live guards and latched stops. Adapt only extra3mm X planning reserve when its
original goal is infeasible. No object/force/joint mutation; caller retains
original Cartesian/COP/slew/IK/final guards and independently audits execution.
"""
import math
import numpy as np
from simfoundry.data.tabletop_route_candidates import footprint_radii
from front_diagonal_entry_geometry_probe import propose as corner_routes

def select(*, original_goal_x, route_stage, target, obstacle, size, other_size,
           quat, other_quat, direction, planning_margin, initial_other,
           hand_obstacle_gap_m, parent_guard_reason, prior_stop_reason,
           lateral_y_enabled=False):
    if type(lateral_y_enabled) is not bool:raise ValueError("lateral_y_enabled must be bool")
    def vector(value,length,name):
        a=np.asarray(value,dtype=float)
        if a.shape!=(length,) or not np.isfinite(a).all():raise ValueError('Invalid '+name)
        return a.tolist()
    target=vector(target,3,'target');obstacle=vector(obstacle,3,'obstacle');size=vector(size,3,'size');other_size=vector(other_size,3,'other_size');initial_other=vector(initial_other,3,'initial_other');quat=vector(quat,4,'quat');other_quat=vector(other_quat,4,'other_quat')
    if min(*size,*other_size)<=0 or direction not in (-1,1) or route_stage not in ('front_x','lateral_y'):raise ValueError('Invalid route dimensions or stage')
    if not all(math.isfinite(x) for x in [original_goal_x,planning_margin,hand_obstacle_gap_m]) or not .012<=planning_margin<=.03:raise ValueError('Invalid original margins')
    for rotation in [quat,other_quat]:
        if abs(sum(x*x for x in rotation)-1)>2e-6:raise ValueError('Invalid observed unit quaternion')
    tr=footprint_radii(size,quat);other=footprint_radii(other_size,other_quat)
    lower=.285+tr[0];upper=obstacle[0]-other[0]-tr[0]-planning_margin
    gap_x=obstacle[0]-target[0]-other[0]-tr[0];gap_y=abs(obstacle[1]-target[1])-other[1]-tr[1]
    table=min(target[0]-tr[0]-.28,.88-target[0]-tr[0],target[1]-tr[1]+.75,.75-target[1]-tr[1])
    other_guards=bool(parent_guard_reason is not None or math.hypot(obstacle[0]-initial_other[0],obstacle[1]-initial_other[1])>.01 or table<.005 or hand_obstacle_gap_m<.005 or max(gap_x,gap_y)<.01)
    record=dict(enabled=True,changed=False,original_goal_x=float(original_goal_x),goal_x=float(original_goal_x),route_stage=route_stage,safe_interval_x=[lower,upper],target_radii_xy=list(tr),other_radii_xy=list(other),current_table_margin_m=table,current_parcel_axis_gap_m=max(gap_x,gap_y),other_guard_active=other_guards,prior_stop_reason=prior_stop_reason,original_planning_margin_m=planning_margin,original_table_margin_m=.005,original_extra_x_reserve_m=.003,training_ready=False)
    def unchanged(reason):return original_goal_x,dict(record,reason=reason)
    if other_guards or prior_stop_reason is not None:return unchanged('preserve_other_guard_or_latched_stop')
    if route_stage!='front_x' and not lateral_y_enabled:return unchanged('preserve_outside_front_x')
    if lower<=original_goal_x<=upper:return unchanged('preserve_valid_original')
    if lower>=upper:return unchanged('no_positive_width_original_margin_interval')
    goal=(lower+upper)/2
    # Original observed-orientation segment proof; retain its full rows so an
    # independent auditor can recompute rather than trust the eligible boolean.
    routes=corner_routes(target,obstacle,size,other_size,quat,other_quat,direction,
                         margin=planning_margin,front_x=goal)
    record['candidate_routes']=routes
    if not all(route['eligible'] for route in routes['routes']):return unchanged('nominal_axis_or_diagonal_path_rejected')
    return goal,dict(record,changed=True,goal_x=goal,reason='midpoint_preserves_original_margins_and_nominal_segments')
