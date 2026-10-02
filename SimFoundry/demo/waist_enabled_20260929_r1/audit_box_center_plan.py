"""Explicit per-side independent plan verification for box-only preference.
Right-side rear recovery must carry center evidence; left retains original plan.
"""
from audit_box_center_preference_plan import PlanAudit as CenterPlanAudit
class PlanAudit(CenterPlanAudit):
 def verify_preference(self,created,*,current,scene,step):
  if scene['side']=='left':
   assert 'box_center_preference_pose' not in created,'Center preference applied to bag'
   return self.original_plan_audit.verify_preference(created,current=current,scene=scene,step=step)
  assert scene['side']=='right' and 'box_center_preference_pose' in created,'Missing box center plan evidence'
  return super().verify_preference(created,current=current,scene=scene,step=step)
