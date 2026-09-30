"""Bounded object-relative waypoint, without forces or parcel pose writes.

The anchor is the measured reference-minus-object offset at contact acquisition.
It must stay fixed until that contact is lost, rather than integrating slip.
"""
import math


def object_relative_push_xy(target, anchor, goal, previous, *, lead_m=.012, step_m=.003):
    if any(len(v) != 2 for v in (target, anchor, goal, previous)):
        raise ValueError('Expected four XY pairs')
    if not all(math.isfinite(x) for v in (target, anchor, goal, previous) for x in v):
        raise ValueError('Nonfinite push geometry')
    if not (math.isfinite(lead_m) and 0 < lead_m <= .012 and math.isfinite(step_m) and .001 <= step_m <= .012):
        raise ValueError('Invalid bounded lead or slew')
    desired = tuple(target[i] + anchor[i] + max(-lead_m, min(lead_m, goal[i]-target[i])) for i in (0,1))
    command = tuple(previous[i]+max(-step_m,min(step_m,desired[i]-previous[i])) for i in (0,1))
    return command, desired
