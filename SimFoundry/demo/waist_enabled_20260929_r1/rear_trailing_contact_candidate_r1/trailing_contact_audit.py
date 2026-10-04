"""Independent preference binding: recompute direction from observed quaternion.
No candidate planner imports. All original geometry/selection/cost checks retained.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from trailing_offset_audit_base import PlanAudit as OffsetAudit
from audit_box_center_preference_plan import PlanAudit as OriginalAudit
class PlanAudit(OffsetAudit):
 def __init__(self,root,stage,*,enabled):
  if type(enabled) is not bool:raise ValueError('Explicit audit policy required')
  super().__init__(root,stage);self.enabled=enabled;self.disabled_audit=OriginalAudit(root,stage)
 def verify_preference(self,created,*,current,scene,step):
  if not self.enabled:
   assert 'rear_box_trailing_preference' not in created
   return self.disabled_audit.verify_preference(created,current=current,scene=scene,step=step)
  m=created['rear_box_trailing_preference'];assert scene['side']=='right'
  assert m['version']=='rear_box_trailing_preference_v1' and m['offset_m']==.020 and m['world_direction']==[0.,1.,0.] and m['original_inset_m']==.020 and m['center_weight_per_m2']==400. and m['not_physical_contact_proof'] is True
  assert m['step']==step and m['observed_target_quat']==scene['target_quat']
  rotation=Rotation.from_quat(scene['target_quat']).as_matrix();direction=(rotation.T@np.array([0.,1.,0.]))[:2];length=float(np.linalg.norm(direction));assert np.isfinite(length) and length>=1e-8
  self.preferred_xy=.020*direction/length
  np.testing.assert_allclose(m['preferred_local_xy_m'],self.preferred_xy,atol=1e-12,rtol=0)
  assert np.all(abs(self.preferred_xy)<=np.asarray(scene['core_size'])[:2]/2-.020)
  original={k:v for k,v in created.items() if k!='rear_box_trailing_preference'}
  return super().verify_preference(original,current=current,scene=scene,step=step)
