"""Real CLI validation and class wiring for isolated interval stage, no simulation."""
from pathlib import Path
import sys,json,hashlib,datetime,contextlib,io,dataclasses
W=Path(__file__).resolve().parent;S=W/'staged_front_corridor_interval';ROOT=W.parents[1];sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'PREPARATION.json').read_text())
for name,h in prep['stage_sha256'].items():assert sha(S/name)==h
base=list(json.loads((W/'peak_guard_groups_r1/PROTOCOL.json').read_text())['commands'][0]['args'])+['--out-dir','/tmp/front_corridor_interval_CLI_NO_SIMULATION'];tests=[]
def cli(name,args,expected):
 settings=None
 try:
  with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  ok=True
 except SystemExit as e:ok=e.code==0
 assert ok==expected,(name,ok);tests.append(dict(name=name,accepted=ok));return settings
old=cli('default_off',base,True);new=cli('enabled_original_diagnostic',base+['--front-corridor-interval'],True);assert not old['front_corridor_interval'] and new['front_corridor_interval'];assert {k:v for k,v in old.items() if k!='front_corridor_interval'}=={k:v for k,v in new.items() if k!='front_corridor_interval'}
for flag in ['--expert-front-top-route','--front-micro-repair-retention','--front-diagonal-entry','--front-direction-recontact','--front-cop-slip-following','--self-clearance-task-ik','--trace-substep-contacts']:
 args=base.copy();args.remove(flag);cli('missing_'+flag,args+['--front-corridor-interval'],False)
args=base.copy();args[args.index('--role')+1]='pilot';cli('pilot_rejected',args+['--front-corridor-interval'],False)
for flag in ['--idle','--waist-probe']:cli('reject_'+flag,base+['--front-corridor-interval',flag],False)
from front_cop_route_micro import FrontCopRouteState
from front_top_route_micro import FrontTopRouteState
assert issubclass(FrontCopRouteState,FrontTopRouteState);fields={f.name:f for f in dataclasses.fields(FrontCopRouteState)};assert fields['corridor_interval_replan'].default is False
assert Path(sys.modules['front_top_route_micro'].__file__).resolve()==S/'front_top_route_micro.py'
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,cli_tests=tests,actual_cop_class_inherits_candidate=True,default_off=True,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'PREPARATION.json',S/'collect_paired_sorting.py',S/'front_top_route_micro.py',S/'front_cop_route_micro.py']},simulation_started=False,training_ready=False)
with (S/'CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
