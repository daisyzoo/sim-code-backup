"""Unwired measured-object goal for an already calibrated contact reference.
Limits desired XY lead. Bounded slew can lag that bound if the object jumps.
No force/pose writes or changes to original guards.
"""
from dataclasses import dataclass
import math
@dataclass
class BoundedTopLead:
    lead_m: float=.024
    previous: tuple|None=None
    def update(self,mode,object_xy,goal_xy,reference_xy,*,step_m=.003):
        if not math.isfinite(self.lead_m) or not .012<=self.lead_m<=.030:raise ValueError('Lead outside diagnostic range')
        if not math.isfinite(step_m) or not .001<=step_m<=.012:raise ValueError('Invalid command slew')
        for value in (object_xy,goal_xy,reference_xy):
            if len(value)!=2 or not all(math.isfinite(v) for v in value):raise ValueError('Invalid XY geometry')
        if mode!='top_push':
            self.previous=None
            return None
        desired=tuple(object_xy[i]+max(-self.lead_m,min(self.lead_m,goal_xy[i]-object_xy[i])) for i in (0,1))
        before=self.previous if self.previous is not None else tuple(reference_xy)
        command=tuple(before[i]+max(-step_m,min(step_m,desired[i]-before[i])) for i in (0,1))
        self.previous=command
        return dict(command_xy=command,desired_xy=desired,previous_xy=before,lead_m=self.lead_m,step_m=step_m,
                    command_relative_object_xy_m=tuple(command[i]-object_xy[i] for i in (0,1)),
                    slew_limited=any(abs(desired[i]-before[i])>step_m for i in (0,1)))
def route_goal(state,row):
    """Read existing route goals only, after original update and guards."""
    if row['mode']!='top_push':return None
    if 'route_stage' in row:
        hold=row.get('clearance_progress')
        y=(hold['front_hold_y'] if hold is not None else state.rear.plan['initial_target_xyz'][1]) if row['route_stage']=='front_x' else state.route_report['goal_y']
        return (row['route_goal_x'],y)
    return (row['target_xyz'][0],state.rear.plan['direction']*.34)
