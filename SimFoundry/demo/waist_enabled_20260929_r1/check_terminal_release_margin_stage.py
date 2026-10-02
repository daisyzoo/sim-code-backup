"""Check actual staged parser and monitor initialization, not an Isaac rollout."""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.top_contact_bypass import TopContactBypassState
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease as ParentMonitor
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());base=json.loads((W/'joint_edge_intersection_physical_preparation_r1/PLAN.json').read_text())['commands'][0]['args'];tree=ast.parse((S/'collect_paired_sorting.py').read_text());blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.terminal_release_margin' and any(isinstance(x,ast.ImportFrom) and x.module=='margin_confirmed_position_release' for x in n.body)];assert len(blocks)==1;code=compile(ast.fix_missing_locations(ast.Module(body=blocks,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec');rows=[];negative=[]
for label,args,expected in [('default_off',base,True),('enabled',base+['--terminal-release-margin'],True),('missing_confirm',[x for x in base if x!='--expert-top-confirmed-release']+['--terminal-release-margin'],False)]:
 try:
  with contextlib.redirect_stderr(io.StringIO()):settings,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  valid=True
 except (ValueError,SystemExit):valid=False
 assert valid==expected,label
 if not valid:negative.append(label);continue
 assert settings['terminal_release_margin']==(label=='enabled')
 for side,direction in [('left',1),('right',-1)]:
  initial=direction*.05;plan={'initial_target_xyz':[.5,initial,.77],'direction':direction};state=TopContactBypassState(SimpleNamespace(plan=plan),side,(.15,.145,.04),confirm_terminal_release=True);frontal_plan={};env=dict(args=SimpleNamespace(**settings),frontal_state=state,frontal_plan=frontal_plan);exec(code,env)
  if label=='default_off':assert state.position_release_monitor is None and not frontal_plan
  else:
   monitor=state.position_release_monitor;assert type(monitor).__module__=='margin_confirmed_position_release';old=ParentMonitor(initial,direction)
   for _ in range(10):a=old.observe([.5,direction*.2,.77]);b=monitor.observe([.5,direction*.2,.77])
   assert a and not b
   for _ in range(10):b=monitor.observe([.5,direction*.212,.77])
   assert b;assert frontal_plan['confirmed_release_margin']==dict(enabled=True,zone_m=.205,minimum_progress_m=.16,original_confirmation_window=10,original_window_xy_m=.01,quality_thresholds_unchanged=True)
  rows.append(dict(case=label,side=side,actual_collector_initialization=True))
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
assert (S/'margin_confirmed_position_release.py').read_bytes()==(W/'margin_confirmed_position_release.py').read_bytes()
report=dict(status='complete',passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,stage_sha256=prep['stage_sha256'],checker_sha256=sha(__file__),history_check_sha256=sha(W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json'),simulation_started=False,training_ready=False)
with (S/'CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print('passed',len(rows),'actual initialization cases')
