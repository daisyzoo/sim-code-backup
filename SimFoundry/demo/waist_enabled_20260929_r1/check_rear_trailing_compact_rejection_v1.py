"""Unissued adversarial-scene checks for exact compact failure trees.
Two measured robot poses with deliberately changed obstacle poses; not real physics.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';D=W/'rear_trailing_contact_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from trailing_recontact_plan import plan
from audit_rear_trailing_compact_events_v1 import EventAudit,has_compact_rejection
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);sources={};rows=[];negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('Invalid rejection accepted '+label)
for side,task in [('right','push_box_to_bin'),('left','nudge_mailer_to_bin')]:
 run='front_box_recenter_physical_r2';case='840023' if side=='right' else '840020';ep=W/run/f'case_{case}'/f'layout_{case}_{task}';p=ep/'recontact_pose.json';history=json.loads(p.read_text())['rows'];sources[str(p)]=sha(p)
 event=next(e for e in history if e['kind']=='command' and e.get('planning') and not e.get('entry_lift_phase'));ctx=event['context'];step=ctx['step'];q=np.array(ctx['current']);observed=copy.deepcopy(ctx['scene']);unsafe=copy.deepcopy(observed);T=guard.model.fk(side,q)[0];unsafe['other_xyz']=(np.mean(guard.model.vertices[side],axis=0)@T[:3,:3].T+T[:3,3]).tolist();scene=RecontactScene(guard,**unsafe);assert not scene.check(q)['accepted']
 created=plan(scene,q,step=step,earlier_seed=(step,q),prefer_interior=True,minimum_motion_pose=True,box_center_preference=side=='right',box_trailing_preference=side=='right');assert has_compact_rejection(created) and created['accepted'] is False and not any(k in created for k in ['command','waypoints','endpoint'])
 checked=EventAudit(ROOT,S).verify_preference(created,current=q,scene=scene.record(),step=step);assert checked['compact_scene_rejection'] and checked['selected']=='original_fallback'
 for label in ['accepted','waypoints','minimum_parent','false_reason','safe_scene']+(['missing_policy','offset','direction','preferred','wrong_step'] if side=='right' else ['box_policy']):
  bad=copy.deepcopy(created);kwargs=dict(current=q,scene=scene.record(),step=step)
  if label=='accepted':bad['accepted']=True
  elif label=='waypoints':bad['waypoints']=[q.tolist()]
  elif label=='minimum_parent':bad['minimum_motion_pose']['parent_plan']['accepted']=True
  elif label=='false_reason':bad['reason']='no_verified_endpoint'
  elif label=='safe_scene':kwargs['scene']=observed
  elif label=='missing_policy':bad.pop('rear_box_trailing_preference')
  elif label=='offset':bad['rear_box_trailing_preference']['offset_m']=.01
  elif label=='direction':bad['rear_box_trailing_preference']['world_direction']=[0.,-1.,0.]
  elif label=='preferred':bad['rear_box_trailing_preference']['preferred_local_xy_m'][0]+=.001
  elif label=='wrong_step':bad['rear_box_trailing_preference']['step']+=1
  elif label=='box_policy':bad['rear_box_trailing_preference']={}
  reject(side+':'+label,lambda:EventAudit(ROOT,S).verify_preference(bad,**kwargs))
 rows.append(dict(side=side,step=step,unissued_adversarial_scene=unsafe,original_observed_scene=observed,created_rejection=created,independent_rejection_check=checked))
for mod in list(sys.modules.values()):
 file=getattr(mod,'__file__',None)
 if file:
  p=Path(file).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative=negative,source_sha256=sources,physical_started=False,training_ready=False)
with (D/'COMPACT_REJECTION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,rejected_plans_verified=2,negative=len(negative))),flush=True)
