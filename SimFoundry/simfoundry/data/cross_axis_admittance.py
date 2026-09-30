"""Bounded robot waypoint correction to reduce non-task world-X contact force.

This controls robot commands only. No force or pose is applied to the parcel.
"""
from dataclasses import dataclass
import math

@dataclass
class CrossAxisAdmittance:
    bias_m: float=0.
    filtered_force_n: float=0.
    gain_m_per_n: float=.0008
    max_step_m: float=.0005
    max_bias_m: float=.01

    def reset(self):
        self.bias_m=0.;self.filtered_force_n=0.

    def update(self,force_x_n,active):
        if not all(math.isfinite(x) for x in (force_x_n,self.gain_m_per_n,self.max_step_m,self.max_bias_m,self.bias_m,self.filtered_force_n)) or not 0<self.gain_m_per_n<=.001 or not 0<self.max_step_m<=.0005 or not 0<self.max_bias_m<=.01:
            raise ValueError('Invalid diagnostic cross-axis admittance')
        self.filtered_force_n=.25*force_x_n+.75*self.filtered_force_n
        if active:
            step=max(-self.max_step_m,min(self.max_step_m,-self.gain_m_per_n*self.filtered_force_n))
            self.bias_m=max(-self.max_bias_m,min(self.max_bias_m,self.bias_m+step))
        return dict(observed_force_x_on_target_n=float(force_x_n),filtered_force_x_on_target_n=self.filtered_force_n,command_bias_x_m=self.bias_m,active=bool(active),max_bias_m=self.max_bias_m,max_step_m=self.max_step_m)
