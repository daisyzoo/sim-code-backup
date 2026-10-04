"""Default-off front-bag recovery bridge; no action/parcel writes.
One lifecycle per real consecutive parent recovery counter. Caller keeps all
parent guards, applies final command checks, and installs captures only on an
actual lifecycle handover. Failed active paths stop; they never fall back.
"""
import numpy as np
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from front_recontact_center_adapter import apply
from recontact_scene import RecontactScene

class FrontRecontactCenterRuntime:
    def __init__(self, guard, side, core_size, other_size, decay, *, enabled=False):
        if type(enabled) is not bool or side not in ('left','right'):
            raise ValueError('Expected explicit enabled and hand side')
        self.enabled=enabled;self.guard=guard;self.side=side
        self.core=np.array(core_size,float);self.other_size=np.array(other_size,float);self.decay=np.array(decay,float)
        if self.core.shape!=(3,) or self.other_size.shape!=(3,) or min(self.core)<=.024 or min(self.other_size)<=0 or not np.isfinite(np.r_[self.core,self.other_size]).all():
            raise ValueError('Invalid actual recovery collision geometry')
        if self.decay.shape!=(11,) or not np.isfinite(self.decay).all() or np.any(self.decay<0) or np.any(self.decay>.95):
            raise ValueError('Invalid causal response parameters')
        self.lifecycle=None;self.last_counter=0;self.center_local=None;self.failure=None;self.rows=[]

    def update(self,row,state,reference,*,selected,step,current,previous_q,previous_command,
               target_xyz,target_quat,other_xyz,other_quat,observed_load_n,
               observed_hand_pose,observed_inactive_hand_pose,normal_anchor,inactive_anchor):
        if type(selected) is not bool:raise ValueError('Expected explicit route selection')
        if not self.enabled:return row,reference,dict(kind='unchanged',reason='disabled')
        def finish(event,scene=None):
            event=dict(event)
            event['old_normal_anchor']=None if normal_anchor is None else np.asarray(normal_anchor).tolist()
            event['old_inactive_anchor']=np.asarray(inactive_anchor).tolist()
            if event['kind']=='stop':self.failure=event['reason']
            result,new_reference=row,reference
            if event['kind'] in ('command','handover'):
                if scene is None:raise ValueError('Missing observed recovery scene')
                result,new_reference=apply(row,state,reference,event,object_xyz=scene.target,object_rotation=scene.rotation)
            if event['kind']=='handover':self.center_local=np.asarray(event['captured_center_local']).copy()
            event['real_recontact_index']=self.last_counter
            event['center_local_after']=None if self.center_local is None else self.center_local.tolist()
            self.rows.append(dict(step=step,**event))
            return result,new_reference,event
        def stop(reason):
            if self.lifecycle is not None and self.lifecycle.active:self.lifecycle.stop(reason)
            return finish(dict(kind='stop',requires_stop=True,reason=reason))
        if self.failure is not None:return stop(self.failure)
        if not selected or self.side!='left':
            if self.lifecycle is not None and self.lifecycle.active:return stop('selected_front_bag_path_changed')
            return finish(dict(kind='unchanged',reason='not_selected_front_bag'))
        counter=state.recontacts
        if type(counter) is not int or counter<0:return stop('invalid_parent_recontact_counter')
        if counter<self.last_counter or counter>self.last_counter+1:return stop('nonconsecutive_parent_recontact_counter')
        if counter==0:return finish(dict(kind='unchanged',reason='first_contact_remains_original'))
        if row.get('recontacts',counter)!=counter:return stop('row_parent_recontact_counter_disagrees')
        if counter!=self.last_counter:
            if self.lifecycle is not None and self.lifecycle.active:return stop('parent_recovery_changed_during_active_path')
            self.lifecycle=FrontRecontactCenterLifecycle(enabled=True,recontact_index=counter)
            self.last_counter=counter
        if self.lifecycle is None:return stop('missing_recovery_lifecycle')
        guard_stop=bool(row.get('route_stop_reason') or row.get('release_reason'))
        if guard_stop:
            if self.lifecycle.active:return stop('parent_guard_during_active_recovery')
            return finish(dict(kind='unchanged',reason='parent_guard_has_precedence'))
        if 'contact_load' not in row:
            if self.lifecycle.active:return stop('missing_actual_load_record_on_active_recovery')
            return finish(dict(kind='unchanged',reason='no_measured_load_record'))
        scene=RecontactScene(self.guard,self.side,target_xyz,target_quat,self.core,other_xyz,other_quat,self.other_size)
        event=self.lifecycle.update(step=step,selected=True,parent_mode=row['mode'],recontacts=counter,guard_stop=False,
            observed_load_n=float(observed_load_n),filtered_load_n=float(row['contact_load']['filtered_vertical_load_n']),
            scene=scene,current=current,previous_q=previous_q,previous_command=previous_command,decay=self.decay,
            observed_hand_pose=observed_hand_pose,observed_inactive_hand_pose=observed_inactive_hand_pose)
        return finish(event,scene)
