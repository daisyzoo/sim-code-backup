"""Default-off fixed20mm world+Y trailing preference for right box recontact.
Geometry/contact/task gates unchanged. Fresh parent is same-observation input.
No contact success or training admission follows from this preference.
"""
import numpy as np
from box_center_preference_plan import plan as original_plan
from trailing_offset_solver import plan as shifted_plan
SPEC=dict(version='rear_box_trailing_preference_v1',offset_m=.020,world_direction=[0.,1.,0.],original_inset_m=.020,center_weight_per_m2=400.,not_physical_contact_proof=True)
def plan(scene,q,*,step,parent_plan,enabled=False):
 if type(enabled) is not bool:raise ValueError('Explicit trailing-preference switch required')
 if not enabled:return original_plan(scene,q,step=step,parent_plan=parent_plan)
 if scene.side!='right':raise ValueError('Trailing preference is right-box-only')
 direction=(scene.rotation.T@np.array([0.,1.,0.]))[:2];length=float(np.linalg.norm(direction))
 if not np.isfinite(length) or length<1e-8:raise ValueError('Degenerate observed plane projection')
 preferred=.020*direction/length
 created=shifted_plan(scene,q,step=step,parent_plan=parent_plan,preferred_xy=preferred)
 return dict(created,rear_box_trailing_preference=dict(SPEC,preferred_local_xy_m=preferred.tolist(),step=step,observed_target_quat=scene.record()['target_quat']))
