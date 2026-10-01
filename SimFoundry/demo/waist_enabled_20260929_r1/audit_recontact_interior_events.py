"""Independent declared interior-preference choice and original recovery audit.
Uses independent URDF/hull geometry; imports no candidate planner or lifecycle.
Verifies all recorded preferred/selected attempts and selected path geometry.
A rejected optimizer attempt does not prove global geometric infeasibility.
Original command, measured-handover, bounds and contact gates remain unchanged.
"""
import numpy as np
from audit_recontact_pose_events import EventAudit as OriginalEventAudit
from audit_unloaded_wrist_prior_live import near

class EventAudit(OriginalEventAudit):
 def inspect_plan(self,plan,q,scene,inset):
  assert plan['scene']==scene
  q=np.array(q);wi=5 if scene['side']=='left' else 10;side_other='right' if scene['side']=='left' else 'left'
  accepted=[]
  for attempt in plan['attempts']:
   x=np.array(attempt['candidate']);g,d=self.geometry(x,scene);point=d['point'];margins=d['core'][:2]/2-abs(point[:2]);height=g['active_above_top_m'];inactive_z=self.hand.minz(x,side_other)
   minimum=float(min(*list(margins-inset),height-.006,.007-height,inactive_z-.84,g['elbow_gap_m']-.005))
   near(attempt['minimum_constraint'],minimum,2e-9);near(attempt['core_xy_margin_m'],margins,2e-9);near(attempt['above_top_m'],height,2e-9)
   assert attempt['vertex_index']==d['vertex_index'];near(attempt['objective'],x[wi]**2+.002*np.sum((x-q)**2),1e-8);near(attempt['wrist_abs_reduction_rad'],abs(q[wi])-abs(x[wi]),1e-9)
   valid=bool(attempt['status']==0 and minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7)
   assert attempt['accepted'] is valid
   if valid:assert np.all(x>=self.lo-2e-7) and np.all(x<=self.hi+2e-7);accepted.append(attempt)
  assert plan['accepted']==bool(accepted)
  if not accepted:return
  best=min(accepted,key=lambda r:r['objective']);assert plan['best']==best;near(plan['endpoint'],best['candidate'],0);near(plan['start'],q,1e-7)
  x=np.array(plan['endpoint']);count=max(1,int(np.ceil(max(abs(x-q)/(self.limits*.25)))))
  expected=np.array([np.clip(q+(x-q)*i/count,self.lo,self.hi) for i in range(1,count+1)])
  near(plan['waypoints'],expected,1e-10)

 def verify_preference(self,created,*,current,scene,step):
  pref=created['interior_preference'];assert pref['enabled'] is True and pref['preferred_inset_m']==.020 and pref['original_inset_m']==.012 and pref['not_physical_contact_proof'] is True
  deep=pref['preferred_plan'];assert deep['step']==created['step']==step;self.inspect_plan(deep,current,scene,.020)
  checks=pref['preferred_path_checks'];expected=[self.geometry(q,scene)[0] for q in deep['waypoints']] if deep['accepted'] else [];assert len(checks)==len(expected)
  for stored,actual in zip(checks,expected):self.compare_geometry(stored,actual)
  usable=bool(deep['accepted'] and all(x['accepted'] for x in expected))
  assert pref['selected']==('preferred' if usable else 'original_fallback')
  assert pref['fallback_reason']==(None if usable else ('preferred_endpoint_rejected' if not deep['accepted'] else 'preferred_path_rejected'))
  assert pref['selected_inset_m']==((.020 if usable else .012) if created['accepted'] else None)
  if usable:assert {k:v for k,v in created.items() if k!='interior_preference'}==deep
  else:self.inspect_plan(created,current,scene,.012)
  return dict(selected=pref['selected'],preferred_accepted=deep['accepted'],path_samples=len(expected),selected_inset_m=pref['selected_inset_m'])

 def verify(self,event,**kwargs):
  created=event['planning'];preference=None
  if created is not None:preference=self.verify_preference(created,current=kwargs['current'],scene=kwargs['scene'],step=kwargs['step'])
  out=super().verify(event,**kwargs)
  if preference is not None:out['interior_preference']=preference
  return out
