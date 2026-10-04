"""Independent static geometry and original causal arithmetic for two predicted plans.
This is an explicitly hypothetical-input check, not native physical data.
"""
from pathlib import Path
import datetime,hashlib,json,sys,copy
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();p=D/'RECOVERY_PREFLIGHT_CHECK.json';bound=json.loads(p.read_text());assert bound['status']=='complete' and len(bound['records'])==2
for f,h in bound['source_sha256'].items():assert sha(f)==h,f
checker=SelectionAudit(ROOT,S);rows=[];negative=[]
for v in bound['records']:
 plan=v['planning'];ctx=plan['transport_preflight']['initial_context'];args=dict(current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],decay=ctx['decay'],scene=plan['scene'],step=ctx['step'])
 proof=checker.verify_selection(plan,**args);assert proof['passed'];rows.append(dict(original_step=v['original_step'],counter=v['counter'],proof=proof,predicted_ticks=plan['transport_preflight']['trials'][-1]['predicted_ticks']))
 for label in ['wrong_start','wrong_trial_ticks','wrong_endpoint','wrong_previous_action']:
  pp=copy.deepcopy(plan);aa=copy.deepcopy(args)
  if label=='wrong_start':pp['start'][0]+=.001
  elif label=='wrong_trial_ticks':pp['transport_preflight']['trials'][0]['predicted_ticks']+=1
  elif label=='wrong_endpoint':pp['attempts'][0]['endpoint'][0]+=.001
  else:aa['previous_command'][0]+=.001
  try:checker.verify_selection(pp,**aa)
  except (AssertionError,KeyError,ValueError):negative.append(dict(step=v['original_step'],case=label,rejected=True))
  else:raise AssertionError(('corrupt hypothetical plan accepted',label))
files=[Path(__file__),p,D/'ACTUAL_CONTEXT_PROPOSAL_CHECK.json',W/'check_inactive_headroom_recovery_preflight.py',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_events.py',W/'audit_front_initial_center_preflight.py',*S.glob('*.py'),S/'causal_response_parameters.json',S/'elbow_torso_hulls.json']
report=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,negative=negative,source_sha256={str(f):sha(f) for f in files},new_headroom_extra_reserve_runtime_checks_retained=True,physical_evidence=False,actual_recovery_verified=False,training_ready=False)
with (D/'INDEPENDENT_RECOVERY_PREFLIGHT_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,rows=rows,negative=len(negative),physical_evidence=False),indent=2))
