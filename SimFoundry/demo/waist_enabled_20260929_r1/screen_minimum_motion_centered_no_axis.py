"""Offline first2 actual recovery inputs, center +/-5mm without PCA-axis heuristic.
Tests a cause-directed geometry candidate after observed eccentric hand moments.
No simulation, contact certification, runtime change, or new admission gate.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';sys.path[:0]=[str(w),str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from offline_centered_surface_no_axis_plan import plan
from audit_minimum_motion_plan_reentrant import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);independent=PlanAudit(repo,stage);rows=[];sources={}
out=w/'MINIMUM_MOTION_CENTERED_NO_AXIS_SCREEN.json';assert not out.exists()
def save(complete):
 files=[Path(__file__),w/'offline_centered_surface_no_axis_plan.py',w/'audit_minimum_motion_plan_reentrant.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py']
 files+=list(stage.glob('*.py'))+[stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']
 sources.update({str(p):sha(p) for p in files})
 out.write_text(json.dumps(dict(scope=__doc__,complete=complete,center_window_m=.005,pca_axis_constraint=False,rows=rows,source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'minimum_motion_groups_r1'/f'case_{cid}'/f'layout_{cid}_{task}'
 assert json.loads((ep/'MINIMUM_MOTION_POSE_REENTRANT_SUPPLEMENT.json').read_text())['passed']
 events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[e for e in events if e.get('planning')]
 for event in starts[:1]:
  ctx=event['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);parent=event['planning']['minimum_motion_pose']['parent_plan']
  result=plan(scene,q,step=event['step'],parent_plan=parent);m=result['minimum_motion_pose'];checks=[]
  for attempt in m['endpoint_attempts']:
   if not attempt['accepted']:continue
   x=np.array(attempt['candidate']);g,d=independent.geometry(x,ctx['scene']);axis=np.linalg.eigh(np.cov(independent.hand.vertices[scene.side].T))[1][:,0];align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis)
   minimum=float(min(align**2,*list(np.minimum(d['core'][:2]/2-.020,.005)-abs(d['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],independent.hand.minz(x,scene.inactive)-.84,g['elbow_gap_m']-.005))
   assert minimum>=-2e-7 and min(g['hand_parcel_gaps_m'].values())>=.01-2e-7 and np.all(x>=independent.lo-2e-7) and np.all(x<=independent.hi+2e-7)
   assert abs(minimum-attempt['minimum_constraint_m'])<2e-8
   checks.append(dict(seed=attempt['seed'],point_local_m=d['point'].tolist(),alignment_abs=float(align),minimum_constraint_m=minimum))
  if m['selected']=='candidate':
   expected,geometries=independent.path(m['nodes'],ctx['scene']);assert np.array_equal(expected,result['waypoints']);assert all(g['accepted'] for g in geometries)
   for recorded,actual in zip(m['selected_path_checks'],geometries):independent.compare_geometry(recorded,actual)
  row=dict(episode=ep.name,step=event['step'],old_waypoints=len(event['planning']['waypoints']),selected=m['selected'],route=m.get('route'),new_waypoints=len(result.get('waypoints',[])),independent_endpoints=checks,fallback_reason=m['fallback_reason'],plan=result);rows.append(row);sources[str(ep/'recontact_pose.json')]=sha(ep/'recontact_pose.json');save(False)
  print(ep.name,event['step'],m['selected'],m.get('route'),len(result.get('waypoints',[])),flush=True)
assert len(rows)==2;save(True);print('COMPLETE2, accepted candidate paths',sum(r['selected']=='candidate' for r in rows),flush=True)
