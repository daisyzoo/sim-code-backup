"""Isolated front-only loaded COP feedback; parent guard and force control first."""
from dataclasses import dataclass, field
import numpy as np
from window_initial_center_route_v2 import FrontTopRouteState
from simfoundry.data.top_contact_bypass import rotation_xyzw
from contact_slip_following import CopSlipFollowing
from front_edge_speed_direction import edge_speed

@dataclass
class FrontCopRouteState(FrontTopRouteState):
    cop_slip_enabled: bool = False
    cop_slip: CopSlipFollowing = field(default_factory=CopSlipFollowing)
    last_emitted_xy: tuple | None = None
    reset_cop_on_route_change: bool = False
    last_route_stage: str | None = None
    route_axis_only: bool = False
    cop_drive_step_m: float = .001
    edge_speed_enabled: bool = False
    edge_core_size: object = None

    def update(self, palm, target, obstacle, target_radius_x, obstacle_radius_x, *,
               tip, quat, obstacle_quat, control_offset_local, load_n,
               hand_obstacle_gap_m, slip_contact=None, **kwargs):
        if self.cop_slip_enabled and (self.object_relative_lead or not self.continuous_drag or self.drag_step_m != .003):
            raise ValueError('COP feedback requires original3mm continuous drag without competing lead')
        if type(self.cop_drive_step_m) not in (int,float) or not np.isfinite(self.cop_drive_step_m) or not .001<=self.cop_drive_step_m<=.003:
            raise ValueError('Front drive increment must be finite1..3mm')
        if type(self.edge_speed_enabled) is not bool:
            raise ValueError('edge_speed_enabled must be bool')
        if self.edge_speed_enabled and not (self.cop_slip_enabled and self.reset_cop_on_route_change and self.route_axis_only):
            raise ValueError('Edge speed requires phase-reset route-axis COP')
        previous_xy=self.last_emitted_xy
        row=super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,
            tip=tip,quat=quat,obstacle_quat=obstacle_quat,control_offset_local=control_offset_local,
            load_n=load_n,hand_obstacle_gap_m=hand_obstacle_gap_m,repair_contact=slip_contact,repair_core_size=self.edge_core_size,**kwargs)
        stage_changed = self.last_route_stage is not None and self.last_route_stage != row['route_stage']
        phase_reset = self.cop_slip_enabled and self.reset_cop_on_route_change and stage_changed
        if phase_reset:
            self.cop_slip.reset()
        edge_direction=None
        if row.get('front_diagonal_entry',{}).get('selected'):
            candidate_direction=np.array([row['route_goal_x'],row['front_diagonal_entry']['goal_y']])-np.asarray(target[:2])
            if np.linalg.norm(candidate_direction)>1e-12:edge_direction=candidate_direction.tolist()
        edge_advice=edge_speed(enabled=self.edge_speed_enabled,mode=row['mode'],nominal_step_m=self.cop_drive_step_m,
            normal_load_n=slip_contact.get('normal_load_n',0.) if slip_contact and slip_contact.get('valid') else 0.,
            cop_local=slip_contact.get('weighted_contact_local') if slip_contact and slip_contact.get('valid') else None,
            object_rotation=rotation_xyzw(quat),core_size=self.edge_core_size,
            axis=0 if row['route_stage']=='front_x' else 1,
            sign=-1 if row['route_stage']=='front_x' else self.rear.plan['direction'],world_direction_xy=edge_direction)
        if self.cop_slip_enabled:
            if row['mode']!='top_push':
                self.cop_slip.reset()
                feedback=dict(override=False,reason='original_non_push_mode')
            else:
                rot=np.asarray(rotation_xyzw(quat));cop=None;normal=0.
                if slip_contact is not None and slip_contact.get('valid'):
                    cop=np.asarray(target)+rot@np.asarray(slip_contact['weighted_contact_local'])
                    normal=slip_contact['normal_load_n']
                progress=row.get('clearance_progress')
                hold_y=progress['front_hold_y'] if progress is not None else self.rear.plan['initial_target_xyz'][1]
                goal_y=hold_y if row['route_stage']=='front_x' else self.route_report['goal_y']
                diagonal=bool(row.get('front_diagonal_entry',{}).get('selected'))
                if diagonal:goal_y=row['front_diagonal_entry']['goal_y']
                feedback=self.cop_slip.update(mode=row['mode'],object_xyz=target,object_rotation=rot,
                    object_size=self.size,goal_xy=(row['route_goal_x'],goal_y),reference_xy=tip[:2],
                    previous_command_xy=previous_xy if previous_xy is not None else tip[:2],
                    cop_world=cop,normal_load_n=normal,drive_step_m=edge_advice['drive_step_m'])
                if feedback['override']:
                    if self.route_axis_only and not diagonal:
                        active_axis = 0 if row['route_stage'] == 'front_x' else 1
                        parent_xy = list(row['target_xyz'][:2])
                        mixed_xy = list(feedback['command_xy'])
                        cross_axis = 1-active_axis
                        actual_previous = previous_xy if previous_xy is not None else tip[:2]
                        mixed_xy[cross_axis] = actual_previous[cross_axis] + float(np.clip(parent_xy[cross_axis]-actual_previous[cross_axis], -.003, .003))
                        feedback['route_axis_control'] = dict(active_axis=active_axis, parent_xy=parent_xy, original_cop_xy=list(feedback['command_xy']), emitted_xy=mixed_xy)
                        self.command=(*mixed_xy,row['target_xyz'][2])
                    else:
                        self.command=(*feedback['command_xy'],row['target_xyz'][2])
                    if diagonal:
                        feedback['diagonal_entry_control']=dict(goal_xy=[row['route_goal_x'],goal_y],both_xy_from_cop=True,original_step_and_reference_bounds=True)
                    row['target_xyz']=self.command
            if self.reset_cop_on_route_change:
                feedback['route_anchor_reset'] = bool(phase_reset)
                feedback['previous_route_stage'] = self.last_route_stage
            if self.edge_speed_enabled:
                feedback['edge_speed']=edge_advice
            row['cop_slip_following']=feedback
        self.last_route_stage = row['route_stage']
        self.last_emitted_xy=tuple(row['target_xyz'][:2])
        return row
