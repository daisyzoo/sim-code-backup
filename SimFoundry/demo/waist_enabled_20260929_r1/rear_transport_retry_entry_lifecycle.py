"""Unwired default-off entry lift + unchanged center recontact lifecycle.
The lifted pose is measured afresh before the original planner is called.
Original240 command-tick budget is shared by both phases; no extra episode time.
Existing command adapter can hold top_cross for lift commands without captures.
A future versioned audit must distinguish entry_lift_phase before integration.
"""
import numpy as np
from rear_transport_retry_lifecycle import RecontactLifecycle as OriginalLifecycle
from box_recovery_entry_lift import EntryLift

class RecontactLifecycle:
    def __init__(self,*,enabled=False,maximum_ticks=240,prefer_interior=False,box_center_preference=False,entry_lift=False,transport_feasible_retry=False):
        if type(transport_feasible_retry) is not bool:raise ValueError('Explicit retry flag required')
        if type(entry_lift) is not bool:raise ValueError('Invalid entry lift switch')
        if entry_lift and not (enabled and prefer_interior and box_center_preference):raise ValueError('Entry lift requires selected center lifecycle')
        self.original=OriginalLifecycle(enabled=enabled,maximum_ticks=maximum_ticks,prefer_interior=prefer_interior,box_center_preference=box_center_preference,transport_feasible_retry=transport_feasible_retry)
        self.lift=EntryLift(enabled=entry_lift);self.entry_lift=entry_lift;self.total_ticks=0;self.total_recontacts=None;self.budget_failure=None;self.pending=False;self.pending_scene=None;self.pending_last=None

    @property
    def active(self):return self.original.active or self.lift.active or self.pending

    @property
    def failure(self):return self.budget_failure or self.lift.failure or self.original.failure

    @property
    def earliest_seed(self):return self.original.earliest_seed

    @earliest_seed.setter
    def earliest_seed(self,value):self.original.earliest_seed=value

    def update(self,**inputs):
        require_rear_transport=inputs.pop("require_rear_transport",False)
        if type(require_rear_transport) is not bool:raise ValueError("Invalid rear transport requirement")
        if not self.entry_lift:return self.original.update(**inputs,require_rear_transport=require_rear_transport)
        if self.failure is not None:return dict(kind='stop',requires_stop=True,reason=self.failure)
        n=inputs['recontacts']
        if not self.active and n!=self.total_recontacts:self.total_recontacts=n;self.total_ticks=0
        if self.total_ticks>=240 and (self.active or (n in self.lift.finished and n!=self.original.attempted)):
            self.budget_failure='combined_recovery_budget_exhausted'
            self.original.active=False;self.lift.active=False;self.pending=False
            return dict(kind='stop',requires_stop=True,reason=self.failure,recovery_total_ticks=self.total_ticks)
        if self.pending:
            eligible=(inputs['scene'].side=='right' and inputs['selected'] is True and inputs['parent_mode'] in ('top_cross','top_descend') and inputs['guard_stop'] is False and inputs['observed_load_n']==0 and 0<=inputs['filtered_load_n']<=.05)
            changed=inputs['scene'].moved_since(self.pending_scene)['changed']
            prior=self.pending_last
            coherent=(inputs['step']==prior['step']+1 and np.max(abs(np.asarray(inputs['previous_q'])-prior['q']))<=1e-7 and np.array_equal(inputs['previous_command'],prior['command']))
            if not eligible or n!=self.total_recontacts or changed or not coherent:
                self.budget_failure='entry_lift_to_recontact_context_changed';self.pending=False
                return dict(kind='stop',requires_stop=True,reason=self.failure,recovery_total_ticks=self.total_ticks)
        event=None
        rejected_lift=None
        if self.lift.active or (not self.original.active and n!=self.original.attempted):
            lifted=self.lift.update(**inputs)
            if lifted['kind']=='stop':return lifted
            if lifted.get('planning') is not None and not lifted['planning']['accepted']:rejected_lift=lifted
            if lifted['kind'] in ('lift_command','lift_ready'):
                # No contact capture here: keep parent recovery and its old anchors.
                event=dict(lifted,kind='command',entry_lift_phase=lifted['kind'])
                if lifted['kind']=='lift_ready':
                    self.pending=True;self.pending_scene=inputs['scene'];self.pending_last=dict(step=inputs['step'],q=np.array(inputs['current']),command=np.array(lifted['command']))
        if event is None:
            event=self.original.update(**inputs,require_rear_transport=require_rear_transport)
            if self.pending:
                if event['kind'] not in ('command','handover'):
                    self.budget_failure='no_verified_recontact_after_entry_lift';self.pending=False
                    return dict(kind='stop',requires_stop=True,reason=self.failure,original_event=event,recovery_total_ticks=self.total_ticks)
                self.pending=False
            if rejected_lift is not None:event=dict(event,rejected_entry_lift_attempt=rejected_lift)
        if event['kind'] in ('command','handover'):
            self.total_ticks+=1
            event=dict(event,recovery_total_ticks=self.total_ticks)
        return event
