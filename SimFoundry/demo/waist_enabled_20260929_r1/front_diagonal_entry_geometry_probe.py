"""Unwired fixed-observed-orientation front-corner center-path proposal.
Exact piecewise-linear AABB separation along arbitrary XY segments; no robot,
contact force, future object orientation, controller or dataset certification.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation

def segment_gap(a,b,obstacle,radii):
 a,b,o,r=map(lambda x:np.asarray(x,dtype=float),(a,b,obstacle,radii))
 if any(x.shape!=(2,) or not np.isfinite(x).all() for x in [a,b,o,r]) or np.any(r<=0):raise ValueError('Invalid segment geometry')
 start=a-o;delta=b-a;intercepts=np.r_[start-r,-start-r];slopes=np.r_[delta,-delta];ts=[0.,1.]
 for i in range(4):
  for j in range(i):
   den=slopes[i]-slopes[j]
   if abs(den)>1e-14:
    t=(intercepts[j]-intercepts[i])/den
    if 0<t<1:ts.append(float(t))
 vals=[float(np.max(intercepts+t*slopes)) for t in ts];i=int(np.argmin(vals));return dict(minimum_axis_gap_m=vals[i],at_fraction=ts[i])

def propose(target,obstacle,size,other_size,quat,other_quat,direction,margin=.012,reserve=.003,table_margin=.005,front_x=None):
 target,obstacle,size,other_size=map(lambda x:np.asarray(x,dtype=float),(target,obstacle,size,other_size))
 if direction not in [-1,1] or any(x.shape!=(3,) or not np.isfinite(x).all() for x in [target,obstacle,size,other_size]) or min(*size,*other_size)<=0 or not .012<=margin<=.03 or reserve!=.003 or table_margin!=.005:raise ValueError('Invalid planning input')
 tr=abs(Rotation.from_quat(quat).as_matrix())@size/2;other=abs(Rotation.from_quat(other_quat).as_matrix())@other_size/2;combined=tr[:2]+other[:2]
 goal_y=direction*max(.205,direction*target[1]+.16);goal_x=min(target[0],obstacle[0]-combined[0]-margin-reserve)
 if front_x is not None:
  if not math.isfinite(front_x):raise ValueError('Invalid front target')
  goal_x=float(front_x)
 near_y=obstacle[1]-direction*(combined[1]+margin+reserve);corner_y=target[1]+direction*np.clip(direction*(near_y-target[1]),0.,direction*(goal_y-target[1]))
 diagonal=[target[:2].tolist(),[goal_x,float(corner_y)],[goal_x,float(goal_y)]];axis=[target[:2].tolist(),[goal_x,float(target[1])],[goal_x,float(goal_y)]];out=[]
 for name,path in [('axis',axis),('diagonal',diagonal)]:
  gaps=[segment_gap(a,b,obstacle[:2],combined) for a,b in zip(path,path[1:])];tm=min(min(x-tr[0]-.28,.88-x-tr[0],y-tr[1]+.75,.75-y-tr[1]) for x,y in path);length=sum(np.linalg.norm(np.asarray(b)-a) for a,b in zip(path,path[1:]));out.append(dict(route=name,points=path,minimum_axis_gap_m=min(g['minimum_axis_gap_m'] for g in gaps),minimum_table_margin_m=float(tm),length_m=float(length),eligible=bool(tm>=table_margin-1e-10 and all(g['minimum_axis_gap_m']>=margin-1e-10 for g in gaps)),segments=gaps))
 return dict(routes=out,scope=__doc__,training_ready=False)
