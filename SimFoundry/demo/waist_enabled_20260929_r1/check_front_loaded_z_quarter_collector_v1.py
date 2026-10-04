"""Check actual parser, default-off AST identity, native factory, metadata/archive.
No simulation or runtime chain audit is implied by this wiring check.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,contextlib,io,json,sys,inspect,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'staged_front_corridor_lateral_v1';S=W/'staged_front_loaded_z_quarter_v1';D=W/'front_loaded_z_quarter_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());tree=ast.parse((S/'collect_paired_sorting.py').read_text());old=ast.parse((P/'collect_paired_sorting.py').read_text())
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.front_loaded_z_quarter' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  v=n.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value=='--front-loaded-z-quarter':return None
  return self.generic_visit(n)
assert ast.dump(RemoveNew().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(old,include_attributes=False)
protocol=read(W/'front_corridor_lateral_physical_r1/PROTOCOL.json');parsers=[]
def parsed(path,cli):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(path,cli,full=True)[0]
 finally:sys.path[:]=before
for c in protocol['plan']['commands']:
 baseline=parsed(P/'collect_paired_sorting.py',c['args']);off=parsed(S/'collect_paired_sorting.py',c['args']);assert off.pop('front_loaded_z_quarter') is False;assert off==baseline
 on=parsed(S/'collect_paired_sorting.py',c['args']+['--front-loaded-z-quarter']);assert on.pop('front_loaded_z_quarter') is True;assert on==baseline;parsers.append(dict(layout_id=c['layout_id'],default_exact=True,enabled_only_new_flag=True))
negative=[];base=protocol['plan']['commands'][0]['args']
for name,cli in [('missing_priority',[x for x in base if x!='--front-loaded-z-priority']),('missing_transport',[x for x in base if x!='--joint-transport-clearance']),('policy',base+['--policy-port','8000']),('idle',base+['--idle'])]:
 try:parsed(S/'collect_paired_sorting.py',cli+['--front-loaded-z-quarter'])
 except SystemExit as e:assert e.code!=0;negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(('invalid quarter parser accepted',name))
from clearance_runtime import ClearanceGuard
from front_loaded_z_priority import FrontLoadedZPriority
assert Path(inspect.getfile(ClearanceGuard)).resolve()==S/'clearance_runtime.py';guard=ClearanceGuard(ROOT,S)
priority=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and 'priority_command' in ast.unparse(n))
factories=[n for n in priority.body if isinstance(n,ast.If) and (ast.unparse(n.test)=='args.front_loaded_z_quarter and front_loaded_z_priority_controller is None' or ast.unparse(n.test)=='front_loaded_z_priority_controller is None')];assert len(factories)==2
program=compile(ast.fix_missing_locations(ast.Module(body=factories,type_ignores=[])),'<native factory>','exec');factory=[]
for enabled in [False,True]:
 env=dict(args=NS(front_loaded_z_quarter=enabled),front_loaded_z_priority_controller=None,FrontLoadedZPriority=FrontLoadedZPriority,clearance_guard=guard)
 exec(program,env);obj=env['front_loaded_z_priority_controller'];expected=S/('front_loaded_z_fraction.py' if enabled else 'front_loaded_z_priority.py');assert Path(inspect.getfile(type(obj))).resolve()==expected
 if enabled:assert obj.fraction==.25
 before=obj;exec(program,env);assert env['front_loaded_z_priority_controller'] is before;factory.append(dict(enabled=enabled,module=str(expected),reuses_controller=True))
meta=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_quarter' and "episode.collect_meta['front_loaded_z_quarter']" in ast.unparse(n));archive=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_quarter' and 'paths.append' in ast.unparse(n))
for enabled in [False,True]:
 env=dict(args=NS(front_loaded_z_quarter=enabled),episode=NS(collect_meta={}),STAGE=S,paths=[])
 for node in [meta,archive]:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<native metadata/archive>', 'exec'),env)
 if enabled:assert env['episode'].collect_meta['front_loaded_z_quarter']==dict(version='front_loaded_z_quarter_v1',fraction=.25,z_target='parent_linear_achieved_to_original_requested',original_task_retained=True,training_ready=False);assert env['paths']==[S/'front_loaded_z_fraction.py']
 else:assert env['episode'].collect_meta=={} and env['paths']==[]
sources={str(p):sha(p) for p in S.iterdir() if p.is_file()};sources.update({str(p):sha(p) for p in [Path(__file__),P/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py',W/'front_corridor_lateral_physical_r1/PROTOCOL.json']})
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,default_exact_parent_ast=True,parser_cases=parsers,invalid_parser_rejections=negative,factory=factory,native_metadata_and_archive=True,source_sha256=sources,passed=True,full_runtime_chain_pending=True,physics_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parser_commands=len(parsers),negative_rejections=len(negative),native_factory_cases=len(factory),physics_started=False)),flush=True)
