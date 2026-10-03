"""New77-source inverse mapping and exact enabled six-configuration semantics.
The negative checks alter in-memory arguments only, never frozen source files.
"""
from pathlib import Path
import sys,json,copy,datetime,hashlib
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';sys.path[:0]=[str(W),str(W.parents[1])]
from front_recontact_stage_source_binding import verify_preparation,verify_settings
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();plan=json.loads((W/'front_corridor_midpoint_physical_r1/PROTOCOL.json').read_text())['plan'];records=[]
for c in plan['commands']:
 parsed,_=parser_namespace(S/'collect_paired_sorting.py',c['args']+['--front-recontact-center-landing'],full=True);assert parsed['front_recontact_center_landing'] is True
 # Native provenance contains post-AppLauncher normalized rendering arguments.
 args=json.loads((W/'front_corridor_midpoint_physical_r1'/f"case_{c['layout_id']}"/'provenance.json').read_text())['args'];args=dict(args,front_recontact_center_landing=True)
 assert verify_settings(args);records.append(dict(layout=c['layout_id'],passed=True,native_parent_args_plus_only_new_flag=True))
negative=[]
changes={'front_recontact_center_landing':False,'front_cop_drive_step_m':.001,'front_corridor_midpoint_replan':False,'front_initial_center_landing':False,'front_loaded_z_priority':False,'peak_load_bias_guard':False,'push_assist':True,'waist_limit_rad':1.3,'policy_port':8888,'role':'train','expert_front_clearance_m':.005,'expert_frontal_top_load_n':1.,'newton_contacts':False,'idle':True,'rear_waypoint_reconciliation':True}
for k,v in changes.items():
 bad=copy.deepcopy(args);bad[k]=v
 try:verify_settings(bad)
 except (AssertionError,KeyError,ValueError):negative.append(k)
 else:raise AssertionError('bad setting accepted '+k)
for p in [Path(__file__),W/'front_recontact_stage_source_binding.py',S/'COLLECTOR_PREPARATION.json',W/'front_corridor_midpoint_physical_r1/PROTOCOL.json']:bound[str(p)]=sha(p)
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime_source_count=len(expected),configurations=records,rejected_settings=negative,source_sha256=bound,native_new_episode_not_yet_available=True,training_ready=False)
with (S/'SOURCE_BINDING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,sources=len(expected),configs=len(records),negative=len(negative))))
