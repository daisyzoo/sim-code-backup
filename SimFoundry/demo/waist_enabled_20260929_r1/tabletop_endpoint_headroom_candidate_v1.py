"""Uninstalled object-route candidate: add planning headroom, never lower release gates.
Fixed-orientation object envelopes only. Robot reach, arms, contact and full task
success remain unproved; reject rather than reuse parent geometry for a longer path.
"""
import math
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates as parent_routes
from simfoundry.data.tabletop_route_candidates import _segment_gap

def candidate_routes(target,obstacle,target_size,obstacle_size,target_quat,obstacle_quat,direction,margin=.02,*,endpoint_headroom_m=0.):
    if isinstance(endpoint_headroom_m,bool) or not math.isfinite(endpoint_headroom_m) or not 0<=endpoint_headroom_m<=.02:
        raise ValueError('Explicit finite planning headroom in [0,.02] required')
    parent=parent_routes(target,obstacle,target_size,obstacle_size,target_quat,obstacle_quat,direction,margin)
    if endpoint_headroom_m==0:return parent
    goal_y=parent['goal_y']+direction*endpoint_headroom_m
    tr=parent['target_radii_xy'];other=parent['other_radii_xy'];combined=tuple(a+b for a,b in zip(tr,other));rows=[]
    for old in parent['candidates']:
        points=[list(p) for p in old['waypoints_xy']];points[-1][1]=goal_y
        separation=min(_segment_gap(a,b,obstacle,combined) for a,b in zip(points,points[1:]))
        table_margin=min(min(px-tr[0]-.28,.88-px-tr[0],py-tr[1]+.75,.75-py-tr[1]) for px,py in points)
        reasons=[]
        if table_margin < -1e-10:reasons.append('target envelope crosses tabletop edge')
        if separation < margin-1e-10:reasons.append('target/other envelopes lack requested clearance')
        rows.append(dict(route=old['route'],waypoints_xy=points,object_path_length_m=sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(points,points[1:])),target_table_margin_m=table_margin,min_object_axis_separation_m=separation,object_envelope_eligible=not reasons,reasons=reasons))
    return dict(parent,candidates=rows,goal_y=goal_y,planning_endpoint_headroom=dict(version='object_endpoint_headroom_candidate_v1',headroom_m=endpoint_headroom_m,original_release_boundary_y=parent['goal_y'],original_release_thresholds_unchanged=True,original_geometry_thresholds_unchanged=True,full_extended_envelope_recomputed=True,robot_feasibility_verified=False,installed=False),training_ready=False)
