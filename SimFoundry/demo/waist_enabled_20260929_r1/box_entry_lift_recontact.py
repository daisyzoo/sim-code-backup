"""Unwired default-off entry lift + unchanged center recontact lifecycle.
The lifted pose is measured afresh before the original planner is called.
Original240 command-tick budget is shared by both phases; no extra episode time.
Existing command adapter can hold top_cross for lift commands without captures.
A future versioned audit must distinguish entry_lift_phase before integration.
"""
from minimum_motion_lifecycle import RecontactLifecycle as OriginalLifecycle
from box_recovery_entry_lift import EntryLift

class RecontactLifecycle:
    def __init__(self,*,enabled=False,maximum_ticks=240,prefer_interior=False,box_center_preference=False,entry_lift=False):
        if type(entry_lift) is not bool:raise ValueError('Invalid entry lift switch')
        if entry_lift and not (enabled and prefer_interior and box_center_preference):raise ValueError('Entry lift requires selected center lifecycle')
        self.original=OriginalLifecycle(enabled=enabled,maximum_ticks=maximum_ticks,prefer_interior=prefer_interior,box_center_preference=box_center_preference)
        self.lift=EntryLift(enabled=entry_lift);self.entry_lift=entry_lift;self.total_ticks=0;self.total_recontacts=None;self.budget_failure=None

    @property
    def active(self):return self.original.active or self.lift.active

    @property
    def failure(self):return self.budget_failure or self.lift.failure or self.original.failure

    @property
    def earliest_seed(self):return self.original.earliest_seed

    @earliest_seed.setter
    def earliest_seed(self,value):self.original.earliest_seed=value

    def update(self,**inputs):
        if not self.entry_lift:return self.original.update(**inputs)
        if self.failure is not None:return dict(kind='stop',requires_stop=True,reason=self.failure)
        n=inputs['recontacts']
        if not self.active and n!=self.total_recontacts:self.total_recontacts=n;self.total_ticks=0
        if self.total_ticks>=240 and (self.active or (n in self.lift.finished and n!=self.original.attempted)):
            self.budget_failure='combined_recovery_budget_exhausted'
            self.original.active=False;self.lift.active=False
            return dict(kind='stop',requires_stop=True,reason=self.failure,recovery_total_ticks=self.total_ticks)
        event=None
        if self.lift.active or (not self.original.active and n!=self.original.attempted):
            lifted=self.lift.update(**inputs)
            if lifted['kind']=='stop':return lifted
            if lifted['kind'] in ('lift_command','lift_ready'):
                # No contact capture here: keep parent recovery and its old anchors.
                event=dict(lifted,kind='command',entry_lift_phase=lifted['kind'])
        if event is None:event=self.original.update(**inputs)
        if event['kind'] in ('command','handover'):
            self.total_ticks+=1
            event=dict(event,recovery_total_ticks=self.total_ticks)
        return event
