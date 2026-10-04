"""Source-bound rear trailing policy plus unchanged compact-scene rejection.
Independent geometry and original exact fallback tree are retained. No candidate planner.
"""
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent
_path=str(W/'rear_trailing_contact_candidate_r1')
sys.path.insert(0,_path)
try:
 from rear_trailing_contact_preparation_r1.trailing_event_audit import EventAudit as BaseEventAudit
finally:
 sys.path.remove(_path)
from audit_compact_scene_rejection import has_compact_rejection,verify_compact_scene_rejection
class EventAudit(BaseEventAudit):
 def __init__(self,repo,stage):super().__init__(repo,stage,enabled=True)
 def verify_preference(self,created,*,current,scene,step):
  if not has_compact_rejection(created):return super().verify_preference(created,current=current,scene=scene,step=step)
  if scene['side']=='left':
   assert 'rear_box_trailing_preference' not in created
   return verify_compact_scene_rejection(self,created,current=current,scene=scene,step=step)
  assert scene['side']=='right'
  m=created['rear_box_trailing_preference']
  expected=dict(version='rear_box_trailing_preference_v1',offset_m=.020,world_direction=[0.,1.,0.],original_inset_m=.020,center_weight_per_m2=400.,not_physical_contact_proof=True,step=step,observed_target_quat=scene['target_quat'])
  assert {k:v for k,v in m.items() if k!='preferred_local_xy_m'}==expected
  direction=(Rotation.from_quat(scene['target_quat']).as_matrix().T@np.array([0.,1.,0.]))[:2];length=float(np.linalg.norm(direction));assert np.isfinite(length) and length>=1e-8
  preferred=.020*direction/length;assert np.all(abs(preferred)<=np.asarray(scene['core_size'])[:2]/2-.020)
  np.testing.assert_allclose(m['preferred_local_xy_m'],preferred,atol=1e-12,rtol=0)
  return verify_compact_scene_rejection(self,{k:v for k,v in created.items() if k!='rear_box_trailing_preference'},current=current,scene=scene,step=step)
