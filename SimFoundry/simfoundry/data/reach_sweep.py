"""Opt-in diagnostic reach-feasible sweep geometry; not obstacle certification."""
import math


def retreating_sweep_x(initial_x, target_y, direction, exit_y, retreat_m):
    """Bend the late outward sweep toward the torso, leaving approach unchanged.

    The far-depth diagnostic has a .60m contact X but loses low-palm reach near
    the lateral endpoint. This smooth path retreats at most ``retreat_m`` once
    the commanded hand reaches |Y|=.08m on its goal side. The X floor .50m is
    only a diagnostic waypoint constraint, not a general clearance guarantee.
    """
    if not all(math.isfinite(v) for v in (initial_x,target_y,direction,exit_y,retreat_m)):
        raise ValueError('Nonfinite sweep geometry')
    if direction not in (-1,1) or exit_y <= .08 or not 0 <= retreat_m <= .10:
        raise ValueError('Invalid diagnostic sweep geometry')
    amount=min(retreat_m,max(0.,initial_x-.50))
    phase=min(1.,max(0.,(direction*target_y-.08)/(exit_y-.08)))
    smooth=phase*phase*(3.-2.*phase)
    return initial_x-amount*smooth


def ready_to_release(initial_y, observed_y, direction):
    """Leave 5mm zone and 1cm progress margin over the unchanged numeric gate."""
    if direction not in (-1,1) or not all(math.isfinite(v) for v in (initial_y,observed_y)):
        raise ValueError('Invalid object feedback for goal release')
    return direction*observed_y >= max(.205,direction*initial_y+.16)


def sweep_exit_y(target_x, base_exit_y, far_exit_y=0.):
    if not all(math.isfinite(v) for v in (target_x,base_exit_y,far_exit_y)):
        raise ValueError('Nonfinite exit configuration')
    if far_exit_y and not .30 <= far_exit_y <= .34:
        raise ValueError('Far endpoint outside diagnostic range')
    return far_exit_y if target_x >= .48 and far_exit_y else base_exit_y
