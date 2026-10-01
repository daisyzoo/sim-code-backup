"""Candidate direct far route: measured support lift/top contact, live guards.

Robot waypoints only; no object pose/force intervention. Geometric eligibility
is not a dynamics/reach/visibility guarantee; complete physical trials required.
"""
from dataclasses import dataclass
import math
from simfoundry.data.top_contact_bypass import TopContactBypassState
from simfoundry.data.initial_top_route_candidate import initial_top_route_candidate
from simfoundry.data.tabletop_route_candidates import footprint_radii

@dataclass
class ClearanceFeedback:
    initial_target_x: float
    initial_obstacle_x: float
    hold_y: float | None = None
    stage: str = 'lateral_y'

    def propose(self, target, obstacle, size, other_size, quat, other_quat,
                tip, previous_command, goal_y, step_m=.003):
        values=[*target,*obstacle,*tip,*previous_command,goal_y,step_m,
                self.initial_target_x,self.initial_obstacle_x]
        if not all(math.isfinite(float(x)) for x in values) or not 0<step_m<=.003:
            raise ValueError('Invalid clearance feedback geometry')
        tr=footprint_radii(size,quat);other=footprint_radii(other_size,other_quat)
        away=-1 if self.initial_target_x<self.initial_obstacle_x else 1
        axis_gaps=[abs(target[i]-obstacle[i])-tr[i]-other[i] for i in (0,1)]
        # Existing outer state owns the 10mm stop. Proposal never overrides it.
        if max(axis_gaps)<.01:
            return dict(eligible=False,reason='preserve_original_parcel_clearance_10mm',axis_gaps_m=axis_gaps)
        # Keep original X unless current rotated footprints need extra space.
        # Require X separation only when the remaining Y segment can approach
        # the other footprint. A separated path moving away preserves reset X.
        low_y,high_y=sorted((target[1],goal_y))
        center_distance_y=max(low_y-obstacle[1],obstacle[1]-high_y,0.)
        remaining_y_gap=center_distance_y-tr[1]-other[1]
        needs_x_corridor=bool(remaining_y_gap<.024)
        boundary=obstacle[0]+away*(tr[0]+other[0]+.024)
        separated_x=min(self.initial_target_x,boundary) if away<0 else max(self.initial_target_x,boundary)
        goal_x=separated_x if needs_x_corridor else self.initial_target_x
        margin=min(goal_x-tr[0]-.28,.88-goal_x-tr[0])
        if margin<.005:
            return dict(eligible=False,reason='planned_corridor_no_table_margin_5mm',axis_gaps_m=axis_gaps)
        # Only stop lateral advance when Y envelopes still overlap. Hysteresis
        # avoids alternating directions around the recovery boundary.
        xgap=away*(target[0]-obstacle[0])-tr[0]-other[0]
        if axis_gaps[1]<.022 and xgap<.018 and self.stage!='clearance_x':
            self.stage='clearance_x';self.hold_y=float(target[1])
        elif self.stage=='clearance_x' and (xgap>=.021 or axis_gaps[1]>=.022):
            self.stage='lateral_y';self.hold_y=None
        ygoal=self.hold_y if self.stage=='clearance_x' else goal_y
        desired=[tip[i]+max(-.012,min(.012,goal-target[i])) for i,goal in enumerate((goal_x,ygoal))]
        command=[previous_command[i]+max(-step_m,min(step_m,desired[i]-previous_command[i])) for i in (0,1)]
        return dict(eligible=True,axis_gaps_m=axis_gaps,stage=self.stage,
                    object_goal_xy=[goal_x,ygoal],desired_support_xy=desired,
                    remaining_y_gap_m=remaining_y_gap,needs_x_corridor=needs_x_corridor,
                    command_xy=command,planned_table_margin_m=margin,
                    scope='Waypoint geometry only. Actual contact, tracking, yaw, clearance and quality unproven.')


@dataclass
class InitialTopRouteState(TopContactBypassState):
    # Initial approach remains .91; only subsequent recoveries use this height.
    recontact_travel_z: float=.86
    obstacle_size: tuple=(.15,.145,.04)
    proposal: dict|None=None
    stop_reason: str|None=None
    stop_tip: tuple|None=None
    clearance_feedback: ClearanceFeedback|None=None

    def update(self,palm,target,obstacle,target_radius_x,obstacle_radius_x,*,tip,quat,
               obstacle_quat,control_offset_local,load_n,hand_obstacle_gap_m,**kwargs):
        if not self.guarded_descent or not self.continuous_drag:
            raise ValueError('Initial top requires guarded continuous drag')
        if not math.isfinite(hand_obstacle_gap_m):
            raise ValueError('Initial top requires measured finite hand/other gap')
        if self.proposal is None:
            if self.rear.plan['required']:
                raise ValueError('Initial direct top cannot replace a blocked-object route')
            self.proposal=initial_top_route_candidate(target,obstacle,self.size,
                self.obstacle_size,quat,obstacle_quat,self.rear.plan['direction'])
            if not self.proposal['proposed']:
                raise ValueError('Initial top not eligible for measured geometry')
            self.top_mode,self.start='top_lift',tuple(tip)
        tr=footprint_radii(self.size,quat);other=footprint_radii(self.obstacle_size,obstacle_quat)
        initial_other=self.rear.plan['obstacle_initial_xyz'];reason=None
        if math.hypot(obstacle[0]-initial_other[0],obstacle[1]-initial_other[1])>.01:
            reason='non_target_motion_10mm'
        elif min(target[0]-tr[0]-.28,.88-target[0]-tr[0],target[1]-tr[1]+.75,.75-target[1]-tr[1])<.005:
            reason='target_table_margin_5mm'
        elif hand_obstacle_gap_m<.005:
            reason='hand_obstacle_gap_5mm'
        elif max(abs(target[0]-obstacle[0])-tr[0]-other[0],abs(target[1]-obstacle[1])-tr[1]-other[1])<.01:
            reason='parcel_clearance_10mm'
        if reason or self.stop_reason:
            if self.stop_reason is None:self.stop_reason,self.stop_tip=reason,tuple(tip)
            self.load.bias_m=0.;self.mode='initial_top_guard_lift';self.mode_step+=1
            return dict(target_xyz=(*self.stop_tip[:2],max(.91,self.stop_tip[2])),mode=self.mode,
                control_offset_local=tuple(control_offset_local),route_stop_reason=self.stop_reason,
                initial_top_selected=True,observed_target=list(target),observed_support_xyz=list(tip),
                hand_obstacle_gap_m=hand_obstacle_gap_m)
        previous_command=self.command
        row=super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,tip=tip,
            quat=quat,control_offset_local=control_offset_local,load_n=load_n,
            hand_obstacle_gap_m=hand_obstacle_gap_m,**kwargs)
        feedback=None
        if row['mode']=='top_push':
            if self.clearance_feedback is None:
                self.clearance_feedback=ClearanceFeedback(
                    self.rear.plan['initial_target_xyz'][0],
                    self.rear.plan['obstacle_initial_xyz'][0])
            feedback=self.clearance_feedback.propose(target,obstacle,self.size,
                self.obstacle_size,quat,obstacle_quat,tip,
                previous_command if previous_command is not None else tip,
                self.proposal['goal_y'],step_m=min(.003,self.drag_step_m))
            if not feedback['eligible']:
                self.stop_reason,self.stop_tip=feedback['reason'],tuple(tip)
                self.load.bias_m=0.;self.mode='initial_top_guard_lift'
                return dict(target_xyz=(*tip[:2],max(.91,tip[2])),mode=self.mode,
                    control_offset_local=tuple(control_offset_local),
                    route_stop_reason=self.stop_reason,initial_top_selected=True,
                    observed_target=list(target),observed_support_xyz=list(tip),
                    hand_obstacle_gap_m=hand_obstacle_gap_m,clearance_feedback=feedback)
            self.command=(*feedback['command_xy'],row['target_xyz'][2])
            row['target_xyz']=self.command
        return dict(row,initial_top_selected=True,route_stop_reason=None,
                    clearance_feedback=feedback)
