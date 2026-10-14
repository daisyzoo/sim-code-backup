"""Closed eye-level tour with unwrapped yaw, avoiding opposite-target interpolation."""
import math


def tour_pose(route,fraction):
    position=max(0,min(1,fraction))*(len(route)-1)
    index=min(int(position),len(route)-2);t=position-index;t=t*t*(3-2*t)
    a,b=route[index],route[index+1]
    eye=[x+(y-x)*t for x,y in zip(a['eye'],b['eye'])]
    yaw=math.radians(a['yaw']+(b['yaw']-a['yaw'])*t)
    pitch=math.radians(a['pitch']+(b['pitch']-a['pitch'])*t)
    direction=[math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)]
    return eye,[x+y for x,y in zip(eye,direction)]
