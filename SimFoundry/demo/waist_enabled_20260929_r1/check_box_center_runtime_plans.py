"""All8 actual rear-box recovery starts: causal runtime and independent plan audit.
No dynamics, new image, contact success or training admission is established.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_plan import plan
from audit_box_center_preference_plan import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);audit=PlanAudit(repo,stage);rows=[];sources={};out=stage/'RUNTIME_PLAN_CHECK.json';assert not out.exists()
def save(complete,negatives=None):
 for f in [Path(__file__),w/'audit_box_center_preference_plan.py',w/'audit_slow_drag_plan.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',*stage.glob('*.py'),stage/'elbow_torso_hulls.json',repo/'assets/robots/g1_hand_support_vertices.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(f)]=sha(f)
 out.write_text(json.dumps(dict(passed=complete,complete=complete,scope=__doc__,rows=rows,negative_cases=negatives or [],source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for run in ['rear_slow_drag_groups_r1','rear_box_rate_groups_r1']:
 ep=w/run/'case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[e for e in events if e.get('planning')];first=starts[0];earliest=(first['step'],np.asarray(first['context']['current']))
 sources[str(ep/'recontact_pose.json')]=sha(ep/'recontact_pose.json')
 for e in starts:
  ctx=e['context'];q=np.array(ctx['current']);scene=RecontactScene(guard,**ctx['scene']);kw=dict(step=e['step'],earlier_seed=earliest,prefer_interior=True,minimum_motion_pose=True)
  original=plan(scene,q,**kw);assert original==e['planning'],'Disabled runtime does not reproduce actual parent'
  result=plan(scene,q,**kw,box_center_preference=True);assert result['box_center_preference_pose']['parent_plan']==original
  proof=audit.verify_preference(result,current=q,scene=ctx['scene'],step=e['step']);_,old=audit.geometry(original['endpoint'],ctx['scene']);_,new=audit.geometry(result['endpoint'],ctx['scene'])
  row=dict(run=run,step=e['step'],default_off_parent_exact=True,parent_recomputed_causally=True,selected=proof['selected'],old_radius_mm=float(np.linalg.norm(old['point'][:2])*1000),new_radius_mm=float(np.linalg.norm(new['point'][:2])*1000),old_waypoints=len(original['waypoints']),new_waypoints=len(result['waypoints']),plan=result);rows.append(row);save(False);print(run,e['step'],proof['selected'],row['old_waypoints'],row['new_waypoints'],flush=True)
assert len(rows)==8
negatives=[]
for label,mutate in [('weight',lambda p:p['box_center_preference_pose'].update(center_weight_per_m2=399.)),('parent_current',lambda p:p['box_center_preference_pose']['parent_plan']['start'].__setitem__(0,0.)),('objective',lambda p:p['box_center_preference_pose']['endpoint_attempts'][0].update(objective=0.)),('selected_endpoint',lambda p:p['endpoint'].__setitem__(0,0.))]:
 corrupt=copy.deepcopy(result);mutate(corrupt)
 try:audit.verify_preference(corrupt,current=q,scene=ctx['scene'],step=e['step'])
 except (AssertionError,ValueError):negatives.append(label)
 else:raise AssertionError('Auditor accepted corrupted '+label)
for value in [1,None]:
 try:plan(scene,q,**kw,box_center_preference=value)
 except ValueError:negatives.append('non_boolean_'+str(value))
 else:raise AssertionError('Runtime accepted non-boolean')
assert len(negatives)==6;save(True,negatives);print('COMPLETE8;6bad inputs rejected',flush=True)
