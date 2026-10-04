"""Uninstalled front-family candidate with transactional interval ownership.
Geometry comes from the same native update inputs, never the caller's scalar
margin. Outer guards consume the interval without inventing a base loss update.
Original native route transitions may change phase before the loss predicate.
"""
from dataclasses import dataclass,field
import math
from contact_window_evidence_v2 import summarize,loss_counter_observation
from window_initial_center_cop_v2 import FrontCopRouteState
from simfoundry.data.top_contact_bypass import rotation_xyzw

@dataclass
class WindowFrontCopRouteState(FrontCopRouteState):
    contact_window_enabled: bool=False
    contact_window_selected_front: bool=False
    _window_pending: object=field(default=None,init=False,repr=False)
    _window_active: object=field(default=None,init=False,repr=False)
    _window_last_step: int=field(default=0,init=False,repr=False)
    window_last_disposition: object=field(default=None,init=False,repr=False)

    def observe_contact_window(self,*,action_step,after_action_step,vertical_load_n,instantaneous_load_n):
        if self.contact_window_enabled is not True:raise ValueError('Explicit enabled candidate required')
        if self._window_pending is not None or self._window_active is not None or action_step<=self._window_last_step:raise ValueError('Advancing interval must be consumed once')
        values=tuple(vertical_load_n)
        summary=summarize(action_step=action_step,after_action_step=after_action_step,vertical_load_n=values,instantaneous_load_n=instantaneous_load_n)
        self._window_pending=dict(summary=summary,values=values,observed_phase=self.top_mode)
        self._window_last_step=action_step

    def _window_loss_contact(self,load_n):
        packet=self._window_active
        if packet is None or packet['evidence'] is not None:raise ValueError('Exactly one bound loss update allowed')
        if self.top_mode!='top_push' or abs(load_n-packet['summary']['instantaneous_load_n'])>1e-5:raise ValueError('Native loss phase and current force must match')
        summary=packet['summary']
        evidence=loss_counter_observation(enabled=True,selected_front=self.contact_window_selected_front,mode=self.top_mode,action_step=summary['action_step'],after_action_step=summary['after_action_step'],vertical_load_n=packet['values'],instantaneous_load_n=load_n,current_support_core_margin_m=packet['geometry']['current_support_core_margin_m'])
        packet['evidence']=evidence
        return evidence['contact_evidence_for_loss_counter']

    def update(self,palm,target,obstacle,target_radius_x,obstacle_radius_x,*,tip,quat,obstacle_quat,control_offset_local,load_n,hand_obstacle_gap_m,slip_contact=None,**kwargs):
        if type(self.contact_window_enabled) is not bool or type(self.contact_window_selected_front) is not bool:raise ValueError('Explicit boolean flags required')
        call=dict(tip=tip,quat=quat,obstacle_quat=obstacle_quat,control_offset_local=control_offset_local,load_n=load_n,hand_obstacle_gap_m=hand_obstacle_gap_m,slip_contact=slip_contact,**kwargs)
        if not self.contact_window_enabled:
            if self._window_pending is not None or self._window_active is not None:raise ValueError('Cannot disable with outstanding interval')
            return super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,**call)
        p=self._window_pending
        if p is None or self._window_active is not None:raise ValueError('Fresh interval required')
        s=p['summary']
        if p['observed_phase']!=self.top_mode or not math.isfinite(load_n) or abs(load_n-s['instantaneous_load_n'])>1e-5:raise ValueError('Observation phase/force changed before outer update')
        if getattr(self.load,'_last_action_step',None)!=s['action_step']:raise ValueError('Pressure and loss interval mismatch')
        core=self.edge_core_size
        if core is None or len(core)!=3 or not all(math.isfinite(float(v)) and v>0 for v in core):raise ValueError('Actual collision core required')
        if len(target)!=3 or len(tip)!=3 or not all(math.isfinite(float(v)) for v in [*target,*tip]):raise ValueError('Finite current geometry required')
        rot=rotation_xyzw(quat);local=tuple(sum(rot[i][j]*(tip[i]-target[i]) for i in range(3)) for j in range(3))
        geometry=dict(target_xyz=list(target),support_xyz=list(tip),target_quat_xyzw=list(quat),actual_core_xyz=list(core),support_local_xyz=list(local),current_support_core_margin_m=min(core[i]/2-abs(local[i]) for i in (0,1)),scope='Same native update support point; not current COP or whole-hand collision certificate')
        self._window_pending=None;self._window_active=dict(p,geometry=geometry,evidence=None)
        try:
            row=super().update(palm,target,obstacle,target_radius_x,obstacle_radius_x,**call)
            disposition=dict(action_step=s['action_step'],observed_phase=p['observed_phase'],final_phase=self.top_mode,output_mode=row['mode'],geometry=geometry,evidence=self._window_active['evidence'],disposition='loss_counter_evaluated' if self._window_active['evidence'] is not None else 'original_guard_or_nonpush_no_loss_update',training_ready=False)
            self.window_last_disposition=disposition;row['contact_window_interval']=disposition
            return row
        except Exception as exc:
            self.window_last_disposition=dict(action_step=s['action_step'],disposition='native_update_exception_consumed',error=type(exc).__name__,training_ready=False)
            raise
        finally:self._window_active=None
