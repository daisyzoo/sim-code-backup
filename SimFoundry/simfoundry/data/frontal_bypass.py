"""Quarantined frontal pushing route for blocked lateral parcel paths.

Only emits palm waypoints. It never changes object poses/forces and does not
certify full-arm clearance or dynamic reachability. Those are physical audits.
"""
from dataclasses import dataclass
import math
from simfoundry.data.reach_sweep import ready_to_release


def rectangle_radii(size_xy, yaw):
    x,y=(float(v)/2 for v in size_xy)
    if x<=0 or y<=0 or not all(math.isfinite(v) for v in (x,y,yaw)):
        raise ValueError('Invalid parcel footprint')
    c,s=abs(math.cos(yaw)),abs(math.sin(yaw))
    return c*x+s*y,s*x+c*y


def frontal_bypass_plan(target_xyz, obstacle_xyz, target_size_xy, obstacle_size_xy,
                        target_yaw, obstacle_yaw, direction, margin=.02):
    values=[*target_xyz,*obstacle_xyz,target_yaw,obstacle_yaw,direction,margin]
    if direction not in (-1,1) or margin<0 or not all(math.isfinite(v) for v in values):
        raise ValueError('Invalid bypass geometry')
    tx,ty=rectangle_radii(target_size_xy,target_yaw)
    ox,oy=rectangle_radii(obstacle_size_xy,obstacle_yaw)
    goal_y=direction*max(.205,direction*target_xyz[1]+.16)
    low,high=sorted((target_xyz[1],goal_y))
    blocked=(abs(target_xyz[0]-obstacle_xyz[0])<tx+ox+margin and
             high>=obstacle_xyz[1]-ty-oy-margin and low<=obstacle_xyz[1]+ty+oy+margin)
    return dict(required=bool(blocked),rear_goal_x=float(obstacle_xyz[0]+ox+tx+margin),
                target_size_xy=list(target_size_xy),target_radius_x=tx,initial_target_xyz=list(target_xyz),direction=direction,
                nominal_approach_x=float(target_xyz[0]-tx-.065),
                obstacle_initial_xyz=list(obstacle_xyz),obstacle_radius_x=ox,margin=margin,
                scope='Object envelope route, dynamically rechecked if current extents are provided; not full-arm clearance.')


def rear_contact_world_y(target_y,size_x,direction,offset,quat):
    if len(quat)!=4 or direction not in (-1,1) or size_x<=0 or not all(math.isfinite(v) for v in [target_y,size_x,offset,*quat]):raise ValueError('Invalid object-frame rear contact')
    norm=math.sqrt(sum(v*v for v in quat))
    if norm<1e-8:raise ValueError('Zero object quaternion')
    x,y,z,w=(v/norm for v in quat)
    return target_y-2*(x*y+z*w)*size_x/2-(1-2*(x*x+z*z))*direction*offset


@dataclass
class FrontalBypassState:
    plan: dict
    staging_z: float=.92
    press_z: float=.810
    feedback_rear_endpoint: bool=False
    follow_target_y: bool=False
    rear_contact_y_offset_m: float=0.
    rear_contact_object_frame: bool=False
    recontact_after_rear: bool=False
    planned_sweep_x: bool=False
    tracked_sweep: bool=False
    sweep_lead_y: float=.04
    sweep_command_xy: tuple|None=None
    recontact_lift_start: tuple|None=None
    recontact_xy: tuple|None=None
    push_command_y: float|None=None
    mode: str='rear_lift'
    mode_step: int=0
    settled: int=0
    start_palm: tuple|None=None
    push_command_x: float|None=None
    sweep_start: tuple|None=None
    release_start: tuple|None=None

    def update(self,palm,observed_target,observed_obstacle=None,target_radius_x=None,obstacle_radius_x=None,target_quat=None):
        if len(palm)!=3 or len(observed_target)!=3 or not all(math.isfinite(v) for v in [*palm,*observed_target]):
            raise ValueError('Invalid measured physical state')
        if not self.plan['required']:raise ValueError('Bypass not required for this object route')
        if not math.isfinite(self.rear_contact_y_offset_m) or not 0 <= self.rear_contact_y_offset_m <= .04:raise ValueError('Invalid rear contact offset')
        if self.rear_contact_y_offset_m and not self.follow_target_y:raise ValueError('Rear offset requires Y tracking')
        if self.start_palm is None:self.start_palm=tuple(palm)
        obstacle=self.plan['obstacle_initial_xyz'] if observed_obstacle is None else observed_obstacle
        tr=self.plan['target_radius_x'] if target_radius_x is None else target_radius_x
        other_r=self.plan['obstacle_radius_x'] if obstacle_radius_x is None else obstacle_radius_x
        if tr<=0 or other_r<=0 or not all(math.isfinite(v) for v in [*obstacle,tr,other_r]):raise ValueError('Invalid current object envelope')
        rear_goal_x=float(obstacle[0]+other_r+tr+self.plan['margin'])
        x=self.plan['nominal_approach_x'];y=self.plan['initial_target_xyz'][1];direction=self.plan['direction']
        if self.mode=='rear_lift' and palm[2]>=self.staging_z-.015:self.mode,self.mode_step='rear_cross',0
        elif self.mode=='rear_cross' and abs(palm[0]-x)<.035 and abs(palm[1]-y)<.025 and palm[2]>=self.staging_z-.02:self.mode,self.mode_step='rear_press',0
        elif self.mode=='rear_press':
            close=abs(palm[0]-x)<.04 and abs(palm[1]-y)<.025 and palm[2]<=self.press_z+.025
            self.settled=self.settled+1 if close else 0
            if self.settled>=3:self.mode,self.mode_step='rear_push',0;self.push_command_x=float(palm[0])
        elif self.mode=='rear_push' and observed_target[0]>=rear_goal_x:
            if self.recontact_after_rear:
                self.mode,self.mode_step='bypass_lift',0;self.recontact_lift_start=tuple(palm)
                self.recontact_xy=(observed_target[0]-.06,observed_target[1]-direction*.06)
                self.settled=0
            else:
                self.mode,self.mode_step='bypass_sweep',0;self.sweep_start=tuple(palm)
        elif self.mode=='bypass_lift' and palm[2]>=self.staging_z-.015:
            self.mode,self.mode_step='bypass_cross',0
        elif self.mode=='bypass_cross' and abs(palm[0]-self.recontact_xy[0])<.035 and abs(palm[1]-self.recontact_xy[1])<.025 and palm[2]>=self.staging_z-.02:
            self.mode,self.mode_step='bypass_press',0
        elif self.mode=='bypass_press':
            close=abs(palm[0]-self.recontact_xy[0])<.03 and abs(palm[1]-self.recontact_xy[1])<.025 and palm[2]<=.865
            self.settled=self.settled+1 if close else 0
            if self.settled>=3:
                self.mode,self.mode_step='bypass_sweep',0;self.sweep_start=tuple(palm)
        elif self.mode=='bypass_sweep' and ready_to_release(y,observed_target[1],direction):
            self.mode,self.mode_step='bypass_release',0;self.release_start=tuple(palm)
        if self.mode=='rear_lift':target=(*self.start_palm[:2],self.staging_z)
        elif self.mode=='rear_cross':target=(x,y,self.staging_z)
        elif self.mode=='rear_press':target=(x,y,self.press_z)
        elif self.mode=='rear_push':
            # Fingertip nominal contact, rather than demanding palm at object center.
            endpoint=rear_goal_x-tr-.035
            if self.feedback_rear_endpoint:
                # Infer the current palm-to-object offset from measured poses;
                # limit command tracking lead and never move the parcel directly.
                endpoint=min(rear_goal_x-tr+.015, palm[0]+max(0.,rear_goal_x-observed_target[0])+.008, palm[0]+.02)
                self.push_command_x+=max(-.003,min(.003,endpoint-self.push_command_x))
            else:
                self.push_command_x=min(endpoint,self.push_command_x+.003)
            if self.follow_target_y:
                if self.push_command_y is None:self.push_command_y=y
                desired_y=observed_target[1]-direction*self.rear_contact_y_offset_m
                if self.rear_contact_object_frame:
                    if target_quat is None or self.rear_contact_y_offset_m<=0:raise ValueError('Object-frame offset requires actual quaternion and positive offset')
                    desired_y=rear_contact_world_y(observed_target[1],self.plan['target_size_xy'][0],direction,self.rear_contact_y_offset_m,target_quat)
                self.push_command_y+=max(-.002,min(.002,desired_y-self.push_command_y))
                y=self.push_command_y
            target=(self.push_command_x,y,self.press_z)
        elif self.mode=='bypass_lift':target=(*self.recontact_lift_start[:2],self.staging_z)
        elif self.mode=='bypass_cross':target=(*self.recontact_xy,self.staging_z)
        elif self.mode=='bypass_press':target=(*self.recontact_xy,.84)
        elif self.mode=='bypass_sweep':
            t=min(1.,self.mode_step/74.);s=t*t*(3-2*t)
            # Start at actual established contact instead of jumping to a distant waypoint.
            sweep_x=self.sweep_start[0]
            if self.planned_sweep_x:
                if self.recontact_xy is None:raise ValueError('Planned sweep X requires measured recontact route')
                blend=min(1.,self.mode_step/30.);blend=blend*blend*(3-2*blend)
                sweep_x+=blend*(self.recontact_xy[0]-sweep_x)
            sweep_y=self.sweep_start[1]+s*(direction*.34-self.sweep_start[1])
            if self.tracked_sweep:
                if self.sweep_command_xy is None:self.sweep_command_xy=self.sweep_start[:2]
                previous_x,previous_y=self.sweep_command_xy
                sweep_x=previous_x+max(-.003,min(.003,observed_target[0]-.06-previous_x))
                if not math.isfinite(self.sweep_lead_y) or not 0 <= self.sweep_lead_y <= .06:raise ValueError('Invalid sweep lead')
                goal_y=direction*min(.34,direction*observed_target[1]+self.sweep_lead_y)
                sweep_y=previous_y+max(-.006,min(.006,goal_y-previous_y))
                self.sweep_command_xy=(sweep_x,sweep_y)
            target=(sweep_x,sweep_y,self.sweep_start[2])
        elif self.mode=='bypass_release':target=(*self.release_start[:2],max(self.staging_z,self.release_start[2]))
        else:raise ValueError('Unknown bypass mode')
        self.mode_step+=1
        return dict(target_xyz=tuple(float(v) for v in target),mode=self.mode,
                    rear_goal_x=rear_goal_x,observed_target=list(observed_target),
                    rear_clearance_measured=bool(observed_target[0]>=rear_goal_x))


def extent_x_from_quat(size_xyz, quat_xyzw):
    if len(size_xyz)!=3 or len(quat_xyzw)!=4 or not all(math.isfinite(v) for v in [*size_xyz,*quat_xyzw]) or min(size_xyz)<=0:
        raise ValueError('Invalid current box pose')
    norm=math.sqrt(sum(v*v for v in quat_xyzw))
    if norm<1e-8:raise ValueError('Invalid zero quaternion')
    x,y,z,w=(v/norm for v in quat_xyzw)
    row=(1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w))
    return sum(abs(r)*length/2 for r,length in zip(row,size_xyz))
