"""Independent recorded-plan checks: new box preference plus unchanged bag.
Pure geometry/metadata checking, not source-admitted new physics or training.
"""
from pathlib import Path
import sys,json,hashlib,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(w),str(repo)]
from audit_box_center_plan import PlanAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();audit=PlanAudit(repo,stage);rows=[];sources={};bad=[]
screen=stage/'RUNTIME_PLAN_CHECK.json';d=json.loads(screen.read_text());assert d['passed'];sources[str(screen)]=sha(screen)
for row in d['rows']:
 p=row['plan'];ctx=dict(current=p['start'],scene=p['scene'],step=p['step']);proof=audit.verify_preference(p,**ctx);assert proof['selected']=='candidate';rows.append(dict(side='right',run=row['run'],step=p['step'],passed=True))
 try:audit.verify_preference(p['box_center_preference_pose']['parent_plan'],**ctx)
 except AssertionError:bad.append('right_box_missing_center_evidence')
 else:raise AssertionError('Missing new box evidence accepted')
ep=w/'rear_box_rate_groups_r1/case_840004/layout_840004_nudge_mailer_to_bin';f=ep/'recontact_pose.json';sources[str(f)]=sha(f)
for event in json.loads(f.read_text())['rows']:
 if event.get('planning') is None:continue
 p=event['planning'];ctx=dict(current=event['context']['current'],scene=event['context']['scene'],step=event['step']);assert ctx['scene']['side']=='left';proof=audit.verify_preference(p,**ctx);rows.append(dict(side='left',step=event['step'],passed=True))
 invalid=copy.deepcopy(p);invalid['box_center_preference_pose']={}
 try:audit.verify_preference(invalid,**ctx)
 except AssertionError:bad.append('left_bag_center_evidence_forbidden')
 else:raise AssertionError('New box preference accepted on bag')
assert sum(x['side']=='right' for x in rows)==8 and any(x['side']=='left' for x in rows)
for f in [Path(__file__),w/'audit_box_center_plan.py',w/'audit_box_center_preference_plan.py',w/'audit_box_center_events.py',w/'audit_slow_drag_plan.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py']:sources[str(f)]=sha(f)
(stage/'SIDE_AUDIT_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,rows=rows,rejected_wrong_side_metadata=bad,source_sha256=sources,physical_validation=False,training_ready=False),indent=2));print('PASS',len(rows),'independent plans;',len(bad),'invalid side metadata')
