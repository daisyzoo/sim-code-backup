"""Read-only unchanged-camera projection for diagnostic robot waist preference."""
from functools import lru_cache
import itertools,math
import numpy as np
from simfoundry.calibration.sorting_station import SORTING_D435I_POS,SORTING_D435I_ROT_XYZW
from simfoundry.data.top_contact_bypass import rotation_xyzw

@lru_cache(maxsize=8)
def camera_grid(limit):
    yaws=np.linspace(-limit,limit,max(3,int(math.ceil(2*limit/.005))+1))
    rot=np.zeros((len(yaws),3,3));c=np.cos(yaws);s=np.sin(yaws)
    rot[:,0,0]=c;rot[:,0,1]=-s;rot[:,1,0]=s;rot[:,1,1]=c;rot[:,2,2]=1.
    positions=np.array([.08-.0039635,0,.793+.044])+rot@np.array(SORTING_D435I_POS)
    rotations=rot@np.array(rotation_xyzw(SORTING_D435I_ROT_XYZW))
    return yaws,positions,rotations


def visible_waist_preference(center,quat,size,intrinsics,width,height,current_waist,limit,minimum_fraction=.5):
    values=[*center,*size,*intrinsics,width,height,current_waist,limit,minimum_fraction]
    if not all(math.isfinite(v) for v in values) or min(size)<=0 or min(intrinsics[:2])<=0 or min(width,height)<=0 or not 0<limit<=1. or not 0<minimum_fraction<=1:
        raise ValueError('Invalid camera preference inputs')
    yaws,positions,rotations=camera_grid(float(limit));corners=np.array(list(itertools.product([-1,1],repeat=3)))*np.array(size)/2
    world=corners@np.array(rotation_xyzw(quat)).T+np.array(center)
    camera=np.einsum('nki,nij->nkj',world[None]-positions[:,None],rotations)
    fx,fy,cx,cy=intrinsics;depth=camera[:,:,2];safe_depth=np.where(abs(depth)<1e-9,1e-9,depth)
    uv=np.stack([fx*camera[:,:,0]/safe_depth+cx,fy*camera[:,:,1]/safe_depth+cy],axis=-1)
    lo,hi=uv.min(1),uv.max(1);area=np.prod(hi-lo,axis=1)
    intersection=np.maximum(0,np.minimum(hi,[width,height])-np.maximum(lo,[0,0]))
    fractions=np.where((depth>0).all(1),np.prod(intersection,axis=1)/np.maximum(area,1e-12),0.)
    allowed=np.flatnonzero(fractions>=minimum_fraction)
    if len(allowed):index=int(allowed[np.argmin(abs(yaws[allowed]-current_waist))]);preference=float(yaws[index])
    else:index=int(np.argmax(fractions));preference=float(current_waist)
    return dict(preferred_waist_rad=preference,has_visible_candidate=bool(len(allowed)),candidate_bbox_fraction=float(fractions[index]),minimum_bbox_fraction=minimum_fraction,current_waist_rad=float(current_waist),scope='Projected bbox only; no occlusion or IK/path guarantee. Soft robot posture preference; camera unchanged.')
