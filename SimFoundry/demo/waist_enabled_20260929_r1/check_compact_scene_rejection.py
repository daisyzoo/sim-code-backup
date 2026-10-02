"""Actual rejected-plan records plus explicit mutation and safe-scene negatives."""
from pathlib import Path
import sys,json,hashlib,copy,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_compact_scene_rejection import EventAudit,verify_compact_scene_rejection
from audit_recontact_pose_events import EventAudit as GeometryAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=EventAudit(W.parents[1],W/'staged_joint_edge_clearance_intersection');g=GeometryAudit(W.parents[1],W/'staged_joint_edge_clearance_intersection');ep=W/'joint_edge_intersection_physical_r1/case_840015/layout_840015_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];positives=[];negatives=[]
for ev in events:
 if ev['step'] not in [948,1117]:continue
 plan=ev['planning'];ctx=ev['context'];kw=dict(current=ctx['current'],scene=ctx['scene'],step=ev['step']);r=a.verify_preference(plan,**kw);assert r['compact_scene_rejection'] and r['waypoints']==[];positives.append(ev['step'])
 if negatives:continue
 for name in ['accepted_flag','invented_step','invented_waypoint','parent_mismatch','attempt_injection','wrong_reason','safe_observed_scene']:
  bad=copy.deepcopy(plan);inputs=copy.deepcopy(kw)
  if name=='accepted_flag':bad['accepted']=True
  elif name=='invented_step':bad['interior_preference']['preferred_plan']['step']=ev['step']
  elif name=='invented_waypoint':bad['waypoints']=[ctx['current']]
  elif name=='parent_mismatch':bad['minimum_motion_pose']['parent_plan']['reason']='other'
  elif name=='attempt_injection':bad['box_center_preference_pose']['endpoint_attempts']=[dict(accepted=False)]
  elif name=='wrong_reason':bad['reason']='no_verified_endpoint'
  else:
   q=np.clip(inputs['current'],g.lo,g.hi);assert g.geometry(q,inputs['scene'])[0]['accepted'];inputs['current']=q
  try:verify_compact_scene_rejection(a,bad,**inputs)
  except AssertionError:negatives.append(name)
  else:raise AssertionError(('invalid rejection accepted',name))
assert positives==[948,1117] and len(negatives)==7
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,actual_records_checked=positives,rejected_mutations=negatives,source_sha256={str(p):sha(p) for p in [ep/'recontact_pose.json',W/'audit_compact_scene_rejection.py',W/'audit_recontact_pose_events.py']},checker_sha256=sha(__file__),full_trajectory_verified=False,training_ready=False)
with (W/'COMPACT_SCENE_REJECTION_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print('PASS',positives,negatives)
