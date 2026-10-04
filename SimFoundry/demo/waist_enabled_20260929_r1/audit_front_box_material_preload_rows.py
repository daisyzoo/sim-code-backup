"""Independent finite material-reference XY arithmetic; no candidate imports.
Caller must independently validate source, original route/COP/load/edge advice,
reference lifetime, Z and final joint commands. This helper alone admits nothing.
"""
import numpy as np

class MaterialPreloadAudit:
 def __init__(self,enabled,side):
  assert type(enabled) is bool and side in ('left','right')
  self.enabled=enabled;self.side=side;self.local=None;self.phase=None;self.preload=0.;self.count=0
 def reset(self):self.local=None;self.phase=None;self.preload=0.
 def before_row(self,row):
  e=row.get('front_box_material_preload')
  if not self.enabled:
   assert e is None;return
  inactive=self.side!='right' or row['mode']!='top_push' or not row.get('cop_slip_following',{}).get('override') or row.get('route_stop_reason') or row.get('release_reason') or row.get('terminal_position_confirmed')
  if inactive:assert e==dict(override=False,reason='parent_or_unselected');self.reset()
 def verify(self,row,*,object_xyz,rotation,observed_support,previous,goal,normal_load_n,drive_step_m,parent_xy,diagonal):
  if not self.enabled:return np.asarray(parent_xy)
  assert self.side=='right' and row['mode']=='top_push' and not row.get('route_stop_reason') and not row.get('release_reason') and not row.get('terminal_position_confirmed')
  assert normal_load_n>=.3 and .001<=drive_step_m<=.002
  e=row['front_box_material_preload'];assert e['override'] is True and e['reason']=='bounded_material_reference_preload'
  obj,R,ref,prev,goal=[np.asarray(v,float) for v in [object_xyz,rotation,observed_support,previous,goal]];assert type(row['recontacts']) is int and row['recontacts']>=0
  phase=(row['route_stage'],row['recontacts']);fresh=self.local is None or self.phase!=phase
  if fresh:self.local=R.T@(ref-obj);self.preload=0.;self.phase=phase
  self.preload=min(.012,self.preload+drive_step_m);delta=goal-obj[:2];distance=np.linalg.norm(delta);assert distance>1e-12;axis=delta/distance;anchor=obj+R@self.local;desired=anchor[:2]+axis*min(self.preload,distance);bounded=np.clip(desired,ref[:2]-.030,ref[:2]+.030);cmd=prev+np.clip(bounded-prev,-.003,.003);emitted=cmd.copy();cross=None
  if not diagonal:cross=1-(0 if row['route_stage']=='front_x' else 1);emitted[cross]=parent_xy[cross]
  expected=dict(command_xy=cmd,reference_local=self.local,preload_m=self.preload,drive_step_m=drive_step_m,anchor_world=anchor,drive_direction_xy=axis,desired_xy=desired,previous_command_xy=prev,observed_support_xyz=ref,command_delta_xy=cmd-prev,command_reference_lead_xy=cmd-ref[:2],parent_xyz=[*parent_xy,row['target_xyz'][2]],emitted_xy=emitted,preserved_z=row['target_xyz'][2])
  for key,value in expected.items():
   stored=np.asarray(e[key],float);assert stored.shape==np.asarray(value).shape and np.isfinite(stored).all();assert np.max(abs(stored-value))<=2e-6,(row['step'],key)
  assert e['captured_reference'] is fresh and e['phase']==list(phase) and e['preserved_cross_axis']==cross
  assert e['original_parent_checks_required'] is True and e['synthetic_proposal_only'] is True
  for key,value,boundary in [('desired_lead_clipped',bool(np.any(abs(bounded-desired)>1e-12)),np.min(abs(abs(desired-ref[:2])-.030))),('retained_slew_lag_outside_lead',bool(np.any(abs(cmd-ref[:2])>.030+1e-9)),np.min(abs(abs(cmd-ref[:2])-.030)))]:
   if boundary>2e-6:assert e[key] is value
  assert max(abs(emitted-prev))<=.003+2e-6;self.count+=1;return emitted
