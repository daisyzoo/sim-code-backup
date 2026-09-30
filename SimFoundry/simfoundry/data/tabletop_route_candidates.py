"""Read-only front/rear object-envelope routes; not robot or force commands.

Uses fixed observed orientations to propose center paths. A controller must
recheck actual geometry during execution and separately validate hand/arm
clearance, reach, forces, target support and non-target displacement.
"""
import math
from simfoundry.data.top_contact_bypass import rotation_xyzw


def footprint_radii(size, quat):
    if len(size)!=3 or not all(math.isfinite(v) and v>0 for v in size):
        raise ValueError('Invalid parcel dimensions')
    r=rotation_xyzw(quat)
    return tuple(sum(abs(r[i][k])*size[k]/2 for k in range(3)) for i in (0,1))


def _segment_gap(a, b, obstacle, radii):
    # All segments are axis-aligned. For each axis, take the minimum possible
    # center separation anywhere on this segment, then subtract summed radii.
    # A positive maximum proves a separating axis for the entire segment.
    if abs(a[0]-b[0])>1e-12 and abs(a[1]-b[1])>1e-12:
        raise ValueError('Only axis-aligned center segments supported')
    gaps=[]
    for i in (0,1):
        low,high=sorted((a[i],b[i]));distance=max(low-obstacle[i],obstacle[i]-high,0.)
        gaps.append(distance-radii[i])
    return max(gaps)


def tabletop_route_candidates(target, obstacle, target_size, obstacle_size,
                               target_quat, obstacle_quat, direction, margin=.02):
    if (len(target)!=3 or len(obstacle)!=3 or direction not in (-1,1)
            or not all(math.isfinite(x) for x in [*target,*obstacle,margin]) or margin<0):
        raise ValueError('Invalid route geometry')
    tr=footprint_radii(target_size,target_quat);other=footprint_radii(obstacle_size,obstacle_quat)
    combined=tuple(a+b for a,b in zip(tr,other))
    goal_y=direction*max(.205,direction*target[1]+.16)
    route_x={'direct':target[0],
             'front':min(target[0],obstacle[0]-combined[0]-margin),
             'rear':max(target[0],obstacle[0]+combined[0]+margin)}
    rows=[]
    for name,x in route_x.items():
        points=[(target[0],target[1]),(x,target[1]),(x,goal_y)]
        gaps=[_segment_gap(a,b,obstacle,combined) for a,b in zip(points,points[1:])]
        table_margin=min(min(px-tr[0]-.28,.88-px-tr[0],py-tr[1]+.75,.75-py-tr[1]) for px,py in points)
        separation=min(gaps)
        reasons=[]
        if table_margin < -1e-10:reasons.append('target envelope crosses tabletop edge')
        if separation < margin-1e-10:reasons.append('target/other envelopes lack requested clearance')
        rows.append(dict(route=name,waypoints_xy=[list(v) for v in points],
            object_path_length_m=sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(points,points[1:])),
            target_table_margin_m=table_margin,min_object_axis_separation_m=separation,
            object_envelope_eligible=not reasons,reasons=reasons))
    return dict(candidates=rows,goal_y=goal_y,target_radii_xy=list(tr),other_radii_xy=list(other),
        scope='Fixed observed-orientation AABB swept center paths only; no selected robot route, hand/arm collision, IK, dynamics, visibility or task success guarantee. Preserve rejected alternatives and recheck live geometry.',training_ready=False)
