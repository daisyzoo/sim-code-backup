"""Unwired rear-region wrapper; the frozen parent update and guards run first."""
from dataclasses import dataclass, field
from region_top_contact import TopContactBypassState
from simfoundry.data.top_contact_bypass import rotation_xyzw
from rear_cop_centering import RearCopCentering
from rear_coupled_progress import govern_rear_progress
from rear_early_edge_governor import govern_rear_joint_xy_early


@dataclass
class RearCopRouteState(TopContactBypassState):
    rear_early_edge_enabled: bool = False
    rear_slow_drag: bool = False
    rear_joint_xy_enabled: bool = False
    rear_coupled_progress_enabled: bool = False
    rear_core_slice_enabled: bool = False
    rear_cop_enabled: bool = False
    rear_cop_core_size: object = None
    rear_cop: RearCopCentering = field(default_factory=RearCopCentering)

    def update(self, palm, target, obstacle, target_radius_x, obstacle_radius_x, *,
               tip, quat, control_offset_local, load_n, slip_contact=None, **kwargs):
        if type(self.rear_early_edge_enabled) is not bool or (self.rear_early_edge_enabled and not self.rear_joint_xy_enabled):
            raise ValueError('Early edge requires original jointXY governor')
        if type(self.rear_slow_drag) is not bool or (self.rear_slow_drag and not self.rear_cop_enabled):
            raise ValueError('Rear slow drag requires enabled rear COP')
        if self.rear_cop_enabled and (not self.continuous_drag or self.drag_step_m != (.0015 if self.rear_slow_drag else .003)):
            raise ValueError('Rear COP requires declared 3mm or rear-only 1.5mm continuous drag')
        if type(self.rear_core_slice_enabled) is not bool:
            raise ValueError('rear_core_slice_enabled must be bool')
        if self.rear_core_slice_enabled and not self.rear_cop_enabled:
            raise ValueError('Core slice requires rear COP')
        self.rear_cop.core_slice_feedback = self.rear_core_slice_enabled
        if type(self.rear_coupled_progress_enabled) is not bool:
            raise ValueError('rear_coupled_progress_enabled must be bool')
        if self.rear_coupled_progress_enabled and not self.rear_core_slice_enabled:
            raise ValueError('Coupled progress requires rear core slice')
        if type(self.rear_joint_xy_enabled) is not bool:
            raise ValueError('rear_joint_xy_enabled must be bool')
        if self.rear_joint_xy_enabled and not self.rear_coupled_progress_enabled:
            raise ValueError('Joint XY requires parent coupled progress')
        previous_xy = self.last_waypoint_xy
        previous_z = self.command[2] if self.command is not None else tip[2]
        row = super().update(palm, target, obstacle, target_radius_x, obstacle_radius_x,
                             tip=tip, quat=quat, control_offset_local=control_offset_local,
                             load_n=load_n, **kwargs)
        if not self.rear_cop_enabled:
            return row
        if self.selected_surface_local_xy is None:
            self.rear_cop.reset()
            row['rear_cop_centering'] = dict(override=False, reason='region_not_handed_over')
            return row
        cop = None
        normal = 0.
        if slip_contact is not None and slip_contact.get('valid'):
            cop = slip_contact['weighted_contact_local']
            normal = slip_contact['normal_load_n']
        previous = (*previous_xy, previous_z) if previous_xy is not None else tip
        feedback = self.rear_cop.update(mode=row['mode'], parent_xyz=row['target_xyz'],
            previous_xyz=previous, reference_xyz=tip, object_xyz=target,
            object_rotation=rotation_xyzw(quat), core_size=self.rear_cop_core_size,
            cop_local=cop, normal_load_n=normal)
        if feedback['override']:
            self.command = tuple(feedback['command_xyz'])
            row['target_xyz'] = self.command
            self.last_waypoint_xy = self.command[:2]
        row['rear_cop_centering'] = feedback
        if self.rear_coupled_progress_enabled:
            progress = (govern_rear_progress(enabled=True, mode=row['mode'],
                previous_xyz=previous, parent_xyz=row['target_xyz'],
                object_rotation=rotation_xyzw(quat), core_size=self.rear_cop_core_size,
                cop_local=cop, normal_load_n=normal, direction=self.rear.plan['direction'])
                if feedback['override'] else dict(override=False, reason='original_rear_not_overridden'))
            if progress['override']:
                self.command = tuple(progress['command_xyz'])
                row['target_xyz'] = self.command
                self.last_waypoint_xy = self.command[:2]
            row['rear_coupled_progress'] = progress
        if self.rear_joint_xy_enabled:
            joint_xy = (govern_rear_joint_xy_early(early_enabled=self.rear_early_edge_enabled, side=self.side, enabled=True, mode=row['mode'],
                previous_xyz=previous, parent_xyz=feedback['command_xyz'],
                reference_xyz=tip, object_rotation=rotation_xyzw(quat),
                core_size=self.rear_cop_core_size, cop_local=cop,
                normal_load_n=normal, direction=self.rear.plan['direction'])
                if feedback['override'] else dict(override=False, reason='original_rear_not_overridden'))
            # Infeasible/invalid-load/guard cases retain the parent Y governor.
            # This candidate never replaces the original guard transition.
            if joint_xy['override']:
                self.command = tuple(joint_xy['command_xyz'])
                row['target_xyz'] = self.command
                self.last_waypoint_xy = self.command[:2]
            row['rear_joint_xy_progress'] = joint_xy
        return row
