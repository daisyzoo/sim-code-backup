"""Diagnostic state-triggered two-pass expert; joint commands only."""
import numpy as np
from simfoundry.data.sorting_cartesian_expert import CartesianSweepState,cartesian_sweep_palm

class EventRecontactController:
    def __init__(self,side,initial_xyz):
        if side not in ('left','right'):raise ValueError('Invalid arm')
        self.side=side;self.initial=np.asarray(initial_xyz,dtype=float).copy()
        if self.initial.shape!=(3,) or not np.isfinite(self.initial).all():raise ValueError('Invalid initial parcel')
        self.direction=1 if side=='left' else -1;self.phase='first';self.events=[];self.held=None
        self.state=self._state(self.initial,False)
    def _state(self,xyz,second):
        offset=-.04 if self.direction*xyz[1]<-.03 else (-.11 if xyz[0]>=.48 else -.13)
        return CartesianSweepState(self.side,float(xyz[0]),float(xyz[1]),exit_y=.30,
            contact_x_bias=.04 if second else 0.,contact_palm_z=(.840 if self.side=='left' else .845)-(.02 if second else 0.),
            staging_palm_z=1. if second else .92,contact_side_offset=offset)
    def action(self,robot,hands,step,default_q,observed_xyz,previous_offset):
        xyz=np.asarray(observed_xyz,dtype=float)
        if xyz.shape!=(3,) or not np.isfinite(xyz).all():raise ValueError('Invalid observed parcel')
        if step==0:return np.zeros(23,dtype=np.float32)
        if self.phase=='done':return self.held.copy()
        progress=self.direction*(xyz[1]-self.initial[1]);signed_y=self.direction*xyz[1]
        if signed_y>=.23 and progress>=.15:
            self.phase='done';self.held=np.asarray(previous_offset,dtype=np.float32).copy();self.events.append(dict(step=step,event='goal_hold',xyz=xyz.tolist()));return self.held.copy()
        if self.phase=='first' and (progress>=.10 or self.state.mode=='hold'):
            self.phase='second';self.state=self._state(xyz,True);self.events.append(dict(step=step,event='recontact',xyz=xyz.tolist(),progress_m=float(progress)))
        result=np.zeros(23,dtype=np.float32)
        cartesian_sweep_palm(robot,hands,result,state=self.state,step=step-1,default_q=default_q)
        return result
