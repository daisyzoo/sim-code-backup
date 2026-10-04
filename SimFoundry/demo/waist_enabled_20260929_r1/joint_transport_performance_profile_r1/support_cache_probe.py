"""UNWIRED mathematical support-function cache for independent gap profiling.
Uses ALL original hand vertices to cache local face-axis extrema. Original
world face axes and box vertices retained. This prototype does not yet provide
a conservative floating-point interval or production path certificate.
"""
import itertools
import numpy as np
from scipy.spatial.transform import Rotation
from audit_front_recontact_center_events import RecoveryEventAudit
class CachedSupportAudit(RecoveryEventAudit):
 def __init__(self,root,stage):
  super().__init__(root,stage)
  self.extrema={}
  for side in ['left','right']:
   v=self.hand.vertices[side]@self.axes[side].T
   self.extrema[side]=(v.min(0),v.max(0))
  self.corners=np.array(list(itertools.product([-1.,1.],repeat=3)))
 def gap(self,side,pose,position,quat,size):
  R=pose[:3,:3];t=pose[:3,3]
  if np.max(abs(R.T@R-np.eye(3)))>1e-12:return super().gap(side,pose,position,quat,size)
  boxR=Rotation.from_quat(quat).as_matrix();own=self.axes[side]@R.T;axes=np.vstack([own,boxR.T]);offset=t@own.T
  mn,mx=self.extrema[side];cross=(self.hand.vertices[side]@R.T+t)@boxR
  handmin=np.r_[mn+offset,cross.min(0)];handmax=np.r_[mx+offset,cross.max(0)]
  boxes=(self.corners*np.array(size)/2@boxR.T+position)@axes.T
  return float(np.max(np.r_[boxes.min(0)-handmax,handmin-boxes.max(0)]))
