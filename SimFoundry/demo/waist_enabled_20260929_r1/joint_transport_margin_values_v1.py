"""Scalar transport margins with original arithmetic and geometry, no unused Jacobians.
Not an independent safety certificate. For immutable native scene/guard contexts.
"""
import numpy as np
from scipy.spatial.transform import Rotation

def pose(model,side,q):
    q=np.asarray(q,dtype=float)
    if q.shape!=(11,) or not np.isfinite(q).all() or side not in model.chains:raise ValueError('Invalid articulated hand query')
    m=model.base.copy()
    for name,origin,axis in model.chains[side]:
        m=m@origin
        if axis is not None:
            index=model.names.index(name) if name in model.names else None
            a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();m=m@a
    return m

def elbow_values(geometry,q):
    q=np.asarray(q,dtype=float)
    if q.shape!=(11,) or not np.isfinite(q).all():raise ValueError('Invalid elbow query')
    result=[]
    for side in ['left','right']:
        M=geometry.model.base.copy();torso=None
        for name,origin,axis in geometry.model.chains[side]:
            M=M@origin
            if axis is not None:
                index=geometry.model.names.index(name) if name in geometry.model.names else None
                R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(axis*(q[index] if index is not None else 0.)).as_matrix();M=M@R
            if name=='waist_yaw_joint':torso=M.copy()
            if name==side+'_elbow_joint':break
        if torso is None:raise ValueError('Unsupported torso chain')
        world=geometry.vertices[side]@M[:3,:3].T+M[:3,3];p=(world-torso[:3,3])@torso[:3,:3];projection=p@geometry.axes.T;mins=np.argmin(projection,axis=0);maxs=np.argmax(projection,axis=0);low=projection[mins,np.arange(len(geometry.axes))];high=projection[maxs,np.arange(len(geometry.axes))];gaps=np.r_[low-geometry.high,geometry.low-high];branch=int(np.argmax(gaps));result.append(float(gaps[branch]))
    return np.array(result)

def scene_margins(scene,q,floor,elbow_floor):
    model=scene.guard.model;T=pose(model,scene.side,q);Ti=pose(model,scene.inactive,q);iv=model.vertices[scene.inactive];ip=iv@Ti[:3,:3].T+Ti[:3,3];ii=int(ip[:,2].argmin());inactive_z=float(ip[ii,2]);gaps={}
    for side,mat,label,pos,quat,size in [(scene.side,T,'active_other',scene.other,scene.other_quat,scene.other_size),(scene.inactive,Ti,'inactive_target',scene.target,scene.quat,scene.core),(scene.inactive,Ti,'inactive_other',scene.other,scene.other_quat,scene.other_size)]:
        gaps[label]=float(scene.separators[side].gap(mat[:3,3],Rotation.from_matrix(mat[:3,:3]).as_quat(),pos,quat,size))
    return np.r_[inactive_z-floor,gaps['inactive_target']-.01,gaps['inactive_other']-.01,gaps['active_other']-.01,elbow_values(scene.guard.geometry,q)-elbow_floor]
