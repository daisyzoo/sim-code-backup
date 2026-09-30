"""Quarantined physical fingertip side-contact route after rear clearance.

Emits robot waypoints only. Actual mesh vertex, not an extended virtual tool.
Does not certify collision-free arm paths or sustained physical contact.
"""
from dataclasses import dataclass
import math
from simfoundry.data.reach_sweep import ready_to_release


def distal_mesh_vertex(side):
    # Actual max-X vertices of the shipped left/right U1 rubber-hand STL.
    if side == 'left':return (.2533150613307953,-.02431151084601879,.00818454660475254)
    if side == 'right':return (.2533150613307953,.02431151084601879,.008186472579836845)
    raise ValueError('Unknown hand side')


def contact_pad_mesh_vertex(side):
    # Nearest shipped STL vertex to median measured contact, extended run62000.
    # Contact-margin/timing gaps: left6.07mm/right2.12mm; not a calibrated patch.
    if side == 'left':return (.23085735738277435,-.0006534020649269223,-.01938154362142086)
    if side == 'right':return (.23980176448822021,.006234536878764629,-.015244950540363789)
    raise ValueError('Unknown hand side')


def side_surface_point(xyz,quat,size,direction):
    if len(xyz)!=3 or len(quat)!=4 or len(size)!=3 or min(size)<=.03 or direction not in (-1,1) or not all(math.isfinite(v) for v in [*xyz,*quat,*size]):raise ValueError('Invalid parcel pose')
    norm=math.sqrt(sum(v*v for v in quat))
    if norm<1e-8:raise ValueError('Zero quaternion')
    x,y,z,w=(v/norm for v in quat)
    rot=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
    # Select the actual object face facing the approach side in world Y.
    # Hard-coding local Y chooses the wrong face after a quarter turn.
    face_axis=max((0,1),key=lambda k:abs(rot[1][k]))
    face_sign=1 if -direction*rot[1][face_axis]>=0 else -1
    free_axis=1-face_axis
    local=[0.,0.,size[2]/2-.003]
    local[face_axis]=face_sign*size[face_axis]/2
    local[free_axis]=(-1 if rot[0][free_axis]>=0 else 1)*(size[free_axis]/2-.015)
    return tuple(xyz[i]+sum(rot[i][k]*local[k] for k in range(3)) for i in range(3))


@dataclass
class FingertipBypassState:
    rear: object
    side: str
    size: tuple
    mode: str='rear_lift'
    mode_step: int=0
    tip_mode: str|None=None
    lift_start: tuple|None=None
    release_start: tuple|None=None
    command: tuple|None=None
    settled: int=0
    use_contact_pad: bool=False
    strict_descent: bool=False

    def control_vertex(self):
        return contact_pad_mesh_vertex(self.side) if self.use_contact_pad else distal_mesh_vertex(self.side)

    def update(self,palm,target,obstacle,target_radius_x,obstacle_radius_x,*,tip,quat):
        if len(tip)!=3 or not all(math.isfinite(v) for v in tip):raise ValueError('Invalid measured fingertip')
        direction=self.rear.plan['direction'];surface=side_surface_point(target,quat,self.size,direction)
        if self.tip_mode is None:
            row=self.rear.update(palm,target,obstacle,target_radius_x,obstacle_radius_x,target_quat=quat)
            if row['mode']!='bypass_sweep':
                self.mode,self.mode_step=self.rear.mode,self.rear.mode_step
                return dict(row,control_offset_local=None,observed_tip_xyz=list(tip))
            self.tip_mode='tip_lift';self.mode_step=0;self.lift_start=tuple(tip)
        outside=(surface[0],surface[1]-direction*.012,surface[2])
        if self.tip_mode=='tip_lift' and tip[2]>=.90:
            self.tip_mode='tip_cross';self.mode_step=0
        elif self.tip_mode=='tip_cross' and abs(tip[0]-outside[0])<(.005 if self.strict_descent else .02) and abs(tip[1]-outside[1])<(.005 if self.strict_descent else .02) and tip[2]>=.90:
            self.tip_mode='tip_press';self.mode_step=0
        elif self.tip_mode=='tip_press':
            close=abs(tip[0]-outside[0])<.02 and abs(tip[1]-outside[1])<.02 and abs(tip[2]-outside[2])<.015
            self.settled=self.settled+1 if close else 0
            if self.settled>=3:self.tip_mode='tip_sweep';self.mode_step=0;self.command=tuple(tip)
        elif self.tip_mode=='tip_sweep' and ready_to_release(self.rear.plan['initial_target_xyz'][1],target[1],direction):
            self.tip_mode='tip_release';self.mode_step=0;self.release_start=tuple(tip)
        if self.tip_mode=='tip_lift':waypoint=(*self.lift_start[:2],max(.92,self.lift_start[2]))
        elif self.tip_mode=='tip_cross':waypoint=(*outside[:2],.92)
        elif self.tip_mode=='tip_press':waypoint=outside
        elif self.tip_mode=='tip_sweep':
            desired=(surface[0],surface[1]+direction*.004,surface[2])
            self.command=tuple(a+max(-limit,min(limit,b-a)) for a,b,limit in zip(self.command,desired,(.003,.004,.0015)))
            waypoint=self.command
        elif self.tip_mode=='tip_release':waypoint=(*self.release_start[:2],max(.92,self.release_start[2]))
        else:raise ValueError('Unknown fingertip phase')
        self.mode=self.tip_mode;self.mode_step+=1
        return dict(target_xyz=waypoint,mode=self.mode,control_offset_local=self.control_vertex(),observed_tip_xyz=list(tip),parcel_surface_xyz=surface,observed_target=list(target),rear_clearance_measured=bool(target[0]>=obstacle[0]+obstacle_radius_x+target_radius_x+self.rear.plan['margin']))
