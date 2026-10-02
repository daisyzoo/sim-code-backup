"""Unwired, default-off measured lift to the unchanged recontact entry height.
Only right-hand, measured-unloaded recovery. No normal-anchor capture or push.
Caller must hold the parent in recovery and count these ticks in its ORIGINAL
240-tick total recovery and1200-frame episode budget before integrating this.
"""
import numpy as np
from box_center_preference_plan import lift_endpoint,interpolate
from recontact_tracking import propose

class EntryLift:
    def __init__(self,*,enabled=False):
        if type(enabled) is not bool:raise ValueError('Expected explicit switch')
        self.enabled=enabled;self.active=False;self.failure=None;self.finished=set();self.ticks=0;self.ready=0;self.index=0;self.last=None

    def stop(self,reason,**evidence):
        self.active=False;self.failure=reason
        return dict(kind='stop',requires_stop=True,reason=reason,**evidence)

    def update(self,*,step,selected,parent_mode,recontacts,guard_stop,observed_load_n,filtered_load_n,scene,current,previous_q,previous_command,decay,observed_hand_pose,observed_inactive_hand_pose):
        if not self.enabled:return dict(kind='unchanged',reason='disabled')
        if self.failure is not None:return dict(kind='stop',requires_stop=True,reason=self.failure)
        if type(selected) is not bool or type(guard_stop) is not bool or type(step) is not int or type(recontacts) is not int:raise ValueError('Invalid lift context')
        q,qp,previous,pose,ip=[np.asarray(v,float) for v in [current,previous_q,previous_command,observed_hand_pose,observed_inactive_hand_pose]]
        if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,qp,previous]) or any(v.shape!=(4,4) or not np.isfinite(v).all() for v in [pose,ip]):raise ValueError('Invalid measured lift state')
        if not np.isfinite(observed_load_n) or not np.isfinite(filtered_load_n):raise ValueError('Nonfinite load')
        if np.max(abs(scene.guard.model.fk(scene.side,q)[0]-pose))>1e-4 or np.max(abs(scene.guard.model.fk(scene.inactive,q)[0]-ip))>1e-4:raise ValueError('Measured lift pose differs from q')
        z=float(np.min((scene.guard.model.vertices[scene.side]@pose[:3,:3].T+pose[:3,3])[:,2]))
        eligible=bool(scene.side=='right' and selected and recontacts>0 and parent_mode in ('top_cross','top_descend') and not guard_stop and observed_load_n==0 and 0<=filtered_load_n<=.05)
        context=dict(step=step,selected=selected,parent_mode=parent_mode,recontacts=recontacts,guard_stop=guard_stop,observed_load_n=float(observed_load_n),filtered_load_n=float(filtered_load_n),scene=scene.record(),current=q.tolist(),previous_q=qp.tolist(),previous_command=previous.tolist(),observed_hand_pose=pose.tolist(),observed_inactive_hand_pose=ip.tolist())
        created=None
        if not self.active:
            if not eligible or recontacts in self.finished or z>=.84:return dict(kind='unchanged',reason='not_new_height_blocked_unloaded_recovery',context=context)
            if not scene.check(q)['accepted']:return dict(kind='unchanged',reason='initial_scene_rejected',context=context)
            height=.845-scene.target[2]-scene.core[2]/2
            lift=lift_endpoint(scene,q,height)
            path=interpolate(scene,[q,np.array(lift['candidate'])]) if lift['accepted'] else None
            endz=None
            if path and path['accepted']:
                T=scene.guard.model.fk(scene.side,lift['candidate'])[0];endz=float(np.min((scene.guard.model.vertices[scene.side]@T[:3,:3].T+T[:3,3])[:,2]))
            accepted=bool(path and path['accepted'] and endz>=.84)
            created=dict(step=step,start=q.tolist(),scene=scene.record(),lift=lift,path=path,endpoint_lowest_world_z_m=endz,accepted=accepted)
            if not accepted:
                self.finished.add(recontacts)
                return dict(kind='unchanged',reason='no_verified_entry_lift',planning=created,context=context)
            self.plan=created;self.scene=scene;self.recontacts=recontacts;self.active=True;self.ticks=0;self.ready=0;self.index=0;self.last=None
        if not eligible:return self.stop('parent_guard_phase_or_contact_changed',context=context)
        if recontacts!=self.recontacts:return self.stop('recovery_count_changed_during_lift',context=context)
        if scene.moved_since(self.scene)['changed']:return self.stop('object_pose_changed_during_lift',context=context)
        if self.ticks>=40:return self.stop('entry_lift_budget_exhausted',context=context)
        if self.last is not None and (step!=self.last['step']+1 or np.max(abs(qp-self.last['q']))>1e-7 or not np.array_equal(previous,self.last['command'])):return self.stop('nonconsecutive_lift_history',context=context)
        waypoints=self.plan['path']['waypoints']
        if np.max(abs(q-np.array(waypoints[self.index])))<=.003 and self.index<len(waypoints)-1:self.index+=1
        command,record=propose(enabled=True,selected=True,mode='top_cross',recontacts=recontacts,observed_load_n=observed_load_n,filtered_load_n=filtered_load_n,current=q,previous_q=qp,previous_command=previous,waypoint=waypoints[self.index],decay=decay,guard=scene.guard,scene_check=scene.check)
        if command is None:return self.stop('no_verified_entry_lift_command',proposal=record,context=context)
        self.ticks+=1
        ready=bool(z>=.84 and np.max(abs(q-np.array(self.plan['lift']['candidate'])))<=.003 and scene.check(q)['accepted'] and np.all(q>=scene.guard.lower-2e-7) and np.all(q<=scene.guard.upper+2e-7))
        self.ready=self.ready+1 if ready else 0
        out=dict(kind='lift_ready' if self.ready>=3 else 'lift_command',command=command.tolist(),proposal=record,context=context,planning=created,waypoint_index=self.index,ticks=self.ticks,measured_ready_count=self.ready,measured_lowest_world_z_m=z)
        self.last=dict(step=step,q=q.copy(),command=command.copy())
        if self.ready>=3:self.active=False;self.finished.add(recontacts)
        return out
