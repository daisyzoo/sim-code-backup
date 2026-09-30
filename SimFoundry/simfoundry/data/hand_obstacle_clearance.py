"""Conservative face-axis separation of actual convex hand and parcel Cube.

Positive gap proves separation along a unit axis. Omitting edge-cross axes can
underestimate clearance; nonpositive output is a potential overlap, not a full
collision certificate. No physical state or force is changed.
"""
from functools import lru_cache
import itertools
import numpy as np
from scipy.spatial import ConvexHull
from simfoundry.data.top_contact_bypass import support_mesh,rotation_xyzw

class ConvexFaceSeparation:
    def __init__(self,points):
        self.vertices=np.asarray(points,dtype=float)
        if self.vertices.ndim!=2 or self.vertices.shape[1]!=3 or not np.isfinite(self.vertices).all():raise ValueError('Invalid hull points')
        hull=ConvexHull(self.vertices)
        self.axes=np.unique(np.round(hull.equations[:,:3],10),axis=0)
        self.axes/=np.linalg.norm(self.axes,axis=1)[:,None]
        projected=self.vertices@self.axes.T
        self.low=projected.min(0);self.high=projected.max(0)

    def gap(self,hand_xyz,hand_quat,box_xyz,box_quat,box_size):
        values=[*hand_xyz,*box_xyz,*box_size]
        if len(hand_xyz)!=3 or len(box_xyz)!=3 or len(box_size)!=3 or not np.isfinite(values).all() or min(box_size)<=0:raise ValueError('Invalid hand/box geometry')
        rh=np.array(rotation_xyzw(hand_quat));rb=np.array(rotation_xyzw(box_quat));center=(np.array(box_xyz)-hand_xyz)@rh
        # Box vertices in the hand frame, hand face projections precomputed.
        box=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(box_size)/2
        b=(box@rb.T@rh+center)@self.axes.T
        hand_axes_gap=np.maximum(b.min(0)-self.high,self.low-b.max(0)).max()
        # Hand vertices projected on the three box face normals.
        h=(self.vertices@rh.T+np.array(hand_xyz)-box_xyz)@rb;half=np.array(box_size)/2
        box_axes_gap=np.maximum(h.min(0)-half,-half-h.max(0)).max()
        return float(max(hand_axes_gap,box_axes_gap))

@lru_cache(maxsize=2)
def hand_face_separation(side):
    return ConvexFaceSeparation(support_mesh()[side])
