"""Default-off initial direct-top feedback adapter. No force or object writes.
The original parent still owns guards, pressure, transitions, release and Z.
This changes only final lateral feedback when short by less than one old step.
"""
from dataclasses import dataclass
from simfoundry.data.initial_top_route import InitialTopRouteState, ClearanceFeedback
from terminal_directional_lead_candidate import propose as terminal_propose

@dataclass
class DirectionalLeadFeedback(ClearanceFeedback):
    task_direction: int = 1

    def propose(self,target,obstacle,size,other_size,quat,other_quat,tip,previous_command,goal_y,step_m=.003):
        parent=super().propose(target,obstacle,size,other_size,quat,other_quat,tip,previous_command,goal_y,step_m)
        return terminal_propose(parent,enabled=True,direction=self.task_direction,target_y=target[1],tip_y=tip[1],previous_y=previous_command[1],step_m=step_m)

@dataclass
class TerminalLeadInitialTopState(InitialTopRouteState):
    terminal_directional_lead_enabled: bool = False

    def update(self,*args,**kwargs):
        if type(self.terminal_directional_lead_enabled) is not bool:
            raise ValueError('Explicit boolean terminal lead configuration required')
        if self.terminal_directional_lead_enabled:
            if self.clearance_feedback is None:
                self.clearance_feedback=DirectionalLeadFeedback(self.rear.plan['initial_target_xyz'][0],self.rear.plan['obstacle_initial_xyz'][0],task_direction=self.rear.plan['direction'])
            elif type(self.clearance_feedback) is not DirectionalLeadFeedback:
                raise ValueError('Do not replace live feedback history or switch controller midway')
        return super().update(*args,**kwargs)
