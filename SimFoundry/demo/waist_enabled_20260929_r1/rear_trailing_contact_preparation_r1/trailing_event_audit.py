"""Independent bilateral recovery audit with original lift/combined240 budget.
Only right-box preference math changes. Imports no candidate controller/solver.
The explicit policy is provided by a source-bound caller, never by event metadata.
"""
from trailing_contact_audit import PlanAudit as TrailingPlanAudit
from audit_box_center_preference_events import EventAudit as OriginalPreferenceEvent
from audit_box_entry_lift_events_measured import EventAudit as OriginalCombinedEvent
class BilateralPlanAudit(TrailingPlanAudit):
    def verify_preference(self,created,*,current,scene,step):
        if scene['side']=='left':
            assert 'box_center_preference_pose' not in created
            assert 'rear_box_trailing_preference' not in created
            return self.original_plan_audit.verify_preference(created,current=current,scene=scene,step=step)
        assert scene['side']=='right' and 'box_center_preference_pose' in created
        return super().verify_preference(created,current=current,scene=scene,step=step)
class BilateralEventAudit(BilateralPlanAudit):
    verify=OriginalPreferenceEvent.verify
class EventAudit(OriginalCombinedEvent):
    def __init__(self,root,stage,*,enabled):
        super().__init__(root,stage)
        self.original=BilateralEventAudit(root,stage,enabled=enabled)
        self.hand=self.original.hand
