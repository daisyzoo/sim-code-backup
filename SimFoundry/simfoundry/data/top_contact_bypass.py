"""Quarantined contact from above using actual convex-hand supporting vertices.

Emits bounded robot waypoints only. No object forces or pose changes. Selection
of a supporting vertex prevents confusing a single distal tip with the lowest
hand point; it does not certify the full arm or dynamic collision clearance.
"""
from dataclasses import dataclass,field
from functools import lru_cache
from pathlib import Path
import json,hashlib,math
from simfoundry.data.contact_load_control import ContactLoadControl
from simfoundry.data.cross_axis_admittance import CrossAxisAdmittance
from simfoundry.data.reach_sweep import ready_to_release


def rotation_xyzw(quat):
    if len(quat)!=4 or not all(math.isfinite(v) for v in quat):raise ValueError('Invalid quaternion')
    norm=math.sqrt(sum(v*v for v in quat))
    if norm<1e-8:raise ValueError('Zero quaternion')
    x,y,z,w=(v/norm for v in quat)
    return ((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))


@lru_cache(maxsize=1)
def support_mesh():
    root=Path(__file__).resolve().parents[2]
    data=json.loads((root/'assets/robots/g1_hand_support_vertices.json').read_text())
    if hashlib.sha256((root/data['source_path']).read_bytes()).hexdigest()!=data['source_sha256']:raise ValueError('Support vertices do not match collision asset')
    return {k:tuple(tuple(v) for v in vals) for k,vals in data['vertices'].items()}


def support_vertex(side,hand_quat_xyzw,parcel_quat_xyzw):
    rh=rotation_xyzw(hand_quat_xyzw);rp=rotation_xyzw(parcel_quat_xyzw)
    normal_local=tuple(sum(rh[i][k]*rp[i][2] for i in range(3)) for k in range(3))
    return min(support_mesh()[side],key=lambda v:sum(a*b for a,b in zip(v,normal_local)))


def top_surface_point(xyz,quat,size,inset=.02,front_inset_fraction=None):
    if len(xyz)!=3 or len(size)!=3 or min(size)<=0 or not all(math.isfinite(v) for v in [*xyz,*size]):raise ValueError('Invalid top contact geometry')
    rot=rotation_xyzw(quat);axis=max((0,1),key=lambda i:abs(rot[0][i]));local=[0.,0.,size[2]/2]
    if front_inset_fraction is not None:
        if not math.isfinite(front_inset_fraction) or not 0<front_inset_fraction<=1:raise ValueError('Invalid top inset fraction')
        inset=front_inset_fraction*size[axis]/2
    if not math.isfinite(inset) or not 0<inset<=size[axis]/2:raise ValueError('Inset outside selected top half-face')
    local[axis]=(-1 if rot[0][axis]>=0 else 1)*(size[axis]/2-inset)
    return tuple(xyz[i]+sum(rot[i][k]*local[k] for k in range(3)) for i in range(3))


def top_corner_local(quat,size,inset=.01):
    if len(size)!=3 or not all(math.isfinite(v) for v in size) or not math.isfinite(inset) or inset<=0 or min(size[:2])<=2*inset or size[2]<=0:raise ValueError('Invalid top corner geometry')
    rot=rotation_xyzw(quat)
    return tuple([(-1 if rot[0][i]>=0 else 1)*(size[i]/2-inset) for i in (0,1)]+[size[2]/2])


def local_surface_world(xyz,quat,local):
    rot=rotation_xyzw(quat)
    return tuple(xyz[i]+sum(rot[i][k]*local[k] for k in range(3)) for i in range(3))


@dataclass
class TopContactBypassState:
    rear: object
    side: str
    size: tuple
    mode: str='rear_lift'
    mode_step: int=0
    top_mode: str|None=None
    start: tuple|None=None
    release: tuple|None=None
    command: tuple|None=None
    settled: int=0
    guarded_descent: bool=False
    alignment_tolerance_m: float=.008
    continuous_drag: bool=False
    drag_step_m: float=.003
    front_inset_fraction: float|None=None
    corner_contact: bool=False
    forward_margin_m: float=0.
    edge_guard_m: float=0.
    recovery_clearance_m: float=0.
    recontact_travel_z: float=.91
    tilt_recontact_rad: float=0.
    confirm_terminal_release: bool=False
    position_release_monitor: object|None=None
    release_reason: str|None=None
    last_recontact_reason: str|None=None
    hold_push_x: bool=False
    hold_established_x: bool=False
    cross_axis_admittance: bool=False
    hand_obstacle_guard_m: float=0.
    contact_rear_shift_m: float=0.
    cross_axis_control: CrossAxisAdmittance=field(default_factory=CrossAxisAdmittance)
    push_x_anchor: float|None=None
    approach_compensation: bool=False
    approach_xy_bias: list=field(default_factory=lambda:[0.,0.])
    corner_local: tuple|None=None
    lost_contact_steps: int=0
    recontacts: int=0
    descent_z: float|None=None
    load: ContactLoadControl=field(default_factory=lambda:ContactLoadControl(3.,min_bias_m=-.006))

    def _start_recontact(self,tip,reason):
        self.top_mode='top_lift';self.mode_step=0;self.start=tuple(tip);self.command=None;self.descent_z=None;self.settled=0;self.lost_contact_steps=0;self.load.bias_m=0.;self.recontacts+=1;self.corner_local=None;self.approach_xy_bias=[0.,0.];self.last_recontact_reason=reason;self.push_x_anchor=self.push_x_anchor if self.hold_established_x else None;self.cross_axis_control.reset()

    def update(self,palm,target,obstacle,target_radius_x,obstacle_radius_x,*,tip,quat,control_offset_local,load_n,loaded_contact=None,hand_obstacle_gap_m=None):
        if not math.isfinite(self.hand_obstacle_guard_m) or not 0<=self.hand_obstacle_guard_m<=.01 or (self.hand_obstacle_guard_m and (not self.corner_contact or not self.forward_margin_m)):
            raise ValueError('Hand obstacle guard requires real forward-margin corner route and0..10mm bound')
        if self.hand_obstacle_guard_m and (hand_obstacle_gap_m is None or not math.isfinite(hand_obstacle_gap_m)):
            raise ValueError('Hand obstacle guard requires measured finite separation')
        if self.hold_established_x and (not self.continuous_drag or self.hold_push_x or self.cross_axis_admittance):raise ValueError('Established X hold requires continuous drag without legacy X/admittance modes')
        if self.cross_axis_admittance and not self.hold_push_x:raise ValueError('Cross-axis admittance requires push X anchor')
        if self.hold_push_x and not self.edge_guard_m:raise ValueError('Push X hold requires guarded top contact')
        if not math.isfinite(self.edge_guard_m) or not 0<=self.edge_guard_m<self.forward_margin_m and self.edge_guard_m!=0:raise ValueError('Edge guard must be nonnegative and less than planned forward margin')
        if not math.isfinite(self.recovery_clearance_m) or (self.recovery_clearance_m and (not .04<=self.recovery_clearance_m<=.08 or not self.edge_guard_m)):raise ValueError('Short recovery requires edge guard and40..80mm clearance')
        if not math.isfinite(self.recontact_travel_z) or not .84<=self.recontact_travel_z<=.91:
            raise ValueError('Recontact travel height must be0.84..0.91m')
        if self.recontact_travel_z!=.91 and (not self.guarded_descent or not self.continuous_drag or self.recovery_clearance_m):
            raise ValueError('Short recontact requires guarded continuous drag without another recovery height mode')
        if not math.isfinite(self.forward_margin_m) or self.forward_margin_m<0 or (self.forward_margin_m and not self.corner_contact):raise ValueError('Forward margin requires corner route and finite nonnegative value')
        if not math.isfinite(self.drag_step_m) or not .001<=self.drag_step_m<=.012:raise ValueError('Invalid top drag step')
        if len(tip)!=3 or len(control_offset_local)!=3 or not all(math.isfinite(v) for v in [*tip,*control_offset_local]):raise ValueError('Invalid measured support point')
        if not math.isfinite(self.tilt_recontact_rad) or not 0<=self.tilt_recontact_rad<=.10:
            raise ValueError('Tilt recovery threshold must be0..0.10rad')
        if self.tilt_recontact_rad and not (self.guarded_descent and self.continuous_drag):
            raise ValueError('Tilt recovery requires guarded continuous top route')
        if self.confirm_terminal_release and not (self.guarded_descent and self.continuous_drag):
            raise ValueError('Confirmed release requires guarded continuous top route')
        if self.top_mode is None:
            row=self.rear.update(palm,target,obstacle,target_radius_x,obstacle_radius_x,target_quat=quat)
            if row['mode']!='bypass_sweep':
                self.mode,self.mode_step=self.rear.mode,self.rear.mode_step
                return dict(row,control_offset_local=None,observed_support_xyz=list(tip))
            self.top_mode='top_lift';self.mode_step=0;self.start=tuple(tip)
        surface=top_surface_point(target,quat,self.size,front_inset_fraction=self.front_inset_fraction)
        if self.corner_contact:
            if self.corner_local is None:
                if self.forward_margin_m:
                    from simfoundry.data.top_push_contact_geometry import top_front_contact_local
                    self.corner_local=top_front_contact_local(quat,self.size,self.rear.plan['direction'],self.forward_margin_m)
                    if self.contact_rear_shift_m:
                        from simfoundry.data.top_push_contact_geometry import shift_top_contact_rearward
                        self.corner_local=shift_top_contact_rearward(self.corner_local,quat,self.size,self.rear.plan['direction'],self.forward_margin_m,self.contact_rear_shift_m)
                else:self.corner_local=top_corner_local(quat,self.size)
            surface=local_surface_world(target,quat,self.corner_local)
        if not math.isfinite(self.alignment_tolerance_m) or not .003<=self.alignment_tolerance_m<=.012:
            raise ValueError('Top alignment tolerance must be3..12mm')
        tolerance=.003 if self.approach_compensation else self.alignment_tolerance_m
        if self.approach_compensation and self.top_mode in ('top_cross','top_descend') and load_n<.2 and tip[2]>surface[2]+.015:
            for i in (0,1):
                increment=max(-.0005,min(.0005,.15*(surface[i]-tip[i])))
                self.approach_xy_bias[i]=max(-.01,min(.01,self.approach_xy_bias[i]+increment))
        control_xy=tuple(surface[i]+self.approach_xy_bias[i] for i in (0,1))
        direction=self.rear.plan['direction']
        position_ready=False
        if self.confirm_terminal_release:
            from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
            if self.position_release_monitor is None:
                self.position_release_monitor=ConfirmedPositionRelease(self.rear.plan['initial_target_xyz'][1],direction)
            position_ready=self.position_release_monitor.observe(target)
        guarded_this_step=False
        force=self.load.update(load_n,self.top_mode in ('top_press','top_push'))
        rotation=rotation_xyzw(quat);tilt=math.acos(max(-1.,min(1.,rotation[2][2])))
        if self.hand_obstacle_guard_m and self.top_mode in ('top_descend','top_press','top_push') and hand_obstacle_gap_m<self.hand_obstacle_guard_m and not (self.top_mode=='top_push' and ready_to_release(self.rear.plan['initial_target_xyz'][1],target[1],direction)):
            guarded_this_step=True
            self.contact_rear_shift_m=min(.03,self.contact_rear_shift_m+.01)
            self._start_recontact(tip,'hand_obstacle_clearance')
        if self.edge_guard_m and self.top_mode in ('top_press','top_push') and not (self.top_mode=='top_push' and ready_to_release(self.rear.plan['initial_target_xyz'][1],target[1],direction)):
            edge_close=loaded_contact is not None and loaded_contact.get('valid',False) and loaded_contact['normal_load_n']>.3 and loaded_contact['weighted_forward_edge_distance_m']<self.edge_guard_m
            if edge_close or tilt>.03:
                guarded_this_step=True
                self._start_recontact(tip,'loaded_edge_margin' if edge_close else 'incipient_tilt')
        if self.tilt_recontact_rad and self.top_mode in ('top_press','top_push') and tilt>self.tilt_recontact_rad:
            guarded_this_step=True
            self._start_recontact(tip,'incipient_tilt_independent')
        if position_ready and not guarded_this_step and self.top_mode in ('top_lift','top_cross','top_descend','top_press','top_push'):
            self.top_mode='top_release';self.mode_step=0;self.release=tuple(tip)
            self.release_reason='confirmed_original_target_position'
        travel_z=self.recontact_travel_z if self.recontacts else .91
        if self.recovery_clearance_m and self.recontacts:
            target_upper=target[2]+sum(abs(rotation[2][i])*self.size[i]/2 for i in range(3))
            travel_z=max(target_upper,obstacle[2]+.03)+self.recovery_clearance_m
        lift_threshold=travel_z-(.015 if self.recovery_clearance_m and self.recontacts else .02)
        if self.top_mode=='top_lift' and tip[2]>=lift_threshold:self.top_mode='top_cross';self.mode_step=0
        elif self.top_mode=='top_cross' and max(abs(tip[i]-surface[i]) for i in (0,1))<tolerance and tip[2]>=lift_threshold:
            self.top_mode='top_descend' if self.guarded_descent else 'top_press';self.mode_step=0;self.descent_z=tip[2];self.settled=0
        elif self.top_mode=='top_descend':
            close=max(abs(tip[i]-surface[i]) for i in (0,1))<tolerance and abs(tip[2]-surface[2])<.008
            self.settled=self.settled+1 if close else 0
            if self.settled>=3:self.top_mode='top_press';self.mode_step=0;self.settled=0
        elif self.top_mode=='top_press':
            established=force['filtered_vertical_load_n']>.3 and max(abs(tip[i]-surface[i]) for i in (0,1))<(.003 if self.approach_compensation else .015) and abs(tip[2]-surface[2])<.015
            self.settled=self.settled+1 if established else 0
            if self.guarded_descent and max(abs(tip[i]-surface[i]) for i in (0,1))>(.003 if self.approach_compensation else .015):
                self.top_mode='top_descend';self.mode_step=0;self.descent_z=max(tip[2],surface[2]+.025);self.settled=0;self.load.bias_m=0.
            elif self.settled>=3:self.top_mode='top_push';self.mode_step=0;self.command=tuple(tip)
        elif self.top_mode=='top_push':
            self.lost_contact_steps=self.lost_contact_steps+1 if load_n<.2 else 0
            if ready_to_release(self.rear.plan['initial_target_xyz'][1],target[1],direction):
                self.top_mode='top_release';self.mode_step=0;self.release=tuple(tip);self.release_reason='original_margin'
            elif self.continuous_drag and self.lost_contact_steps>=3:
                self._start_recontact(tip,'lost_contact')
                if self.recontact_travel_z != .91:
                    travel_z=self.recontact_travel_z
        cross_correction=None
        if self.top_mode not in ('top_press','top_push'):force=dict(force,applied_z_bias_m=0.,stored_z_bias_m=self.load.bias_m)
        if self.top_mode=='top_lift':waypoint=(*self.start[:2],max(travel_z,self.start[2]))
        elif self.top_mode=='top_cross':waypoint=(*control_xy,travel_z)
        elif self.top_mode=='top_descend':
            xy_error=max(abs(tip[i]-surface[i]) for i in (0,1))
            if xy_error<tolerance:self.descent_z=max(surface[2]+.004,self.descent_z-.0015)
            elif xy_error>(tolerance if self.approach_compensation else .015) and tip[2]<surface[2]+.025:self.descent_z=min(.91,max(self.descent_z,tip[2])+.003)
            waypoint=(*control_xy,self.descent_z)
        elif self.top_mode=='top_press':waypoint=(*control_xy,surface[2]+.002+force['applied_z_bias_m'])
        elif self.top_mode=='top_push':
            desired_y=surface[1]+direction*.012
            if self.continuous_drag:desired_y=direction*min(.34,direction*self.command[1]+self.drag_step_m)
            if (self.hold_push_x or self.hold_established_x) and self.push_x_anchor is None:self.push_x_anchor=control_xy[0]
            desired_x=self.push_x_anchor if (self.hold_push_x or self.hold_established_x) else control_xy[0]
            if self.cross_axis_admittance:
                has_load=loaded_contact is not None and loaded_contact.get('valid',False) and loaded_contact['normal_load_n']>.3
                fx=loaded_contact['force_on_target_world_n'][0] if has_load else 0.
                cross_correction=self.cross_axis_control.update(fx,has_load)
                desired_x+=cross_correction['command_bias_x_m']
            desired=(desired_x,desired_y,surface[2]+.002+force['applied_z_bias_m'])
            self.command=tuple(a+max(-bound,min(bound,b-a)) for a,b,bound in zip(self.command,desired,(.002,self.drag_step_m if self.continuous_drag else .003,.001)))
            waypoint=self.command
        elif self.top_mode=='top_release':waypoint=(*self.release[:2],max(.91,self.release[2]))
        else:raise ValueError('Unknown top contact phase')
        forward_distance=None
        if self.forward_margin_m:
            from simfoundry.data.top_push_contact_geometry import forward_edge_distance
            r=rotation_xyzw(quat)
            measured_local=tuple(sum((tip[i]-target[i])*r[i][k] for i in range(3)) for k in range(3))
            forward_distance=forward_edge_distance(measured_local,quat,self.size,direction)
        self.mode=self.top_mode;self.mode_step+=1
        return dict(tilt_recontact_threshold_rad=self.tilt_recontact_rad,terminal_position_confirmed=position_ready,release_reason=self.release_reason,hand_obstacle_gap_m=hand_obstacle_gap_m,contact_rear_shift_m=self.contact_rear_shift_m,hand_guard_saturated=self.contact_rear_shift_m>=.03,cross_axis_admittance=cross_correction,push_x_anchor_m=self.push_x_anchor,loaded_contact_geometry=loaded_contact,last_recontact_reason=self.last_recontact_reason,travel_height_m=travel_z,observed_parcel_tilt_rad=tilt,observed_forward_edge_distance_m=forward_distance,target_xyz=waypoint,mode=self.mode,control_offset_local=tuple(control_offset_local),observed_support_xyz=list(tip),parcel_top_xyz=surface,corner_local=self.corner_local,approach_xy_bias_m=list(self.approach_xy_bias),observed_target=list(target),contact_load=force,recontacts=self.recontacts,rear_clearance_measured=bool(target[0]>=obstacle[0]+target_radius_x+obstacle_radius_x+self.rear.plan['margin']))
