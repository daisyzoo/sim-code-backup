"""Diagnostic torso-frame AABB separating gap of real USD convex elbow/torso.
Positive gap certifies separation on a torso coordinate axis; negative is inconclusive.
No body-pose or object intervention. Source hull vertices are hash-bound separately.
"""
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
class ElbowTorsoClearance:
 def __init__(self,model,source):
  self.model=model;self.source=Path(source);data=json.loads(self.source.read_text());self.vertices=np.array(data['elbow']['vertices']);torso=np.array(data['torso']['vertices']);self.low=torso.min(0);self.high=torso.max(0)
 def gap(self,q):
  M=self.model.base.copy();torso=elbow=None
  for name,origin,axis in self.model.chains['right']:
   M=M@origin
   if axis is not None:
    angle=q[self.model.names.index(name)] if name in self.model.names else 0.;T=np.eye(4);T[:3,:3]=Rotation.from_rotvec(axis*angle).as_matrix();M=M@T
   if name=='waist_yaw_joint':torso=M.copy()
   if name=='right_elbow_joint':elbow=M.copy();break
  if torso is None or elbow is None:raise ValueError('Unsupported arm chain')
  relative=torso[:3,:3].T@elbow[:3,:3];center=torso[:3,:3].T@(elbow[:3,3]-torso[:3,3]);p=self.vertices@relative.T+center
  return float(np.maximum(p.min(0)-self.high,self.low-p.max(0)).max())
