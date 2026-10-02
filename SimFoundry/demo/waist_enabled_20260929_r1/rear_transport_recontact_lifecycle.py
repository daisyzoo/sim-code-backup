"""Unwired, simulator-free recovery lifecycle. Original updater/guards run first.
Outputs describe a proposed command or measured handover; caller must apply only
these explicit transitions. An active-path rejection requires stopping, never
silently falling back to a controller whose old reference no longer matches.
"""
import numpy as np
from rear_transport_recontact_plan import plan
from rear_recontact_transport_witness import witness
from recontact_tracking import propose
from simfoundry.data.projected_support_reference import projected_support_reference

class RecontactLifecycle:
    def __init__(self,*,enabled=False,maximum_ticks=240,prefer_interior=False,box_center_preference=False):
        if type(enabled) is not bool or type(maximum_ticks) is not int or maximum_ticks!=240:raise ValueError('Invalid explicit recovery configuration')
        if type(prefer_interior) is not bool:raise ValueError('Invalid interior preference')
        if type(box_center_preference) is not bool:raise ValueError('Invalid box center preference')
        self.box_center_preference=box_center_preference
        self.prefer_interior=prefer_interior
        self.enabled=enabled;self.maximum_ticks=maximum_ticks;self.active=False;self.attempted=-1;self.earliest_seed=None;self.index=0;self.ticks=0;self.ready=0;self.plan=None;self.scene=None;self.failure=None

    def stop(self,reason,**evidence):
        self.active=False;self.failure=reason
        return dict(kind='stop',requires_stop=True,reason=reason,**evidence)

    def update(self,*,step,selected,parent_mode,recontacts,guard_stop,observed_load_n,filtered_load_n,scene,current,previous_q,previous_command,decay,observed_hand_pose,observed_inactive_hand_pose,require_rear_transport=False):
        if type(require_rear_transport) is not bool:raise ValueError('Invalid rear transport requirement')
        if not self.enabled:return dict(kind='unchanged',reason='disabled')
        if self.failure is not None:return dict(kind='stop',requires_stop=True,reason=self.failure)
        if type(selected) is not bool or type(guard_stop) is not bool or type(step) is not int or type(recontacts) is not int:raise ValueError('Invalid lifecycle context')
        q=np.asarray(current,dtype=float);pose=np.asarray(observed_hand_pose,dtype=float)
        if q.shape!=(11,) or not np.isfinite(q).all() or pose.shape!=(4,4) or not np.isfinite(pose).all():raise ValueError('Invalid measured state/pose')
        inactive_pose=np.asarray(observed_inactive_hand_pose,dtype=float)
        inactive_nominal=scene.guard.model.fk(scene.inactive,q)[0]
        if inactive_pose.shape!=(4,4) or not np.isfinite(inactive_pose).all() or np.max(abs(inactive_pose-inactive_nominal))>1e-4:raise ValueError('Inactive measured hand pose differs from q model')
        nominal=scene.guard.model.fk(scene.side,q)[0]
        if np.max(abs(nominal[:3,3]-pose[:3,3]))>1e-4 or np.max(abs(nominal[:3,:3]-pose[:3,:3]))>1e-4:raise ValueError('Measured hand pose differs from actual q model')
        if not np.isfinite(observed_load_n) or not np.isfinite(filtered_load_n):raise ValueError('Nonfinite measured contact')
        unloaded=observed_load_n==0. and 0.<=filtered_load_n<=.05
        eligible=bool(selected and recontacts>0 and parent_mode in ('top_cross','top_descend') and not guard_stop and unloaded)
        context=dict(step=step,selected=selected,parent_mode=parent_mode,recontacts=recontacts,guard_stop=guard_stop,observed_load_n=float(observed_load_n),filtered_load_n=float(filtered_load_n),current=q.tolist(),previous_q=np.asarray(previous_q).tolist(),previous_command=np.asarray(previous_command).tolist(),observed_hand_pose=pose.tolist(),observed_inactive_hand_pose=inactive_pose.tolist(),scene=scene.record())
        created=None
        if not self.active:
            if not eligible or recontacts==self.attempted:return dict(kind='unchanged',reason='not_new_eligible_recovery',context=context)
            vertices=scene.guard.model.vertices[scene.side]
            if np.min((vertices@pose[:3,:3].T+pose[:3,3])[:,2])<.84:return dict(kind='unchanged',reason='initial_hand_below_unloaded_planning_height',context=context)
            self.attempted=recontacts
            if self.earliest_seed is None:self.earliest_seed=(step,q.copy())
            created=plan(scene,q,step=step,earlier_seed=self.earliest_seed,prefer_interior=self.prefer_interior,minimum_motion_pose=True,box_center_preference=self.box_center_preference,require_rear_transport=require_rear_transport)
            if not created['accepted']:
                if require_rear_transport:return self.stop('rear_transport_recontact_unverified',planning=created,context=context)
                return dict(kind='unchanged',reason='no_verified_endpoint',planning=created,context=context)
            self.plan=created;self.scene=scene;self.active=True;self.index=0;self.ticks=0;self.ready=0;self.require_rear_transport=require_rear_transport
        if require_rear_transport!=self.require_rear_transport:return self.stop('rear_transport_requirement_changed_during_path',context=context)
        if not eligible:return self.stop('parent_guard_phase_or_contact_changed',context=context)
        if recontacts!=self.attempted:return self.stop('recovery_count_changed_during_path',context=context)
        moved=scene.moved_since(self.scene)
        if moved['changed']:return self.stop('object_pose_changed_during_path',motion=moved,context=context)
        if self.ticks>=self.maximum_ticks:return self.stop('recontact_path_budget_exhausted',context=context)
        if float(np.max(abs(q-np.asarray(self.plan['waypoints'][self.index]))))<=.003 and self.index<len(self.plan['waypoints'])-1:self.index+=1
        waypoint=self.plan['waypoints'][self.index]
        command,record=propose(enabled=True,selected=True,mode='top_cross',recontacts=recontacts,observed_load_n=observed_load_n,filtered_load_n=filtered_load_n,current=q,previous_q=previous_q,previous_command=previous_command,waypoint=waypoint,decay=decay,guard=scene.guard,scene_check=scene.check)
        if command is None:return self.stop('no_verified_recontact_command',proposal=record,context=context)
        self.ticks+=1
        # Advance on measured state only. Predicted arrival cannot trigger handover.
        endpoint_close=float(np.max(abs(q-np.asarray(self.plan['endpoint']))))<=.003
        vertices=scene.guard.model.vertices[scene.side];R=pose[:3,:3];points=(vertices@R.T+pose[:3,3]-scene.target)@scene.rotation;ix=int(points[:,2].argmin());point=points[ix]
        physical_ready=bool(endpoint_close and np.min(scene.core[:2]/2-abs(point[:2]))>=.01 and .004<=point[2]-scene.core[2]/2<=.01 and np.all(q>=scene.guard.lower-2e-7) and np.all(q<=scene.guard.upper+2e-7) and scene.check(q)['accepted'])
        self.ready=self.ready+1 if physical_ready else 0
        result=dict(kind='command',command=command.tolist(),proposal=record,context=context,waypoint_index=self.index,ticks=self.ticks,measured_ready_count=self.ready,planning=created)
        if self.ready>=3:
            if require_rear_transport:
                measured_witness=witness(scene,q)
                if not measured_witness['accepted']:return self.stop('measured_rear_transport_unverified',witness=measured_witness,context=context)
                result['rear_transport_handover_witness']=measured_witness
            center=vertices[ix];reference=projected_support_reference(vertices,R,scene.rotation[:,2],center_local=center)
            measured=pose[:3,3]+R@reference['reference_local'];local=scene.rotation.T@(measured-scene.target)
            assert np.min(scene.core[:2]/2-abs(local[:2]))>=.01-1e-9
            result.update(kind='handover',captured_inactive_anchor_world=(inactive_pose[:3,3]+inactive_pose[:3,:3]@np.array([.20,0,.007])).tolist(),captured_center_local=center.tolist(),selected_surface_local_xy=local[:2].tolist(),captured_normal_local_up=(R.T@np.array([0.,0.,1.])).tolist(),reference={k:reference[k].tolist() for k in ('reference_local','center_local','lowest_vertex_local','world_normal')},observed_support_xyz=measured.tolist(),handover_scope='Current measured pose/real lowest vertex; caller must reset press/load/XY bookkeeping and replace normal anchor explicitly.')
            self.active=False
        return result
