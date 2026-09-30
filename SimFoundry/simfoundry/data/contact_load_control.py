"""Diagnostic vertical admittance from the previous solved contact observation."""
from dataclasses import dataclass
import math


def hand_target_vertical_load(record,side,target_name):
    if side not in ('left','right') or target_name not in ('parcel_box','mailer'):
        raise ValueError('Unknown contact pair')
    if record is None:return 0.
    total=0.
    for contact in record['parcel_contacts']:
        labels=contact['shapes']
        if any(f'{side}_wrist_roll' in s for s in labels) and any(f'/{target_name}/' in s for s in labels):
            f=float(contact['force_world_N'][2])
            if not math.isfinite(f):raise ValueError('Nonfinite observed contact force')
            total+=abs(f)
    return total


@dataclass
class ContactLoadControl:
    desired_n: float
    bias_m: float=0.
    filtered_n: float=0.
    min_bias_m: float=0.

    def update(self,load_n,active):
        if not math.isfinite(load_n) or load_n<0 or not .5<=self.desired_n<=5. or not math.isfinite(self.min_bias_m) or not -.03<=self.min_bias_m<=0:
            raise ValueError('Invalid diagnostic load setting')
        self.filtered_n=.25*load_n+.75*self.filtered_n
        if active:
            step=max(-.0005,min(.003,.0008*(self.filtered_n-self.desired_n)))
            self.bias_m=max(self.min_bias_m,min(.025,self.bias_m+step))
        # Lifting/approach remains the explicit waypoint path, without stale bias.
        return dict(observed_vertical_load_n=load_n,filtered_vertical_load_n=self.filtered_n,
                    applied_z_bias_m=self.bias_m if active else 0.,stored_z_bias_m=self.bias_m)
