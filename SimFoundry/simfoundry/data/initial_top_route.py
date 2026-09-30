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
class InitialTopRouteState(TopContactBypassState):
    obstacle_size: tuple=(.15,.145,.04)
    proposal: dict|None=None
    stop_reason: str|None=None
    stop_tip: tuple|None=None

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
        row=super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,tip=tip,
            quat=quat,control_offset_local=control_offset_local,load_n=load_n,
            hand_obstacle_gap_m=hand_obstacle_gap_m,**kwargs)
        return dict(row,initial_top_selected=True,route_stop_reason=None)
