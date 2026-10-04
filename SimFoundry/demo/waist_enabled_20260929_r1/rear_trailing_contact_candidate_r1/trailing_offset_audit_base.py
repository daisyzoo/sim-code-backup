"""Independent causal preference and sampled piecewise-path verification.
No candidate solver/planner imports. Does not assert global optimality or real
tracking/contact; preserves original interior fallback and geometry thresholds.
"""
import numpy as np
from audit_slow_drag_plan import PlanAudit as BasePlanAudit
from audit_unloaded_wrist_prior_live import near

class PlanAudit(BasePlanAudit):
 def __init__(self,repo,stage):
  super().__init__(repo,stage)
  self.original_plan_audit=BasePlanAudit(repo,stage)
 def path(self,nodes,scene):
  expected=[]
  for a,b in zip(nodes,nodes[1:]):
   a,b=np.asarray(a,float),np.asarray(b,float);n=max(1,int(np.ceil(max(abs(b-a)/(self.limits*.25)))))
   expected.extend([np.clip(a+(b-a)*i/n,self.lo,self.hi).tolist() for i in range(1,n+1)])
  return expected,[self.geometry(x,scene)[0] for x in expected]

 def checked_path(self,stored,nodes,scene):
  expected,checks=self.path(nodes,scene);near(stored['waypoints'],expected,1e-10);assert len(stored['checks'])==len(checks)
  for actual,record in zip(checks,stored['checks']):self.compare_geometry(record,actual)
  assert stored['accepted'] is bool(checks and all(g['accepted'] for g in checks));return expected

 def verify_endpoint_attempt(self,a,q,scene):
  assert type(a['status']) is int and type(a['accepted']) is bool and type(a['iterations']) is int and 0<=a['iterations']<=220
  if a['candidate'] is None:assert not a['accepted'] and a['minimum_constraint_m'] is None and a['path'] is None;return
  x=np.asarray(a['candidate'],float);g,d=self.geometry(x,scene);other='right' if scene['side']=='left' else 'left';axis=np.linalg.eigh(np.cov(self.hand.vertices[scene['side']].T))[1][:,0];align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis)
  minimum=float(min(align**2-.8**2,*list(d['core'][:2]/2-abs(d['point'][:2])-.020),g['active_above_top_m']-.006,.007-g['active_above_top_m'],self.hand.minz(x,other)-.84,g['elbow_gap_m']-.005))
  near(a['minimum_constraint_m'],minimum,2e-8);near(a['thin_axis_alignment_abs'],align,2e-9);near(a['objective'],np.sum((x-q)**2)+400.*np.sum((d['point'][:2]-self.preferred_xy)**2),1e-9)
  valid=bool(a['status']==0 and minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=self.lo-2e-7) and np.all(x<=self.hi+2e-7));assert a['accepted'] is valid
  if valid:self.checked_path(a['path'],[q,x],scene)
  else:assert a['path'] is None

 def lift(self,a,reference,height,scene):
  near(a['height_m'],height,2e-9);assert a['xy_tolerance_m']==.002 and a['height_tolerance_m']==.001;near(a['reference'],reference,0)
  assert type(a['status']) is int and type(a['accepted']) is bool and type(a['iterations']) is int and 0<=a['iterations']<=220
  if a['candidate'] is None:assert not a['accepted'] and a['minimum_constraint_m'] is None;return
  x=np.asarray(a['candidate']);g,d=self.geometry(x,scene);_,rd=self.geometry(reference,scene);other='right' if scene['side']=='left' else 'left';minimum=float(min(*list(.002-abs(d['point'][:2]-rd['point'][:2])),g['active_above_top_m']-height,height+.001-g['active_above_top_m'],self.hand.minz(x,other)-.84,g['elbow_gap_m']-.005));near(a['minimum_constraint_m'],minimum,2e-8)
  valid=bool(a['status']==0 and minimum>=-2e-7 and g['accepted'] and np.all(x>=self.lo-2e-7) and np.all(x<=self.hi+2e-7));assert a['accepted'] is valid

 def verify_preference(self,created,*,current,scene,step):
  q=np.asarray(current,float);m=created['box_center_preference_pose'];parent=m['parent_plan'];assert scene['side']=='right' and m['box_center_preference'] is True and m['center_weight_per_m2']==400. and m['parent_is_same_observation_minimum_motion'] is True;assert m['enabled'] is True and m['alignment_abs_min']==.8 and m['preferred_inset_m']==.020 and m['seed_policy']==['original_endpoint','current_observed'] and m['not_physical_contact_proof'] is True
  # Preserve every original parent endpoint/fallback/selection check.
  self.original_plan_audit.verify_preference(parent,current=q,scene=scene,step=step)
  assert self.geometry(q,scene)[0]['accepted'];attempts=m['endpoint_attempts'];assert [a['seed'] for a in attempts]==['original_endpoint','current_observed']
  for a in attempts:self.verify_endpoint_attempt(a,q,scene)
  usable=[a for a in attempts if a['accepted'] and a['path']['accepted']];feasible=[a for a in attempts if a['accepted']]
  if usable:
   assert not m['lift_attempts'];best=min(usable,key=lambda a:a['objective']);nodes=[q.tolist(),best['candidate']];path=best['path'];route='straight'
  elif feasible:
   best=min(feasible,key=lambda a:a['objective']);end=np.array(best['candidate']);lifts=m['lift_attempts'];assert [a['height_m'] for a in lifts]==[.015,.030,.060]
   for a in lifts:
    height=a['height_m'];start_height=max(height,self.geometry(q,scene)[0]['active_above_top_m']);self.lift(a['start_lift'],q,start_height,scene);self.lift(a['end_lift'],end,height,scene);nodes=[q.tolist(),a['start_lift']['candidate'],a['end_lift']['candidate'],end.tolist()];assert a['nodes']==nodes
    if a['start_lift']['accepted'] and a['end_lift']['accepted']:self.checked_path(a['path'],nodes,scene);assert a['accepted'] is a['path']['accepted']
    else:assert a['path'] is None and a['accepted'] is False
   valid=[a for a in lifts if a['accepted']]
   if valid:
    chosen=min(valid,key=lambda a:len(a['path']['waypoints']));nodes=chosen['nodes'];path=chosen['path'];route='raised'
   else:path=None
  else:assert not m['lift_attempts'];path=None
  if path is None:
   assert m['selected']=='original_fallback' and m['fallback_reason']==('no_verified_endpoint' if not feasible else 'no_verified_nominal_path');assert {k:v for k,v in created.items() if k!='box_center_preference_pose'}==parent
   return dict(selected='original_fallback',waypoints=parent.get('waypoints',[]))
  assert m['selected']=='candidate' and m['fallback_reason'] is None and m['route']==route;assert m['nodes']==nodes and m['nominal_waypoints']==len(path['waypoints']) and m['selected_path_checks']==path['checks']
  assert created['accepted'] is True and created['step']==step and created['scene']==scene;near(created['start'],q,1e-7);near(created['endpoint'],best['candidate'],0);near(created['waypoints'],path['waypoints'],0)
  assert created['best']=={k:v for k,v in best.items() if k!='path'};assert created['attempts']==[{k:v for k,v in a.items() if k!='path'} for a in attempts]
  axis=np.linalg.eigh(np.cov(self.hand.vertices[scene['side']].T))[1][:,0];near(abs(np.array(m['thin_axis_local'])@axis),1.,1e-10)
  return dict(selected='candidate',route=route,waypoints=path['waypoints'])

 def verified_waypoints(self,created,q,scene,step):
  return np.asarray(self.verify_preference(created,current=q,scene=scene,step=step)['waypoints'])
