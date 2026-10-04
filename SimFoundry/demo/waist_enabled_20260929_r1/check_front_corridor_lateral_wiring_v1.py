"""Parser/class/metadata/archive checks for actual isolated collector; no physics."""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,inspect,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';P=W/'staged_joint_transport_reserve_v1';D=W/'front_corridor_lateral_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from front_initial_center_cop_route import FrontCopRouteState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
for name,h in prep['stage_sha256'].items():assert sha(S/name)==h
for name,edits in prep['changed_files'].items():
 s=(S/name).read_text()
 for edit in reversed(edits):assert s.count(edit['new'])==1;s=s.replace(edit['new'],edit['old'])
 assert s==(P/name).read_text()
plan=W/'joint_transport_reserve_physical_preparation_r1/PLAN.json';cli=json.loads(plan.read_text())['commands'][0]['args'];flag='--front-corridor-lateral-replan';cases=[('off',cli,True),('on',cli+[flag],True)]
for missing in ['--front-corridor-midpoint-replan','--joint-transport-clearance','--front-diagonal-entry','--front-micro-repair-retention','--front-initial-center-landing']:
 assert missing in cli;cases.append(('missing_'+missing,[x for x in cli if x!=missing]+[flag],False))
bad=list(cli)+[flag];bad[bad.index('--role')+1]='pilot';cases.append(('pilot_disallowed',bad,False));parsed={};results=[]
for name,args,expected in cases:
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):actual,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  accepted=True
 except (ValueError,SystemExit):accepted=False
 assert accepted==expected,(name,accepted)
 results.append(dict(case=name,accepted=accepted))
 if accepted:parsed[name]=SimpleNamespace(**actual)
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):old,_=parser_namespace(P/'collect_paired_sorting.py',cli,full=True)
new=vars(parsed['off']).copy();assert new.pop('front_corridor_lateral_replan') is False;assert new==old
p=S/'collect_paired_sorting.py';tree=ast.parse(p.read_text());nodes=list(ast.walk(tree))
block=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_corridor_midpoint_replan' and any(isinstance(v,ast.Name) and v.id=='top_extra' for v in ast.walk(n)))
meta=[n for n in tree.body if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_corridor_lateral_replan']
# Collection metadata is nested in the episode loop; select by actual assignment.
meta=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_corridor_lateral_replan' and any(isinstance(v,ast.Attribute) and v.attr=='collect_meta' for v in ast.walk(n)))
archive=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_initial_center_landing' and any(isinstance(v,ast.Name) and v.id=='paths' for v in ast.walk(n)))
compile_nodes=lambda nodes:compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(p),'exec')
for name in ['off','on']:
 env=dict(args=parsed[name],top_extra={},frontal_plan={});exec(compile_nodes([block]),env)
 expected={'corridor_midpoint_replan':True};phase='front_x_only'
 if name=='on':expected['corridor_lateral_replan']=True;phase='front_x_and_lateral_y'
 assert env['top_extra']==expected and env['frontal_plan']['front_corridor_midpoint']['phase']==phase
 state=FrontCopRouteState(SimpleNamespace(plan={'direction':1}),'left',(.15,.145,.04),**env['top_extra']);assert state.corridor_lateral_replan==(name=='on')
 assert Path(inspect.getfile(type(state))).parent==S
 ep=SimpleNamespace(collect_meta={});me=dict(args=parsed[name],episode=ep,frontal_log=[{},dict(front_corridor_midpoint=dict(changed=True,route_stage='front_x')),dict(front_corridor_midpoint=dict(changed=True,route_stage='lateral_y')),dict(front_corridor_midpoint=dict(changed=False,route_stage='lateral_y'))]);exec(compile_nodes([meta]),me)
 assert ep.collect_meta==({} if name=='off' else dict(front_corridor_lateral_replan=True,front_corridor_lateral_replanned_frames=1))
 arch=dict(args=parsed[name],paths=[],STAGE=S);exec(compile_nodes([archive]),arch)
 assert all(S/n in arch['paths'] for n in ['front_corridor_midpoint_runtime.py','front_initial_center_route.py','front_initial_center_cop_route.py'])
# Constructor accepts dataclass kwargs; invalid combinations must reject before any state access.
for flag_value,midpoint in [(1,True),(True,False)]:
 state=FrontCopRouteState(None,'left',(.15,.145,.04),corridor_lateral_replan=flag_value,corridor_midpoint_replan=midpoint)
 try:state.update(None,None,None,None,None,tip=None,quat=None,obstacle_quat=None,control_offset_local=None,load_n=0,hand_obstacle_gap_m=.1)
 except ValueError:pass
 else:raise AssertionError('invalid class combination accepted')
sources={str(p):sha(p) for p in [Path(__file__),plan,S/'COLLECTOR_PREPARATION.json',W/'prepare_closed_peak_trial.py']};sources.update({str(S/n):h for n,h in prep['stage_sha256'].items()})
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,parser_cases=results,default_off_original_args_equal=True,actual_class_kwargs_and_phase_checked=True,actual_metadata_counts_checked=True,changed_helpers_archived=True,invalid_class_cases_rejected=2,source_sha256=sources,physical_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
