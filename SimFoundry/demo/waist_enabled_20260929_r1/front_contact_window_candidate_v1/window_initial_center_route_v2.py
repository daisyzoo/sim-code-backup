"""Diagnostic front-route robot controller; never moves parcels directly.

The existing support/load controller handles approach and contact recovery.
Only the loaded translation changes: measured X clearance first, then Y.
Live envelope and hand guards latch a lift/hold on unsafe observations.
"""
from dataclasses import dataclass, field
from micro_clearance_return import MicroClearanceReturn
from front_corridor_midpoint_runtime import select as select_corridor_midpoint
import math
from window_initial_center_top_v2 import TopContactBypassState
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates, footprint_radii


def select_front_route(target, obstacle, size, other_size, quat, other_quat, direction, margin=.02):
    report = tabletop_route_candidates(target, obstacle, size, other_size, quat, other_quat, direction, margin=margin)
    eligible = [r for r in report['candidates'] if r['object_envelope_eligible']]
    best = min(eligible, key=lambda r: r['object_path_length_m']) if eligible else None
    return (best if best and best['route'] == 'front' else None), report


@dataclass
class FrontTopRouteState(TopContactBypassState):
    recontact_on_route_change: bool = False
    diagonal_entry: bool = False
    retain_micro_repair_contact: bool = False
    corridor_midpoint_replan: bool = False
    corridor_lateral_replan: bool = False
    micro_return: object = field(default_factory=MicroClearanceReturn)
    obstacle_size: tuple = (.15, .145, .04)
    route_clearance_m: float = .02
    route_stage: str = 'front_x'
    recover_clearance: bool = False
    confirm_nominal_clearance: bool = False
    recovery_hysteresis_m: float = 0.
    object_relative_lead: bool = False
    relative_contact_anchor: tuple | None = None
    clearance_progress: object | None = None
    route_x: float | None = None
    stop_reason: str | None = None
    stop_tip: tuple | None = None
    route_report: dict | None = None

    def _stop(self, tip, reason):
        if self.stop_reason is None:
            self.stop_reason, self.stop_tip = reason, tuple(tip)
        self.load.bias_m = 0.
        self.mode = 'front_guard_lift'
        self.mode_step += 1
        return dict(target_xyz=(*self.stop_tip[:2], max(.91, self.stop_tip[2])),
                    mode=self.mode, control_offset_local=None,
                    route_stage=self.route_stage, route_stop_reason=self.stop_reason)

    def update(self, palm, target, obstacle, target_radius_x, obstacle_radius_x, *,
               tip, quat, obstacle_quat, control_offset_local, load_n,
               hand_obstacle_gap_m, repair_contact=None, repair_core_size=None, **kwargs):
        if type(self.corridor_lateral_replan) is not bool:
            raise ValueError('corridor_lateral_replan must be bool')
        if self.corridor_lateral_replan and not self.corridor_midpoint_replan:
            raise ValueError('Lateral corridor requires original midpoint guards')
        if type(self.corridor_midpoint_replan) is not bool:
            raise ValueError('corridor_midpoint_replan must be bool')
        if type(self.retain_micro_repair_contact) is not bool:
            raise ValueError('retain_micro_repair_contact must be bool')
        if self.retain_micro_repair_contact and not (self.recontact_on_route_change and self.diagonal_entry):
            raise ValueError('Micro repair retention requires diagonal route and direction recontact')
        if type(self.diagonal_entry) is not bool:
            raise ValueError('diagonal_entry must be bool')
        if type(self.recontact_on_route_change) is not bool:
            raise ValueError('recontact_on_route_change must be bool')
        if self.recovery_hysteresis_m and not self.recover_clearance:
            raise ValueError('Hysteresis requires explicit front clearance recovery')
        if not math.isfinite(hand_obstacle_gap_m):
            raise ValueError('Front route requires measured hand/other gap')
        if not math.isfinite(self.route_clearance_m) or not .012 <= self.route_clearance_m <= .03:
            raise ValueError('Front planning clearance must be12..30mm')
        direction = self.rear.plan['direction']
        tr = footprint_radii(self.size, quat)
        other = footprint_radii(self.obstacle_size, obstacle_quat)
        if self.route_report is None:
            chosen, self.route_report = select_front_route(target, obstacle, self.size,
                self.obstacle_size, quat, obstacle_quat, direction, margin=self.route_clearance_m)
            if chosen is None:
                raise ValueError('Front route is not the shortest eligible object-envelope path')
            self.route_x = chosen['waypoints_xy'][1][0] - .003
            self.top_mode, self.start = 'top_lift', tuple(tip)
        reason = None
        initial_other = self.rear.plan['obstacle_initial_xyz']
        if math.hypot(obstacle[0]-initial_other[0], obstacle[1]-initial_other[1]) > .01:
            reason = 'non_target_motion_10mm'
        elif min(target[0]-tr[0]-.28, .88-target[0]-tr[0], target[1]-tr[1]+.75, .75-target[1]-tr[1]) < .005:
            reason = 'target_table_margin_5mm'
        elif hand_obstacle_gap_m < .005:
            reason = 'hand_obstacle_gap_5mm'
        # Recompute the required front clearance under measured rotations.
        required_x = obstacle[0]-other[0]-tr[0]-self.route_clearance_m
        goal_x = min(self.route_x, required_x-.003)
        corridor_record = None
        if self.corridor_midpoint_replan:
            goal_x, corridor_record = select_corridor_midpoint(
                original_goal_x=goal_x, route_stage=self.route_stage,
                target=target, obstacle=obstacle, size=self.size, other_size=self.obstacle_size,
                quat=quat, other_quat=obstacle_quat, direction=direction,
                planning_margin=self.route_clearance_m, initial_other=initial_other,
                hand_obstacle_gap_m=hand_obstacle_gap_m,
                parent_guard_reason=reason, prior_stop_reason=self.stop_reason,
                lateral_y_enabled=self.corridor_lateral_replan)
        if goal_x-tr[0] < .285:
            reason = 'front_corridor_no_table_margin'
        gap_x = obstacle[0]-target[0]-other[0]-tr[0]
        gap_y = abs(obstacle[1]-target[1])-other[1]-tr[1]
        if max(gap_x, gap_y) < .01:
            reason = 'parcel_clearance_10mm'
        if reason or self.stop_reason:
            row = self._stop(tip, reason)
            if corridor_record is not None:
                row['front_corridor_midpoint'] = corridor_record
            # The lift keeps the same actual supporting point as other top modes.
            row['control_offset_local'] = tuple(control_offset_local)
            return dict(row, observed_target=list(target), observed_support_xyz=list(tip),
                        hand_obstacle_gap_m=hand_obstacle_gap_m)
        previous_route_stage = self.route_stage
        previous_top_mode = self.top_mode
        progress = None
        if self.recover_clearance:
            from simfoundry.data.front_clearance_progress import FrontClearanceProgress
            if self.clearance_progress is None:
                self.clearance_progress=FrontClearanceProgress(self.route_clearance_m,self.rear.plan['initial_target_xyz'][1],confirm_nominal_clearance=self.confirm_nominal_clearance,recovery_hysteresis_m=self.recovery_hysteresis_m)
            progress=self.clearance_progress.update(gap_x,target[1])
            self.route_stage=progress['route_stage']
        elif self.route_stage == 'front_x' and gap_x >= self.route_clearance_m:
            self.route_stage = 'lateral_y'
        elif not self.recover_clearance and self.route_stage == 'lateral_y' and gap_x < self.route_clearance_m-.003:
            self.route_stage = 'front_x'
        transition_record = None
        if self.recontact_on_route_change:
            from simfoundry.data.top_contact_bypass import ready_to_release, rotation_xyzw
            tilt = math.acos(max(-1.,min(1.,rotation_xyzw(quat)[2][2])))
            stage_changed = previous_route_stage != self.route_stage
            terminal_ready = bool(ready_to_release(self.rear.plan['initial_target_xyz'][1],target[1],direction))
            tilt_guard = bool(self.tilt_recontact_rad and tilt>self.tilt_recontact_rad)
            restart = bool(stage_changed and previous_top_mode=='top_push' and load_n>=.3 and not terminal_ready and not tilt_guard)
            micro_record = None
            if self.retain_micro_repair_contact:
                micro_record = self.micro_return.update(previous_stage=previous_route_stage,current_stage=self.route_stage,target_xy=target[:2],contact=repair_contact,core_size=repair_core_size,restart_expected=restart,terminal=terminal_ready,tilted=tilt_guard)
                if micro_record['retained']:restart=False
            if restart:
                self._start_recontact(tip,'front_route_direction_change')
                self.relative_contact_anchor = None
            transition_record = dict(previous_stage=previous_route_stage,current_stage=self.route_stage,previous_top_mode=previous_top_mode,measured_vertical_load_n=float(load_n),stage_changed=stage_changed,restarted=restart,terminal_precedence=terminal_ready,tilt_precedence=tilt_guard)
            if micro_record is not None:transition_record['micro_repair_retention']=micro_record
        previous_command = self.command
        row = super().update(palm, target, obstacle, target_radius_x, obstacle_radius_x,
            tip=tip, quat=quat, control_offset_local=control_offset_local, load_n=load_n,
            hand_obstacle_gap_m=hand_obstacle_gap_m, **kwargs)
        if row['mode'] != 'top_push':
            self.relative_contact_anchor = None
        if row['mode'] == 'top_push':
            hold_y=progress['front_hold_y'] if progress is not None else self.rear.plan['initial_target_xyz'][1]
            goal_y = (hold_y if self.route_stage == 'front_x'
                      else self.route_report['goal_y'])
            if self.diagonal_entry and self.route_stage == 'front_x' and load_n>=.3:
                from front_diagonal_entry_geometry_probe import propose
                proposal=propose(target,obstacle,self.size,self.obstacle_size,quat,obstacle_quat,direction,margin=self.route_clearance_m,front_x=goal_x)
                route=proposal['routes'][1]
                selected=route['eligible']
                row['front_diagonal_entry']=dict(selected=selected,reason='current_observed_envelope_segment_clear' if selected else 'original_axis_fallback',proposal=route)
                if selected:
                    goal_y=route['points'][1][1]
                    row['front_diagonal_entry']['goal_y']=goal_y
            # Limited lead from the measured support, limited frame-to-frame
            # command increments. Restore the pre-parent XY command so no hidden
            # lateral push is issued before front clearance is physically measured.
            base = previous_command if previous_command is not None else tuple(tip)
            desired_xy = [tip[i]+max(-.012, min(.012, goal-target[i]))
                          for i, goal in enumerate((goal_x, goal_y))]
            xy = [base[i]+max(-self.drag_step_m, min(self.drag_step_m, desired_xy[i]-base[i]))
                  for i in (0, 1)]
            if self.object_relative_lead:
                from simfoundry.data.object_relative_push import object_relative_push_xy
                if self.relative_contact_anchor is None:
                    self.relative_contact_anchor = tuple(tip[i]-target[i] for i in (0,1))
                xy, desired_xy = object_relative_push_xy(target[:2], self.relative_contact_anchor,
                    (goal_x, goal_y), base[:2], step_m=self.drag_step_m)
                row['object_relative_contact_anchor_xy_m'] = self.relative_contact_anchor
                row['object_relative_desired_xy_m'] = desired_xy
                row['object_relative_lead_limit_m'] = .012
            self.command = (*xy, row['target_xyz'][2])
            row['target_xyz'] = self.command
        if transition_record is not None:
            row["direction_change_recontact"] = transition_record
        if corridor_record is not None:
            row['front_corridor_midpoint'] = corridor_record
        return dict(row, clearance_progress=progress, route_stage=self.route_stage, route_goal_x=goal_x,
                    measured_front_gap_m=gap_x, route_stop_reason=None)
