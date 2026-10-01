"""Isolated contact-bout heading anchor; soft IK task, no parcel intervention."""
import math
import numpy as np
from dataclasses import dataclass


def rotation(value):
    r=np.asarray(value,dtype=float)
    if r.shape!=(3,3) or not np.isfinite(r).all() or not np.allclose(r.T@r,np.eye(3),atol=1e-6) or abs(np.linalg.det(r)-1)>1e-6:
        raise ValueError('Invalid hand rotation')
    return r


@dataclass
class ContactBoutYaw:
    axis: int | None=None
    target_heading: float | None=None

    def update(self, mode, rotation_world=None):
        # No stale heading on approach, loss/recovery, guard, release or idle.
        if mode!='top_push':
            self.axis=None;self.target_heading=None
            return None
        r=rotation(rotation_world)
        if self.axis is None:
            self.axis=int(np.argmax(np.sum(r[:2,:]**2,axis=0)))
            self.target_heading=math.atan2(r[1,self.axis],r[0,self.axis])
        return dict(axis=self.axis,target_heading_rad=self.target_heading)


def contact_bout_yaw_constraint(rotation_world, angular_jacobian_world, anchor, weight_m=.15):
    r=rotation(rotation_world);j=np.asarray(angular_jacobian_world,dtype=float)
    if j.ndim!=2 or j.shape[0]!=3 or not np.isfinite(j).all() or not math.isfinite(weight_m) or not 0<weight_m<=.3:
        raise ValueError('Invalid yaw constraint input')
    axis=anchor['axis'];target=anchor['target_heading_rad']
    if type(axis) is not int or axis not in (0,1,2) or not math.isfinite(target) or abs(target)>math.pi:
        raise ValueError('Invalid heading anchor')
    v=r[:,axis];den=float(v[0]**2+v[1]**2)
    if den<.01:raise ValueError('Heading reference is near vertical')
    current=math.atan2(v[1],v[0]);delta=math.atan2(math.sin(target-current),math.cos(target-current))
    skew=np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]])
    jac=weight_m*(np.array([-v[1],v[0],0.])/den)@(-skew)@j
    return dict(jacobian=jac[None,:],error=np.array([weight_m*np.clip(.72*delta,-.1,.1)]),axis=axis,target_heading_rad=float(target),current_heading_rad=float(current),heading_error_rad=float(delta),horizontal_axis_norm_sq=den,weight_m=float(weight_m))
