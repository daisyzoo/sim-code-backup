"""Execute full native parser and prelaunch argument validation without launching Isaac.
Every original complete command remains available, with a default-off extra flag.
"""
from pathlib import Path
import sys,json,datetime,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';sys.path[:0]=[str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();planpath=W/'front_recontact_headroom_preparation_r1/PLAN.json';plan=json.loads(planpath.read_text());checked=[];negative=[]
for command in plan['commands']:
 args=command['args'];parent,_=parser_namespace(W/'staged_front_recontact_headroom/collect_paired_sorting.py',args,full=True);disabled,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);enabled,_=parser_namespace(S/'collect_paired_sorting.py',args+['--front-recontact-inactive-clearance'],full=True)
 assert disabled.pop('front_recontact_inactive_clearance') is False and enabled.pop('front_recontact_inactive_clearance') is True
 assert semantic_settings(disabled)==semantic_settings(parent)==semantic_settings(enabled)
 checked.append(dict(layout_id=command['layout_id'],tasks=command['tasks'],default_disabled=True,only_new_option_changed=True))
base=plan['commands'][0]['args']+['--front-recontact-inactive-clearance']
for label,remove in [('no_recovery','--front-recontact-center-landing'),('no_initial','--front-initial-center-landing'),('no_loaded_z','--front-loaded-z-priority'),('no_midpoint','--front-corridor-midpoint-replan')]:
 bad=[x for x in base if x!=remove]
 try:parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
 except SystemExit as e:assert e.code!=0;negative.append(label)
 else:raise AssertionError('bad config accepted '+label)
files=[Path(__file__),planpath,S/'COLLECTOR_PREPARATION.json',S/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=checked,negative=negative,source_sha256={str(p):sha(p) for p in files},physical_started=False,training_ready=False)
with (S/'PARSER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,configurations=len(checked),negative=len(negative))))
