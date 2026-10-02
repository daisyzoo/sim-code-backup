"""Uninstalled graph-safe read-only substep snapshot prototype.
Only independent trace/scratch buffers are written. No solver refresh, force
application, graph recapture or controller feedback replacement occurs here.
GPU graph replay and actual runtime integration are not yet validated.
"""
import numpy as np
import warp as wp

@wp.kernel
def _reserve(enabled:wp.array[int], count:wp.array[int], ticks:wp.array[int],
             error:wp.array[int], slot:wp.array[int], kind:int, capacity:int,
             kinds:wp.array[int], stamps:wp.array[int]):
    slot[0]=-1
    if enabled[0]!=0:
        i=count[0]
        count[0]=i+1
        if i>=capacity:
            wp.atomic_max(error,0,1)
        else:
            slot[0]=i
            kinds[i]=kind
            stamps[i]=ticks[0]
        if kind==0:
            ticks[0]=ticks[0]+1

@wp.kernel
def _copy_bodies(slot:wp.array[int], ids:wp.array[int],
                 q:wp.array[wp.transform], qd:wp.array[wp.spatial_vector],
                 out_q:wp.array2d[wp.transform], out_qd:wp.array2d[wp.spatial_vector]):
    j=wp.tid()
    s=slot[0]
    if s>=0:
        out_q[s,j]=q[ids[j]]
        out_qd[s,j]=qd[ids[j]]

@wp.kernel
def _copy_contacts(slot:wp.array[int], nacon:wp.array[int],
                   geom:wp.array[wp.vec2i], world:wp.array[int],
                   mapping:wp.array2d[int], target_shapes:wp.array[int],
                   positions:wp.array[wp.vec3], forces:wp.array[wp.spatial_vector],
                   counts:wp.array[int], error:wp.array[int],
                   valid:wp.array2d[int], shapes:wp.array2d[wp.vec2i],
                   out_pos:wp.array2d[wp.vec3], out_force:wp.array2d[wp.spatial_vector],
                   contact_capacity:int):
    j=wp.tid()
    s=slot[0]
    if s>=0:
        valid[s,j]=0
        if j==0:
            counts[s]=nacon[0]
            if nacon[0]<0 or nacon[0]>contact_capacity:
                wp.atomic_max(error,0,2)
        if j<nacon[0]:
            wi=world[j]
            g=geom[j]
            if wi<0 or wi>=mapping.shape[0] or g[0]<0 or g[1]<0 or g[0]>=mapping.shape[1] or g[1]>=mapping.shape[1]:
                wp.atomic_max(error,0,3)
            else:
                a=mapping[wi,g[0]]
                b=mapping[wi,g[1]]
                if a<0 or b<0 or a>=target_shapes.shape[0] or b>=target_shapes.shape[0]:
                    wp.atomic_max(error,0,4)
                elif target_shapes[a]!=0 or target_shapes[b]!=0:
                    valid[s,j]=1
                    shapes[s,j]=wp.vec2i(a,b)
                    out_pos[s,j]=positions[j]
                    out_force[s,j]=forces[j]

class SubstepBuffers:
    """Fixed buffers; capture enqueues kernels and does not read device values.

    kind0 samples immediately before one solver substep, kind1 after the last
    substep of a manager step. Boundary duplicates are explicit in tick stamps.
    First pre-sample forces belong to the preceding control boundary; callers
    must exclude them from integration of the new control interval.
    """
    def __init__(self, *, device, body_ids, shape_is_target, contact_capacity, capacity=40):
        if type(capacity) is not int or capacity<2 or type(contact_capacity) is not int or contact_capacity<1:
            raise ValueError('Invalid fixed capacity')
        ids=np.asarray(body_ids,dtype=np.int32);mask=np.asarray(shape_is_target,dtype=np.int32)
        if ids.ndim!=1 or len(ids)!=2 or len(set(ids.tolist()))!=2 or np.any(ids<0):raise ValueError('Exactly two distinct parcel body IDs required')
        if mask.ndim!=1 or not len(mask) or not np.all(np.isin(mask,[0,1])):raise ValueError('Invalid parcel shape mask')
        self.device=device;self.capacity=capacity;self.contact_capacity=contact_capacity;self._max_body_id=int(ids.max())
        self.ids=wp.array(ids,dtype=int,device=device);self.mask=wp.array(mask,dtype=int,device=device)
        for name in ['enabled','count','ticks','error','slot']:setattr(self,name,wp.zeros(1,dtype=int,device=device))
        for name in ['kinds','stamps','counts']:setattr(self,name,wp.zeros(capacity,dtype=int,device=device))
        self.q=wp.zeros((capacity,2),dtype=wp.transform,device=device);self.qd=wp.zeros((capacity,2),dtype=wp.spatial_vector,device=device)
        self.valid=wp.zeros((capacity,contact_capacity),dtype=int,device=device)
        self.shapes=wp.zeros((capacity,contact_capacity),dtype=wp.vec2i,device=device)
        self.positions=wp.zeros((capacity,contact_capacity),dtype=wp.vec3,device=device)
        self.forces=wp.zeros((capacity,contact_capacity),dtype=wp.spatial_vector,device=device)
        self._open=False;self.action_step=None

    def begin(self,action_step):
        if self._open or type(action_step) is not int or action_step<0:raise ValueError('Invalid/new control interval required')
        self.enabled.zero_();self.count.zero_();self.ticks.zero_();self.error.zero_()
        self.action_step=action_step;self._open=True
        self.enabled.assign(np.array([1],dtype=np.int32))

    def capture(self,kind,*,state_q,state_qd,nacon,geom,world,mapping,positions,world_forces):
        if type(kind) is not int or kind not in (0,1):raise ValueError('Unsupported callback kind')
        # All checks here use immutable host metadata, not device values.
        if len(state_q.shape)!=1 or state_q.shape!=state_qd.shape or self._max_body_id>=state_q.shape[0]:raise ValueError('State arrays must have matching body dimensions')
        if geom.shape[0]<self.contact_capacity or world.shape[0]<self.contact_capacity or positions.shape[0]<self.contact_capacity or world_forces.shape[0]<self.contact_capacity:raise ValueError('Input contact capacity too small')
        wp.launch(_reserve,dim=1,inputs=[self.enabled,self.count,self.ticks,self.error,self.slot,kind,self.capacity,self.kinds,self.stamps],device=self.device)
        wp.launch(_copy_bodies,dim=2,inputs=[self.slot,self.ids,state_q,state_qd,self.q,self.qd],device=self.device)
        wp.launch(_copy_contacts,dim=self.contact_capacity,inputs=[self.slot,nacon,geom,world,mapping,self.mask,positions,world_forces,self.counts,self.error,self.valid,self.shapes,self.positions,self.forces,self.contact_capacity],device=self.device)

    def finish(self,*,expected_substeps,expected_manager_steps):
        if not self._open:raise ValueError('No open interval')
        self.enabled.zero_();self._open=False
        n=int(self.count.numpy()[0]);err=int(self.error.numpy()[0]);ticks=int(self.ticks.numpy()[0])
        if err or n>self.capacity:raise ValueError(f'Invalid snapshot buffers: error={err},count={n}')
        if type(expected_substeps) is not int or type(expected_manager_steps) is not int or min(expected_substeps,expected_manager_steps)<1:raise ValueError('Explicit positive observed schedule required')
        kinds=self.kinds.numpy()[:n];stamps=self.stamps.numpy()[:n]
        if ticks!=expected_substeps or np.sum(kinds==0)!=expected_substeps or np.sum(kinds==1)!=expected_manager_steps:raise ValueError('Missing or extra substep/manager observations')
        if n<2 or kinds[0]!=0 or kinds[-1]!=1 or stamps[0]!=0 or stamps[-1]!=expected_substeps or not np.array_equal(stamps[kinds==0],np.arange(expected_substeps)):raise ValueError('Invalid callback ordering')
        if expected_substeps%expected_manager_steps:raise ValueError('Nonuniform manager schedule')
        per_manager=expected_substeps//expected_manager_steps
        expected_kinds=[];expected_stamps=[]
        for start in range(0,expected_substeps,per_manager):
            expected_kinds.extend([0]*per_manager+[1]);expected_stamps.extend(list(range(start,start+per_manager))+[start+per_manager])
        if not np.array_equal(kinds,expected_kinds) or not np.array_equal(stamps,expected_stamps):raise ValueError('Invalid exact manager/substep ordering')
        poses=self.q.numpy()[:n];velocities=self.qd.numpy()[:n];positions=self.positions.numpy()[:n];forces=self.forces.numpy()[:n];valid=self.valid.numpy()[:n].astype(bool)
        if not all(np.isfinite(x).all() for x in [poses,velocities,positions[valid],forces[valid]]):raise ValueError('Nonfinite physical observation')
        return dict(action_step=self.action_step,kinds=kinds,substep_stamps=stamps,body_q=poses,body_qd=velocities,solved_contact_counts=self.counts.numpy()[:n],valid=valid,shapes=self.shapes.numpy()[:n],positions=positions,forces_world=forces,scope='Read-only independent buffers. Tick0 precedes current action integration. Duplicate manager boundaries remain explicit.',training_ready=False)
