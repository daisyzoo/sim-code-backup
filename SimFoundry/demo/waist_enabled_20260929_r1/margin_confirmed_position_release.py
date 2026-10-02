"""Isolated confirmed release that also retains the existing release margins.
The original10-frame observed-position/stability condition remains necessary.
The existing5mm zone and10mm progress planning margins remain necessary too.
No task-quality threshold changes; collector wiring/physics still required.
"""
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease as Parent
from simfoundry.data.reach_sweep import ready_to_release

class ConfirmedPositionRelease(Parent):
    def observe(self,target_xyz):
        confirmed=super().observe(target_xyz)
        return bool(confirmed and ready_to_release(self.initial_y,self.window[-1][1],self.direction))
