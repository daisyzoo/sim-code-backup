"""Fault-injected optimizer budget, not physics or production settings.
Exercise actual staged wrapper refusal and independent rejected-plan geometry.
Only this process limits the real SLSQP call to one iteration; no source edits.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_entry_lift';sys.path[:0]=[str(stage),str(w),str(repo)]
import box_center_preference_plan as planner
from box_entry_lift_recontact_guarded import RecontactLifecycle
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_slow_drag_plan import PlanAudit
from audit_box_entry_plan import verify_entry_plan
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=w/'BOX_ENTRY_LIFT_COMBINED_CHECK.json';data=json.loads(baseline.read_text());assert data['complete'] and len(data['rows'])==13
for name,h in data['source_sha256'].items():assert sha(name)==h
real_minimize=planner.minimize
calls=[]
def limited(*args,**kw):
 kw=dict(kw,options=dict(kw['options'],maxiter=1));fit=real_minimize(*args,**kw);calls.append(dict(status=int(fit.status),iterations=int(fit.nit)));return fit
planner.minimize=limited;guard=ClearanceGuard(repo,stage);audit=PlanAudit(repo,stage);rows=[]
try:
 for row in data['rows']:
  first=row['trace'][0];ctx=first['context'];scene=RecontactScene(guard,**ctx['scene']);inputs=dict(ctx,scene=scene,decay=first['proposal']['decay']);state=RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True,entry_lift=True)
  event=state.update(**inputs);assert event['kind']=='unchanged' and event['reason']=='initial_hand_below_unloaded_planning_height' and not state.active and state.total_ticks==0
  rejected=event['rejected_entry_lift_attempt'];assert rejected['reason']=='no_verified_entry_lift' and rejected['context']==event['context'];plan=rejected['planning'];assert verify_entry_plan(audit,plan,current=ctx['current'],scene=ctx['scene'],step=ctx['step'])['accepted'] is False
  assert 'command' not in event and 'captured_center_local' not in event
  count=len(calls);again=state.update(**dict(inputs,step=ctx['step']+1));assert again['kind']=='unchanged' and 'rejected_entry_lift_attempt' not in again and len(calls)==count
  bad=copy.deepcopy(plan);bad['accepted']=True
  try:verify_entry_plan(audit,bad,current=ctx['current'],scene=ctx['scene'],step=ctx['step'])
  except AssertionError:pass
  else:raise AssertionError('Accepted falsified success')
  rows.append(dict(run=row['run'],start_step=ctx['step'],optimizer=calls[-1],rejected_plan=plan,no_command=True,no_same_recovery_retry=True,false_success_rejected=True));print(row['run'],ctx['step'],'refusal_verified',flush=True)
finally:planner.minimize=real_minimize
assert len(rows)==13
sources=[Path(__file__),baseline,w/'audit_box_entry_plan.py',w/'audit_slow_drag_plan.py',stage/'box_center_preference_plan.py',stage/'box_recovery_entry_lift.py',stage/'box_entry_lift_recontact_guarded.py',stage/'minimum_motion_lifecycle.py']
(stage/'REJECTED_PLAN_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,rows=rows,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));print('PASS13')
