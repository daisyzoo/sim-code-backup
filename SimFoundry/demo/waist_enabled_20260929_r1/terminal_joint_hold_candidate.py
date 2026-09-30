"""Unwired terminal hold proposal. Never accepts failure holds or moves objects."""
from dataclasses import dataclass
import math
@dataclass
class TerminalJointHold:
    consecutive: int=0
    command: tuple|None=None
    def observe(self,*,mode,target_confirmed,hand_clearance_m,load_n,active_error_m,inactive_error_m,other_max_xy_m,current_upper_q,previous_upper_command):
        values=[hand_clearance_m,load_n,active_error_m,inactive_error_m,other_max_xy_m,*current_upper_q,*previous_upper_command]
        if len(current_upper_q)!=11 or len(previous_upper_command)!=11 or not all(math.isfinite(float(x)) for x in values):raise ValueError('Finite measured terminal observations required')
        tracking_command=self.command if self.command is not None else previous_upper_command
        valid=(mode in {'goal_release','top_release','bypass_release'} and target_confirmed
               and hand_clearance_m>=.02 and abs(load_n)<.2 and active_error_m<=.012
               and inactive_error_m<=.015 and 0<=other_max_xy_m<=.015
               and max(abs(a-b) for a,b in zip(current_upper_q,tracking_command))<=.015)
        if self.command is not None:
            if valid:return self.command
            self.command=None;self.consecutive=0
            return None
        self.consecutive=self.consecutive+1 if valid else 0
        if self.consecutive>=5:self.command=tuple(float(x) for x in previous_upper_command)
        return self.command
