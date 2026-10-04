"""Actual collector parser, runtime construction, metadata and archive branches.
No simulator startup, physical commands, data admission or training.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,inspect,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v1';P=W/'staged_joint_transport_reserve_v1';D=W/'front_box_trailing_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
for name,h in prep['stage_sha256'].items():assert sha(S/name)==h
for name,edits in prep['changed_files'].items():
 text=(S/name).read_text()
 for edit in reversed(edits):assert text.count(edit['new'])==1;text=text.replace(edit['new'],edit['old'])
 assert text==(P/name).read_text()
plan=W/'joint_transport_reserve_physical_preparation_r1/PLAN.json';cli=json.loads(plan.read_text())['commands'][0]['args'];flag='--front-box-trailing-landing';cases=[('off',cli,True),('on',cli+[flag],True)]
for missing in ['--front-box-recenter','--joint-transport-clearance','--front-recontact-center-landing','--front-initial-center-landing','--front-loaded-z-priority']:
 assert missing in cli;cases.append(('missing_'+missing,[x for x in cli if x!=missing]+[flag],False))
bad=list(cli)+[flag];bad[bad.index('--role')+1]='pilot';cases.append(('pilot_disallowed',bad,False));parsed={};results=[]
for name,args,expected in cases:
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):actual,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  accepted=True
 except (ValueError,SystemExit):accepted=False
 assert accepted==expected,(name,accepted);results.append(dict(case=name,accepted=accepted))
 if accepted:parsed[name]=SimpleNamespace(**actual)
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):old,_=parser_namespace(P/'collect_paired_sorting.py',cli,full=True)
new=vars(parsed['off']).copy();assert new.pop('front_box_trailing_landing') is False;assert new==old
# Parsing the parent executes its sys.path bootstrap; restore the candidate as a fresh collector would.
sys.path[:0]=[str(S),str(W),str(ROOT)]
p=S/'collect_paired_sorting.py';tree=ast.parse(p.read_text());nodes=list(ast.walk(tree));test=lambda n:ast.unparse(n.test) if isinstance(n,ast.If) else ''
block=next(n for n in nodes if test(n)=="args.front_box_recenter and side == 'right'")
metabox=next(n for n in nodes if test(n)=='args.front_box_recenter' and any(isinstance(x,ast.Attribute) and x.attr=='collect_meta' for x in ast.walk(n)))
meta=next(n for n in nodes if test(n)=='args.front_box_trailing_landing' and any(isinstance(x,ast.Attribute) and x.attr=='collect_meta' for x in ast.walk(n)))
archive=next(n for n in nodes if test(n)=='args.front_box_trailing_landing' and any(isinstance(x,ast.Name) and x.id=='paths' for x in ast.walk(n)))
compile_nodes=lambda ns:compile(ast.fix_missing_locations(ast.Module(body=ns,type_ignores=[])),str(p),'exec')
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';row=next(r for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r.get('planning'));z=row['context']['scene'];a=row['context']['decay'];guard=ClearanceGuard(ROOT,S);branches=[]
for name in ['off','on']:
 env=dict(args=parsed[name],side='right',frontal_plan={},clearance_guard=guard,edge_size=z['core_size'],obstacle_size=z['other_size'],parameters={'tasks':{'box':{'decay':a}}},task_id='box');exec(compile_nodes([block]),env);rt=env['front_recontact_runtime'];assert rt.enabled and rt.side=='right';assert Path(inspect.getfile(type(rt)))==S/('trailing_runtime.py' if name=='on' else 'front_box_recenter_runtime.py');assert getattr(rt,'trailing_landing',False)==(name=='on');fm=env['frontal_plan']['front_box_recenter'];assert fm['maximum_ticks']==240 and fm['actual_ready_frames']==3 and fm['measured_capture_only']
 if name=='on':assert fm['landing_world_offset_m']==[0.,.020,0.] and fm['landing_xy_tolerance_m']==.002 and fm['planning_xy_reserve_m']==.0005 and 'center_xy_m' not in fm
 else:assert fm['center_xy_m']==.002 and fm['version']=='front_box_recenter_v1'
 episode=SimpleNamespace(collect_meta={});exec(compile_nodes([metabox,meta]),dict(args=parsed[name],episode=episode));assert episode.collect_meta['front_box_recenter']==fm;assert episode.collect_meta.get('front_box_trailing_landing',False)==(name=='on')
 arch=dict(args=parsed[name],paths=[],STAGE=S);exec(compile_nodes([archive]),arch);assert arch['paths']==([] if name=='off' else [S/n for n in ['trailing_plan.py','trailing_static.py','trailing_selection.py','trailing_lifecycle.py','trailing_adapter.py','trailing_runtime.py']]);branches.append(dict(branch=name,runtime_source=str(Path(inspect.getfile(type(rt)))),metadata=fm,archive_count=len(arch['paths'])))
# All new helper imports resolve to this same isolated stage.
for module in ['trailing_plan','trailing_static','trailing_selection','trailing_lifecycle','trailing_adapter','trailing_runtime']:
 assert Path(sys.modules[module].__file__).resolve()==S/(module+'.py')
from trailing_runtime import FrontRecontactCenterRuntime
for kwargs in [dict(enabled=False,trailing_landing=True),dict(enabled=True,trailing_landing=1)]:
 try:FrontRecontactCenterRuntime(guard,'right',z['core_size'],z['other_size'],a,**kwargs)
 except ValueError:pass
 else:raise AssertionError('invalid runtime config accepted')
sources={str(p):sha(p) for p in [Path(__file__),plan,S/'COLLECTOR_PREPARATION.json',W/'prepare_closed_peak_trial.py',ep/'front_recontact_center.json']};sources.update({str(S/n):h for n,h in prep['stage_sha256'].items()})
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,parser_cases=results,defaultoff_original_args_identical=True,branches=branches,invalid_runtime_configs_rejected=2,source_sha256=sources,physical_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','branches']},indent=2))
