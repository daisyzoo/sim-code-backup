"""Strict independent audit of early scene-rejected planning, with no execution.
Only the exact compact rejection/fallback tree is accepted, and only when the
original independent geometry rejects the same measured state. No planner import,
missing field synthesis, tolerance relaxation or promotion of original failures.
"""
import json,copy
import numpy as np
from audit_closed_peak_trial_lift_events import EventAudit as OriginalEventAudit

def has_compact_rejection(created):
 return created.get('interior_preference',{}).get('preferred_plan',{}).get('reason')=='current_scene_rejected'

def verify_compact_scene_rejection(audit,created,*,current,scene,step):
 assert type(step) is int and step>0 and scene['side'] in ('left','right')
 q=np.asarray(current,float);assert q.shape==(11,) and np.isfinite(q).all()
 geometry,_=audit.geometry(q,scene);assert geometry['accepted'] is False,'safe observed scene cannot claim early rejection'
 leaf=dict(accepted=False,reason='current_scene_rejected')
 expected=dict(leaf,interior_preference=dict(enabled=True,preferred_inset_m=.020,original_inset_m=.012,selected_inset_m=None,selected='original_fallback',preferred_plan=copy.deepcopy(leaf),preferred_path_checks=[],fallback_reason='preferred_endpoint_rejected',not_physical_contact_proof=True))
 metadata=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],endpoint_attempts=[],lift_attempts=[],selected='original_fallback',not_physical_contact_proof=True,fallback_reason='current_scene_rejected')
 expected=dict(expected,minimum_motion_pose=dict(metadata,parent_plan=copy.deepcopy(expected)))
 if scene['side']=='right':expected=dict(expected,box_center_preference_pose=dict(metadata,box_center_preference=True,center_weight_per_m2=400.,parent_is_same_observation_minimum_motion=True,parent_plan=copy.deepcopy(expected)))
 assert json.dumps(created,sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False),'compact rejection must exactly preserve every fallback and carry no plan/command'
 return dict(selected='original_fallback',waypoints=[],compact_scene_rejection=True,independent_observed_geometry=geometry)

class EventAudit(OriginalEventAudit):
 def verify_preference(self,created,**kwargs):
  if has_compact_rejection(created):return verify_compact_scene_rejection(self,created,**kwargs)
  return super().verify_preference(created,**kwargs)
