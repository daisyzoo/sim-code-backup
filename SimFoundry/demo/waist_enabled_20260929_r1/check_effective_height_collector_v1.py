"""Actual parser/factory/metadata/archive check and default-off AST identity; no physics."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,contextlib,io,json,sys,inspect,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'staged_front_loaded_z_quarter_v1';S=W/'staged_front_effective_height_v1';D=W/'front_effective_height_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());tree=ast.parse((S/'collect_paired_sorting.py').read_text());old=ast.parse((P/'collect_paired_sorting.py').read_text());flag='joint_transport_effective_quarter_height';cli_flag='--joint-transport-effective-quarter-height'
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.'+flag in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  v=n.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value==cli_flag:return None
  return self.generic_visit(n)
assert ast.dump(RemoveNew().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(old,include_attributes=False)
protocol=read(W/'front_loaded_z_quarter_physical_r2/PROTOCOL.json');cases=[]
def parsed(path,cli):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(path,cli,full=True)[0]
 finally:sys.path[:]=before
for c in protocol['plan']['commands']:
 base=parsed(P/'collect_paired_sorting.py',c['args']);off=parsed(S/'collect_paired_sorting.py',c['args']);assert off.pop(flag) is False and off==base
 on=parsed(S/'collect_paired_sorting.py',c['args']+[cli_flag]);assert on.pop(flag) is True and on==base;cases.append(dict(layout_id=c['layout_id'],default_exact=True,enabled_only_new_flag=True))
base=protocol['plan']['commands'][0]['args'];bad=[]
invalid=[('missing_quarter',[x for x in base if x!='--front-loaded-z-quarter']),('missing_priority',[x for x in base if x!='--front-loaded-z-priority']),('missing_transport',[x for x in base if x!='--joint-transport-clearance']),('policy',base+['--policy-port','8000']),('idle',base+['--idle']),('waist_probe',base+['--waist-probe']),('pilot',base+['--role','pilot'])]
for name,cli in invalid:
 try:parsed(S/'collect_paired_sorting.py',cli+[cli_flag])
 except SystemExit as e:assert e.code!=0;bad.append(name)
 else:raise AssertionError('invalid config accepted '+name)
from clearance_runtime import ClearanceGuard
from joint_transport_runtime import JointTransportRuntime,SPEC
assert Path(inspect.getfile(ClearanceGuard)).resolve()==S/'clearance_runtime.py';guard=ClearanceGuard(ROOT,S)
block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.joint_transport_clearance' and 'transport_command' in ast.unparse(n))
factories=[n for n in block.body if isinstance(n,ast.If) and ast.unparse(n.test) in ['args.'+flag+' and joint_transport_controller is None','joint_transport_controller is None']];assert len(factories)==2
program=compile(ast.fix_missing_locations(ast.Module(body=factories,type_ignores=[])),'<native factory>','exec');checks=[]
for enabled in [False,True]:
 env=dict(args=NS(**{flag:enabled}),joint_transport_controller=None,JointTransportRuntime=JointTransportRuntime,clearance_guard=guard,ROOT=ROOT,STAGE=S)
 exec(program,env);obj=env['joint_transport_controller'];expected=S/('joint_transport_effective_height_runtime_v1.py' if enabled else 'joint_transport_runtime.py');assert Path(inspect.getfile(type(obj))).resolve()==expected
 assert getattr(obj,'effective_quarter_height',False) is enabled
 before=obj;exec(program,env);assert env['joint_transport_controller'] is before;checks.append(dict(enabled=enabled,module=str(expected),reuses_controller=True))
meta=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.'+flag and 'episode.collect_meta' in ast.unparse(n));archive=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.'+flag and 'paths.extend' in ast.unparse(n));prep=read(D/'STAGE_PREPARATION.json')
for enabled in [False,True]:
 env=dict(args=NS(**{flag:enabled}),episode=NS(collect_meta={}),JOINT_TRANSPORT_SPEC=SPEC,paths=[],STAGE=S)
 for node in [meta,archive]:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<native metadata/archive>','exec'),env)
 if enabled:
  assert env['episode'].collect_meta[flag] is True;assert env['paths']==[S/n for n in prep['helpers']];assert env['JOINT_TRANSPORT_SPEC']==dict(SPEC,version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True,contact_height_target='verified_effective_quarter_task',original_full_task_objective=True,original_height_tolerance_m=2e-7)
 else:assert env['episode'].collect_meta=={} and env['paths']==[] and env['JOINT_TRANSPORT_SPEC'] is SPEC
 assert SPEC['version']=='joint_transport_clearance_reserve_v1'
sources={str(p):sha(p) for p in S.iterdir() if p.is_file()};sources.update({str(p):sha(p) for p in [Path(__file__),P/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py',W/'front_loaded_z_quarter_physical_r2/PROTOCOL.json']})
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,default_exact_parent_ast=True,parser_cases=cases,invalid_parser_rejections=bad,factory=checks,native_metadata_and_archive=True,source_sha256=sources,physics_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parser_commands=len(cases),negative_rejections=len(bad),native_factory_cases=len(checks),physics_started=False)))
