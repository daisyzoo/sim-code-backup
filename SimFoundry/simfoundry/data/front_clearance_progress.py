"""Observed clearance stage logic with optional bounded hysteresis.

Use observed nominal clearance sustained over three observations as an
alternative to the fast0.5mm reserve transition. No time-only or unsafe bypass.
"""
from dataclasses import dataclass
import math

@dataclass
class FrontClearanceProgress:
    clearance_m: float
    hold_y: float
    stage: str='front_x'
    recoveries: int=0
    confirm_nominal_clearance: bool=False
    safe_observations: int=0
    recovery_hysteresis_m: float=0.

    def update(self,gap_m,target_y):
        if not all(math.isfinite(v) for v in (self.clearance_m,self.hold_y,gap_m,target_y)) or not .012<=self.clearance_m<=.03:
            raise ValueError('Invalid front-clearance progress geometry')
        if not math.isfinite(self.recovery_hysteresis_m) or not 0<=self.recovery_hysteresis_m<=.001 or self.clearance_m-self.recovery_hysteresis_m<.011:
            raise ValueError('Hysteresis limited to1mm with recovery above11mm')
        if self.stage not in ('front_x','lateral_y'):
            raise ValueError('Invalid route stage')
        entered=False;resume_reason=None
        if self.stage=='front_x':
            self.safe_observations=self.safe_observations+1 if gap_m>=self.clearance_m else 0
            if gap_m>=self.clearance_m+.0005:
                self.stage='lateral_y';resume_reason='reserve_met'
            elif self.confirm_nominal_clearance and self.safe_observations>=3:
                self.stage='lateral_y';resume_reason='nominal_clearance_confirmed_3'
        elif gap_m<self.clearance_m-self.recovery_hysteresis_m:
            self.stage='front_x';self.hold_y=float(target_y);self.recoveries+=1;entered=True;self.safe_observations=0
        return dict(route_stage=self.stage,front_hold_y=self.hold_y,
                    clearance_recovery_count=self.recoveries,clearance_recovery_entered=entered,
                    resume_clearance_m=self.clearance_m+.0005,recover_clearance_m=self.clearance_m-self.recovery_hysteresis_m,recovery_hysteresis_m=self.recovery_hysteresis_m,
                    nominal_clearance_confirmation=self.confirm_nominal_clearance,
                    safe_clearance_observations=self.safe_observations,clearance_resume_reason=resume_reason)
