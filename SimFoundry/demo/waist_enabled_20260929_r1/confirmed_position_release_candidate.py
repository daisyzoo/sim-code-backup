"""Offline proposal only: original target-position conditions, not full quality.

No controller imports this module. A true value may propose unloading at current
hand XY using the existing release motion; it never certifies task/pose/collision
or allows training. It does not override existing emergency guards.
"""
from collections import deque
import math

class ConfirmedPositionRelease:
    def __init__(self, initial_y, direction):
        if direction not in (-1, 1) or not math.isfinite(initial_y):
            raise ValueError('finite initial Y and signed direction required')
        self.initial_y=float(initial_y);self.direction=direction;self.window=deque(maxlen=10)
    def observe(self, target_xyz):
        point=tuple(float(x) for x in target_xyz)
        if len(point)!=3 or not all(math.isfinite(x) for x in point):
            raise ValueError('finite measured XYZ required')
        self.window.append(point)
        return (len(self.window)==10
                and self.direction*(point[1]-self.initial_y)>=.15
                and all(self.direction*p[1]>=.20 for p in self.window)
                and math.hypot(point[0]-self.window[0][0],point[1]-self.window[0][1])<=.01)
