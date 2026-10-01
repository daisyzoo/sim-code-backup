"""Offline reach hypothesis at the actual first rear-box recovery.
The existing candidate saturates0.98 command yaw. Compare a declared1.20rad
working hypothesis (command1.18) without changing any live limit. Not a physical
or camera/full-body safety certificate; user-authorized waist motion still needs
complete validation before any expanded working range is used in collection.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';sys.path[:0]=[str(w),str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_minimum_motion_plan_reentrant import PlanAudit
from offline_center_penalty_plan import plan as soft_plan
from offline_centered_surface_plan import plan as hard_plan
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
limit=1.20;guard=ClearanceGuard(repo,stage);assert U1_JOINT_LIMIT_LO[12]<-limit<limit<U1_JOINT_LIMIT_HI[12];guard.lower[0],guard.upper[0]=-(limit-.02),limit-.02
class HypothesisScene(RecontactScene):
 def check(self,q):
  old=super().check(q);low=self.guard.lower.copy();high=self.guard.upper.copy();low[0],high[0]=-limit,limit
  bounds=bool(np.all(q>=low-2e-7) and np.all(q<=high+2e-7));out=dict(old,physical_bounds=bounds,accepted=bool(old['active_above_top_m']>=.004 and min(old['hand_parcel_gaps_m'].values())>=.01 and old['elbow_gap_m']>0 and bounds))
  if abs(q[0])<=1.:assert old==out
  return out
class IndependentHypothesis(PlanAudit):
 def geometry(self,q,scene):
  old,detail=super().geometry(q,scene);low=self.lo.copy();high=self.hi.copy();low[0],high[0]=-limit,limit
  bounds=bool(np.all(q>=low-2e-7) and np.all(q<=high+2e-7));out=dict(old,physical_bounds=bounds,accepted=bool(old['active_above_top_m']>=.004 and min(old['hand_parcel_gaps_m'].values())>=.01 and old['elbow_gap_m']>0 and bounds))
  if abs(q[0])<=1.:assert old==out
  return out,detail
ind=IndependentHypothesis(repo,stage);ind.lo[0],ind.hi[0]=guard.lower[0],guard.upper[0]
ep=w/'minimum_motion_groups_r1/case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];event=next(e for e in events if e.get('planning'));assert event['step']==294
ctx=event['context'];q=np.array(ctx['current']);scene=HypothesisScene(guard,**ctx['scene']);rows=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=w/'REAR_BOX_WAIST_MARGIN_SCREEN.json';assert not out.exists()
for label,fn in [('soft_center',soft_plan),('center5mm',hard_plan)]:
 result=fn(scene,q,step=event['step'],parent_plan=event['planning']);m=result['minimum_motion_pose'];checks=[]
 for attempt in m['endpoint_attempts']:
  if not attempt['accepted']:continue
  x=np.asarray(attempt['candidate']);g,d=ind.geometry(x,ctx['scene']);axis=np.linalg.eigh(np.cov(ind.hand.vertices[scene.side].T))[1][:,0];align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis);half=d['core'][:2]/2-.020
  if label=='center5mm':half=np.minimum(half,.005)
  minimum=float(min(align**2-.8**2,*list(half-abs(d['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],ind.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005))
  assert minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=ind.lo-2e-7) and np.all(x<=ind.hi+2e-7)
  assert abs(minimum-attempt['minimum_constraint_m'])<2e-8
  checks.append(dict(seed=attempt['seed'],point_local_m=d['point'].tolist(),alignment_abs=float(align),minimum_constraint_m=minimum))
 if m['selected']=='candidate':
  expected,geoms=ind.path(m['nodes'],ctx['scene']);assert np.array_equal(expected,result['waypoints']) and all(g['accepted'] for g in geoms)
  for recorded,actual in zip(m['selected_path_checks'],geoms):ind.compare_geometry(recorded,actual)
 _,d=ind.geometry(result['endpoint'],ctx['scene']);rows.append(dict(variant=label,selected=m['selected'],route=m.get('route'),waypoints=len(result['waypoints']),endpoint_waist_rad=result['endpoint'][0],surface_radius_mm=float(np.linalg.norm(d['point'][:2])*1000),independent_endpoints=checks,plan=result))
 print(label,m['selected'],len(result['waypoints']),rows[-1]['surface_radius_mm'],rows[-1]['endpoint_waist_rad'],flush=True)
 sources=[Path(__file__),ep/'recontact_pose.json',w/'offline_center_penalty_plan.py',w/'offline_centered_surface_plan.py',stage/'clearance_runtime.py',stage/'recontact_scene.py',w/'audit_minimum_motion_plan_reentrant.py',w/'audit_recontact_pose_events.py',repo/'simfoundry/robots/g1_assets.py']
 out.write_text(json.dumps(dict(scope=__doc__,complete=len(rows)==2,original_working_waist_limit_rad=1.,hypothetical_working_waist_limit_rad=limit,command_margin_rad=.02,rows=rows,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,live_limit_changed=False,training_ready=False),indent=2))
