"""Execute actual prelaunch parser and native factory/metadata/archive AST.
Default-off AST must reduce exactly to parent. No physics or full-prefix claim.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,contextlib,io,json,sys,inspect,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'staged_front_box_trailing_v2';S=W/'staged_rear_early_edge_v1';D=W/'rear_early_edge_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());tree=ast.parse((S/'collect_paired_sorting.py').read_text());old=ast.parse((P/'collect_paired_sorting.py').read_text())
prep=read(D/'STAGE_PREPARATION.json')
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.rear_early_edge' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Assign(self,n):
  if any(isinstance(t,ast.Name) and t.id=='REAR_EARLY_EDGE_SPEC' for t in n.targets):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  v=n.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value=='--rear-early-edge':return None
  return self.generic_visit(n)
assert ast.dump(RemoveNew().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(old,include_attributes=False)
protocol=read(W/'front_box_trailing_physical_r2/PROTOCOL.json');parsers=[]
def parsed(path,cli):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(path,cli,full=True)[0]
 finally:sys.path[:]=before
for c in protocol['plan']['commands']:
 baseline=parsed(P/'collect_paired_sorting.py',c['args']);off=parsed(S/'collect_paired_sorting.py',c['args']);assert off.pop('rear_early_edge') is False;assert off==baseline
 on=parsed(S/'collect_paired_sorting.py',c['args']+['--rear-early-edge']);assert on.pop('rear_early_edge') is True;assert on==baseline;parsers.append(dict(layout_id=c['layout_id'],default_exact=True,enabled_only_new_flag=True))
negative=[];base=protocol['plan']['commands'][0]['args']
cases=[('missing_'+f,[x for x in base if x!=f]) for f in ['--rear-joint-xy-progress','--rear-box-inward-correction','--precise-clearance-task-ik','--edge-clearance-intersection','--peak-load-bias-guard','--trace-substep-contacts']]+[('policy',base+['--policy-port','8000']),('idle',base+['--idle']),('probe',base+['--waist-probe']),('pilot',base+['--role','pilot'])]
for label,cli in cases:
 try:parsed(S/'collect_paired_sorting.py',cli+['--rear-early-edge'])
 except (SystemExit,ValueError) as e:
  if isinstance(e,SystemExit):assert e.code!=0
  negative.append(dict(case=label,rejected=True))
 else:raise AssertionError(('invalid early parser accepted',label))
def execute(nodes,env):exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec'),env)
specnode=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REAR_EARLY_EDGE_SPEC' for t in n.targets));spec=ast.literal_eval(specnode.value);assert spec==prep['spec']
factory=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_cop_centering' and 'top_cls = RearCopRouteState' in ast.unparse(n));factory_cases=[]
for enabled in [False,True]:
 for side in ['left','right']:
  env=dict(args=NS(rear_early_edge=enabled,rear_cop_centering=True,rear_slow_drag=True,rear_box_center_preference=True,rear_core_slice_feedback=True),side=side,actual_core=dict(collision_core_size_xyz=[.1344,.0864,.045]),frontal_plan={},top_extra={},REAR_EARLY_EDGE_SPEC=spec)
  execute([factory],env);active=enabled and side=='right';expected=S/('rear_cop_route_early.py' if active else 'rear_cop_route.py');assert Path(inspect.getfile(env['top_cls'])).resolve()==expected
  assert env['top_extra'].get('rear_early_edge_enabled',False)==active;assert bool(env['frontal_plan'].get('rear_early_edge'))==active
  if active:assert env['frontal_plan']['rear_early_edge']==spec
  factory_cases.append(dict(enabled=enabled,side=side,early_selected=active,class_module=str(expected)))
meta=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_early_edge' and "episode.collect_meta['rear_early_edge']" in ast.unparse(n));archive=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_early_edge' and 'paths.extend' in ast.unparse(n));metadata=[]
for enabled in [False,True]:
 for selected in [False,True]:
  env=dict(args=NS(rear_early_edge=enabled),episode=NS(collect_meta={}),frontal_plan={'rear_early_edge':spec} if selected else None,frontal_log=[{'rear_joint_xy_progress':{'early_edge':{'candidate_selected':x}}} for x in [True,False,True]] if selected else [],REAR_EARLY_EDGE_SPEC=spec,STAGE=S,paths=[])
  execute([meta,archive],env)
  if enabled:
   assert env['episode'].collect_meta==dict(rear_early_edge=spec,rear_early_edge_selected=selected,rear_early_edge_candidate_selected_frames=2 if selected else 0)
   assert env['paths']==[S/'rear_cop_route_early.py',S/'rear_early_edge_governor.py']
  else:assert env['episode'].collect_meta=={} and env['paths']==[]
  metadata.append(dict(enabled=enabled,selected=selected,native_metadata_and_archive_match=True))
sources={str(p):sha(p) for p in S.iterdir() if p.is_file()};sources.update({str(p):sha(p) for p in [Path(__file__),P/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py',W/'front_box_trailing_physical_r2/PROTOCOL.json']})
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,default_exact_parent_ast=True,parser_cases=parsers,invalid_parser_rejections=negative,native_factory_cases=factory_cases,native_metadata_and_archive_cases=metadata,source_sha256=sources,full_prefix_replay=False,audit_family_ready=False,physics_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,commands=len(parsers),negative=len(negative),factory_cases=len(factory_cases),metadata_cases=len(metadata))))
