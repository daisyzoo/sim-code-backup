"""Unwired direct-route terminal lead floor; no threshold, force or object writes.
Use only the original per-step distance while still short of the release goal.
Independent guards, pressure, source binding and new physics remain required.
"""
import math,copy

def propose(parent,*,enabled,direction,target_y,tip_y,previous_y,step_m):
    if type(enabled) is not bool:raise ValueError('boolean enable required')
    if not enabled:return parent
    if direction not in (-1,1) or type(direction) is bool:raise ValueError('signed task direction required')
    if not all(math.isfinite(v) for v in (target_y,tip_y,previous_y,step_m)) or not 0<step_m<=.003:raise ValueError('original finite slew step required')
    if not parent.get('eligible') or parent['stage']!='lateral_y':return parent
    goal=parent['object_goal_xy'][1];assert math.isfinite(goal)
    remaining=direction*(goal-target_y)
    if not 0<remaining<step_m:return parent
    desired=tip_y+direction*step_m
    command=previous_y+max(-step_m,min(step_m,desired-previous_y))
    result=copy.deepcopy(parent);result['desired_support_xy'][1]=desired;result['command_xy'][1]=command
    result['terminal_directional_lead_floor']=dict(enabled=True,original_step_m=step_m,signed_remaining_y_m=remaining,original_desired_y=parent['desired_support_xy'][1],original_command_y=parent['command_xy'][1],goal_unchanged=True,quality_unchanged=True,physical_benefit_proven=False)
    return result
