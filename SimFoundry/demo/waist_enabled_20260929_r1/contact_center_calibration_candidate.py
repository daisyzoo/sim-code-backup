"""Unwired contact-reference proposal. Collector must separately guard/lift/recenter."""
from dataclasses import dataclass,field
import numpy as np
@dataclass
class ContactCenterCalibration:
    vertices: object
    samples: list=field(default_factory=list)
    center_local: object=None
    pending: object=None
    last_step: int=-1
    def __post_init__(self):
        v=np.asarray(self.vertices,dtype=float)
        if v.ndim!=2 or v.shape[1]!=3 or len(v)<4 or not np.isfinite(v).all():raise ValueError('Invalid hand geometry')
        self.vertices=v.copy();self.low=v.min(0);self.high=v.max(0);self.geometric_center=(self.low+self.high)/2
    def observe(self,packet,*,step,mode,side,actor,hand_xyz,hand_rotation,object_xyz,object_normal):
        if type(step) is not int or step<=self.last_step:raise ValueError('Observations must have increasing frame indices')
        gap=step!=self.last_step+1;self.last_step=step
        if self.center_local is not None:return dict(latched=True,ready=False,center_local=self.center_local.tolist(),reason='already_committed')
        self.pending=None
        if gap:self.samples.clear()
        def reject(reason):
            self.samples.clear()
            return dict(latched=False,ready=False,reason=reason,sample_count=0)
        if mode!='top_press':return reject('not_press')
        if side not in ('left','right') or actor not in ('parcel_box','mailer'):raise ValueError('Unregistered hand/actor')
        r=np.asarray(hand_rotation,dtype=float);origin=np.asarray(hand_xyz,dtype=float);target=np.asarray(object_xyz,dtype=float);n=np.asarray(object_normal,dtype=float)
        if r.shape!=(3,3) or any(x.shape!=(3,) for x in [origin,target,n]) or not all(np.isfinite(x).all() for x in [r,origin,target,n]):raise ValueError('Invalid current geometry')
        if np.max(abs(r.T@r-np.eye(3)))>1e-5 or abs(np.linalg.det(r)-1)>1e-5 or abs(np.linalg.norm(n)-1)>1e-5:raise ValueError('Unnormalized orientation')
        if packet is None or packet.get('after_action_step')!=step-1:return reject('stale_or_missing_packet')
        key='box' if actor=='parcel_box' else 'mailer';measured=np.asarray(packet['post_action_pose'][key],dtype=float)
        if measured.shape!=(3,) or not np.isfinite(measured).all() or np.max(abs(measured-target))>1e-5:return reject('post_action_pose_mismatch')
        points=[];weights=[]
        for c in packet['parcel_contacts']:
            slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
            if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
            f=np.asarray(c['force_world_N'],dtype=float)*(1 if slots[0]==1 else -1);point=np.asarray(c['position_world'],dtype=float)
            if f.shape!=(3,) or point.shape!=(3,) or not np.isfinite(f).all() or not np.isfinite(point).all():return reject('invalid_contact')
            weight=-float(f@n)
            if weight>.05:points.append(point);weights.append(weight)
        load=float(sum(weights))
        if not .3<load<30:return reject('no_stable_normal_load')
        cop=np.average(points,axis=0,weights=weights);local=r.T@(cop-origin)
        if np.any(local<self.low-.003) or np.any(local>self.high+.003):return reject('centroid_outside_hand_bounds')
        tangent=(np.eye(3)-np.outer(n,n))@(r@(local-self.geometric_center))
        if np.linalg.norm(tangent)>.08:return reject('reference_shift_over_80mm')
        self.samples.append(local);self.samples=self.samples[-3:];center=np.median(self.samples,axis=0);scatter=float(np.max(np.linalg.norm(np.asarray(self.samples)-center,axis=1)))
        ready=len(self.samples)==3 and scatter<=.001
        if ready:self.pending=center.copy()
        return dict(latched=False,ready=ready,reason='three_consistent_loaded_press_samples' if ready else 'collecting',sample_count=len(self.samples),normal_load_n=load,centroid_world=cop.tolist(),centroid_local=local.tolist(),candidate_center_local=center.tolist(),scatter_m=scatter,tangent_reference_shift_m=float(np.linalg.norm(tangent)))
    def commit(self):
        if self.pending is None or self.center_local is not None:raise ValueError('No fresh proposal to commit')
        self.center_local=self.pending.copy();self.pending=None
        return self.center_local.copy()
