"""Execute full native parser and prelaunch argument validation without launching Isaac.
Every original complete command remains available, with a default-off extra flag.
"""
from pathlib import Path
import sys,json,datetime,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();planpath=W/'front_box_recenter_preparation_r2/PLAN.json';plan=json.loads(planpath.read_text());checked=[];negative=[]
for command in plan['commands']:
 args=command['args'];parent,_=parser_namespace(W/'staged_front_box_recenter_v3/collect_paired_sorting.py',args,full=True);disabled,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);enabled,_=parser_namespace(S/'collect_paired_sorting.py',args+['--joint-transport-clearance'],full=True)
 assert disabled.pop('joint_transport_clearance') is False and enabled.pop('joint_transport_clearance') is True
 assert disabled.pop('inactive_transport_clearance') is False and enabled.pop('inactive_transport_clearance') is False
 assert semantic_settings(disabled)==semantic_settings(parent)==semantic_settings(enabled)
 checked.append(dict(layout_id=command['layout_id'],tasks=command['tasks'],default_disabled=True,only_new_option_changed=True))
base=plan['commands'][0]['args']+['--joint-transport-clearance']
for label,remove in [('no_box_profile','--front-box-recenter'),('no_recovery','--front-recontact-center-landing'),('no_initial','--front-initial-center-landing'),('no_loaded_z','--front-loaded-z-priority'),('no_midpoint','--front-corridor-midpoint-replan')]:
 bad=[x for x in base if x!=remove]
 try:parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
 except (SystemExit,ValueError) as e:
  if isinstance(e,SystemExit):assert e.code!=0
  negative.append(label)
 else:raise AssertionError('bad config accepted '+label)
try:parser_namespace(S/'collect_paired_sorting.py',base+['--inactive-transport-clearance'],full=True)
except (SystemExit,ValueError):negative.append('mutually_exclusive_transport')
else:raise AssertionError('two transports accepted')
files=[Path(__file__),planpath,S/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=checked,negative=negative,source_sha256={str(p):sha(p) for p in files},physical_started=False,training_ready=False)
with (W/'joint_transport_reserve_preparation_r1/PARSER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,configurations=len(checked),negative=len(negative))))
