"""Unwired measured clearance preparation for the original front-bag lifecycle.
Preparation commands share the original 240-tick budget. A commanded preparation
commits the path: loss of original guards, continuity or geometry stops it.
Predicted headroom never starts recovery; only the next measured q can do so.
No parcel/anchor mutation. Requires runtime, final-command and independent audits.
"""
import numpy as np
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from front_initial_center_plan import checked_scene
from inactive_clearance_proposal import propose

class InactiveClearanceLifecycle(FrontRecontactCenterLifecycle):
    def __init__(self, *, recontact_index, enabled=False, maximum_ticks=240):
        super().__init__(recontact_index=recontact_index, enabled=enabled, maximum_ticks=maximum_ticks)
        self.preparing = False
        self.preparation_ticks = 0
        self.preparation_scene = None

    def update(self, **c):
        if not self.enabled or self.failure is not None or self.finished:
            return super().update(**c)
        if self.active and not self.preparing:
            return super().update(**c)
        scene=c['scene']; q=np.asarray(c['current'],float)
        if q.shape!=(11,) or not np.isfinite(q).all():raise ValueError('Invalid measured upper11')
        if type(c['selected']) is not bool or type(c['guard_stop']) is not bool or type(c['step']) is not int or c['step']<1 or type(c['recontacts']) is not int:
            raise ValueError('Invalid measured preparation context')
        eligible=(c['selected'] and scene.side=='left' and c['recontacts']==self.recontact_index and c['parent_mode'] in ('top_cross','top_descend') and not c['guard_stop'])
        if not np.isfinite([c['observed_load_n'],c['filtered_load_n']]).all():raise ValueError('Nonfinite measured contact')
        unloaded=c['observed_load_n']==0. and 0.<=c['filtered_load_n']<=.05
        if self.preparing and (not eligible or not unloaded):
            return self.stop('clearance_preparation_guard_phase_or_contact_changed')
        if not eligible or not unloaded or self.attempted:
            return super().update(**c)
        for side,key in [(scene.side,'observed_hand_pose'),(scene.inactive,'observed_inactive_hand_pose')]:
            pose=np.asarray(c[key],float)
            if pose.shape!=(4,4) or not np.isfinite(pose).all() or np.max(abs(pose-scene.guard.model.fk(side,q)[0]))>1e-4:
                raise ValueError('Measured hand pose differs from actual q model')
        geometry=checked_scene(scene,q)
        if self.preparing:
            if c['step']!=self.last_step+1:return self.stop('clearance_preparation_nonconsecutive_observation')
            moved=scene.moved_since(self.preparation_scene)
            if moved['changed']:return self.stop('clearance_preparation_object_pose_changed',motion=moved)
            if not geometry['accepted']:return self.stop('clearance_preparation_original_measured_geometry_rejected',geometry=geometry)
            if self.ticks>=self.maximum_ticks:return self.stop('initial_front_path_budget_exhausted')
        if geometry['accepted'] and geometry['inactive_lowest_z_m']>=.841:
            committed=self.preparing
            self.preparing=False;self.active=False
            event=super().update(**c)
            if committed and event['kind']=='unchanged':
                return self.stop('clearance_preparation_cannot_start_original_recovery',original_event=event)
            if committed:
                event=dict(event,preparation_ticks=self.preparation_ticks,measured_clearance_transition=True)
            return event
        u,record=propose(enabled=True,selected=c['selected'],side=scene.side,mode=c['parent_mode'],counter=c['recontacts'],guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'],current=q,previous_q=c['previous_q'],previous_command=c['previous_command'],decay=c['decay'],scene=scene)
        if u is None:
            if self.preparing:return self.stop('clearance_preparation_no_verified_command',proposal=record)
            return super().update(**c)
        if self.ticks>=self.maximum_ticks:return self.stop('initial_front_path_budget_exhausted')
        if self.preparation_scene is None:self.preparation_scene=scene
        self.preparing=self.active=True
        self.last_step=c['step'];self.ticks+=1;self.preparation_ticks+=1
        context={k:c[k] for k in ['step','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']}
        for key in ['current','previous_q','previous_command','decay','observed_hand_pose','observed_inactive_hand_pose']:context[key]=np.asarray(c[key]).tolist()
        context['scene']=scene.record()
        return dict(kind='command',command=u.tolist(),proposal=record,context=context,ticks=self.ticks,preparation_ticks=self.preparation_ticks,measured_ready_count=0,phase='inactive_clearance_preparation',scope=__doc__)
