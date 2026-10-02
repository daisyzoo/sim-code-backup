"""Expert-only runtime bridge. Real measured poses/state enter the lifecycle;
causal preflight is never reused as a measured handover or parcel motion.
"""
import numpy as np
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
from front_initial_center_adapter import apply
from recontact_scene import RecontactScene


class FrontInitialCenterRuntime:
    def __init__(self, guard, side, core_size, other_size, decay):
        self.guard=guard;self.side=side
        self.core=np.array(core_size,float);self.other_size=np.array(other_size,float)
        self.decay=np.array(decay,float)
        if self.core.shape!=(3,) or self.other_size.shape!=(3,) or min(self.core)<=.024 or min(self.other_size)<=0 or not np.isfinite(np.r_[self.core,self.other_size]).all():
            raise ValueError('Invalid actual front collision geometry')
        if self.decay.shape!=(11,) or not np.isfinite(self.decay).all() or np.any(self.decay<0) or np.any(self.decay>.95):
            raise ValueError('Invalid causal response parameters')
        self.lifecycle=FrontInitialCenterLifecycle(enabled=True)
        self.center_local=None
        self.rows=[]

    def update(self, row, state, reference, *, step, current, previous_q, previous_command,
               target_xyz, target_quat, other_xyz, other_quat, observed_load_n,
               observed_hand_pose, observed_inactive_hand_pose, normal_anchor, inactive_anchor):
        scene=RecontactScene(self.guard,self.side,target_xyz,target_quat,self.core,other_xyz,other_quat,self.other_size)
        guard_stop=bool(row.get('route_stop_reason') or row.get('release_reason'))
        if 'contact_load' not in row and self.lifecycle.active:
            event=self.lifecycle.stop('missing_actual_load_record_on_active_front_path')
        else:
            event=self.lifecycle.update(step=step,selected=True,parent_mode=row['mode'],recontacts=state.recontacts,
                guard_stop=guard_stop,observed_load_n=float(observed_load_n),
                filtered_load_n=float(row.get('contact_load',{}).get('filtered_vertical_load_n',state.load.filtered_n)),
                scene=scene,current=current,previous_q=previous_q,previous_command=previous_command,decay=self.decay,
                observed_hand_pose=observed_hand_pose,observed_inactive_hand_pose=observed_inactive_hand_pose)
        event['old_normal_anchor']=None if normal_anchor is None else np.asarray(normal_anchor).tolist()
        event['old_inactive_anchor']=np.asarray(inactive_anchor).tolist()
        if event['kind']=='stop':
            self.rows.append(dict(step=step,**event))
            return row,reference,event
        result,new_reference=apply(row,state,reference,event,object_xyz=scene.target,object_rotation=scene.rotation)
        if event['kind']=='handover':
            self.center_local=np.array(event['captured_center_local'])
        event['center_local_after']=None if self.center_local is None else self.center_local.tolist()
        self.rows.append(dict(step=step,**event))
        return result,new_reference,event
