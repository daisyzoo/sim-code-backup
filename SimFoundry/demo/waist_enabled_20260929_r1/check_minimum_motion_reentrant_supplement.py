"""Actual multi-path regression; original frozen formal audit remains failed."""
from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_minimum_motion_plan import PlanAudit as Original
from audit_minimum_motion_plan_reentrant import PlanAudit as Revised
from audit_minimum_motion_pose_task_optimality import verify_task_rows,IndependentElbows
r=w/'minimum_motion_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';stage=w/'staged_minimum_motion_recontact'
events=json.loads((ep/'recontact_pose.json').read_text())['rows'];plans=[e for e in events if e.get('planning')];assert len(plans)==2
old=Original(repo,stage);new=Revised(repo,stage)
def run(a,e,p=None):return a.verify_preference(p or e['planning'],current=e['context']['current'],scene=e['context']['scene'],step=e['step'])
assert run(old,plans[0])==run(new,plans[0])
old.endpoint=new.endpoint=np.asarray(plans[0]['planning']['endpoint'])
try:run(old,plans[1])
except TypeError as exc:assert 'not callable' in str(exc)
else:raise AssertionError('Original second-path failure not reproduced')
assert run(new,plans[1])['selected']=='candidate'
rejected=[]
for key in ['endpoint','waypoint','threshold','objective','status','path_geometry']:
 p=copy.deepcopy(plans[1]['planning']);m=p['minimum_motion_pose']
 if key=='endpoint':p['endpoint'][0]+=.02
 elif key=='waypoint':p['waypoints'][0][0]+=.02
 elif key=='threshold':m['alignment_abs_min']=.5
 elif key=='objective':m['endpoint_attempts'][0]['objective']+=.2
 elif key=='status':m['endpoint_attempts'][0]['status']=9
 elif key=='path_geometry':m['selected_path_checks'][0]['active_above_top_m']+=.01
 try:run(new,plans[1],p)
 except (AssertionError,ValueError):rejected.append(key)
 else:raise AssertionError(('corruption passed',key))
pose=json.loads((ep/'MINIMUM_MOTION_POSE_REENTRANT_SUPPLEMENT.json').read_text());assert pose['passed'] and pose['handovers']==2 and pose['command_events']==130
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name,h in pose['source_sha256'].items():assert sha(ep/name)==h
verified={e['step']:{k:v for k,v in e.items() if k!='step'} for e in events if e['kind'] in ('command','handover')};assert set(verified)=={x['step'] for x in pose['records']}
geom=IndependentElbows(stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
task=verify_task_rows(ep,geom,verified)
(ep/'MINIMUM_MOTION_TASK_REENTRANT_SUPPLEMENT.json').write_text(json.dumps(dict(task=task,pose_sha256=sha(ep/'MINIMUM_MOTION_POSE_REENTRANT_SUPPLEMENT.json'),task_auditor_sha256=sha(w/'audit_minimum_motion_pose_task_optimality.py'),supplement_only=True,training_ready=False),indent=2))
out=dict(original_multi_path_error_reproduced=True,first_plan_proof_identical=True,second_plan_passed=True,second_plan_corruptions_rejected=rejected,native_full1200_passed=True,native_verified_events=130,native_handovers=2,task_frames=task['frames'],task_passed=task['passed'],task_max_kkt_residual=task['max_kkt_residual'],task_errors=task['errors'],checker_sha256=sha(__file__),formal_results_unchanged=True,training_ready=False)
(r/'REENTRANT_SUPPLEMENT_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
