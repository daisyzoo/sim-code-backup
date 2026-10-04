"""Isolated default-off wrapper, parent routing/guards/load/Z run first.
Changes selected right-hand front loaded XY only. Uses actual emitted previous
XY; preserves original route cross-axis control and edge speed advice.
"""
from dataclasses import dataclass,field
import numpy as np
from front_initial_center_cop_route import FrontCopRouteState
from simfoundry.data.top_contact_bypass import rotation_xyzw
from material_preload_v2 import MaterialPreload

@dataclass
class FrontBoxMaterialPreloadState(FrontCopRouteState):
    material_preload_enabled: bool=False
    material_preload: MaterialPreload=field(default_factory=MaterialPreload)

    def update(self,palm,target,obstacle,target_radius_x,obstacle_radius_x,*,tip,quat,
               obstacle_quat,control_offset_local,load_n,hand_obstacle_gap_m,
               slip_contact=None,**kwargs):
        if type(self.material_preload_enabled) is not bool:raise ValueError('Explicit preload dispatch required')
        previous=self.last_emitted_xy
        row=super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,
            tip=tip,quat=quat,obstacle_quat=obstacle_quat,control_offset_local=control_offset_local,
            load_n=load_n,hand_obstacle_gap_m=hand_obstacle_gap_m,slip_contact=slip_contact,**kwargs)
        if not self.material_preload_enabled:return row
        if not (self.cop_slip_enabled and self.reset_cop_on_route_change and self.route_axis_only and self.edge_speed_enabled):
            raise ValueError('Finite preload requires original phase/axis/edge protected COP route')
        cop=row.get('cop_slip_following',{})
        if self.side!='right' or row['mode']!='top_push' or not cop.get('override') or row.get('route_stop_reason') or row.get('release_reason') or row.get('terminal_position_confirmed'):
            self.material_preload.reset()
            row['front_box_material_preload']=dict(override=False,reason='parent_or_unselected')
            return row
        diagonal=bool(row.get('front_diagonal_entry',{}).get('selected'))
        gy=row['front_diagonal_entry']['goal_y'] if diagonal else (row.get('clearance_progress',{}).get('front_hold_y',self.rear.plan['initial_target_xyz'][1]) if row['route_stage']=='front_x' else self.route_report['goal_y'])
        valid=bool(slip_contact and slip_contact.get('valid') and cop.get('override'))
        event=self.material_preload.update(enabled=True,selected=bool(self.side=='right' and cop.get('override')),side=self.side,
            mode=row['mode'],route_stage=row['route_stage'],recontacts=self.recontacts,
            parent_guard=bool(row.get('route_stop_reason') or row.get('release_reason') or row.get('terminal_position_confirmed')),
            object_xyz=target,object_rotation=rotation_xyzw(quat),observed_support_xyz=tip,
            previous_command_xy=previous if previous is not None else tip[:2],goal_xy=[row['route_goal_x'],gy],
            normal_load_n=slip_contact['normal_load_n'] if valid else 0.,cop_valid=valid,
            drive_step_m=cop.get('edge_speed',{}).get('drive_step_m',self.cop_drive_step_m))
        if event['override']:
            parent_xyz=list(row['target_xyz']);xy=list(event['command_xy']);cross=None
            if self.route_axis_only and not diagonal:
                active=0 if row['route_stage']=='front_x' else 1;cross=1-active;xy[cross]=parent_xyz[cross]
            event.update(parent_xyz=parent_xyz,emitted_xy=xy,preserved_cross_axis=cross,preserved_z=parent_xyz[2])
            self.command=(*xy,parent_xyz[2]);row['target_xyz']=self.command;self.last_emitted_xy=tuple(xy)
        row['front_box_material_preload']=event
        return row
