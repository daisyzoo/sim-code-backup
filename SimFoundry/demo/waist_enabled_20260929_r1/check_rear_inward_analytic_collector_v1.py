"""Actual parser and native dispatch/metadata/archive checks; no App launch."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,contextlib,datetime,hashlib,inspect,io,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'staged_front_effective_height_v1';S=W/'staged_rear_inward_analytic_v1';D=W/'rear_inward_analytic_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=read(D/'STAGE_PREPARATION.json');flag='rear_inward_analytic_first';cli='--rear-inward-analytic-first'
def parse(path,args):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(path,args,full=True)[0]
 finally:sys.path[:]=before
protocol=read(W/'front_effective_height_physical_r1/PROTOCOL.json');cases=[]
for c in protocol['plan']['commands']:
 old=parse(P/'collect_paired_sorting.py',c['args']);off=parse(S/'collect_paired_sorting.py',c['args']);assert off.pop(flag) is False and off==old
 on=parse(S/'collect_paired_sorting.py',c['args']+[cli]);assert on.pop(flag) is True and on==old;cases.append(dict(layout_id=c['layout_id'],wait=c['wait'],tasks=c['tasks'],defaultoff_identical=True,enabled_changes_only_flag=True))
base=protocol['plan']['commands'][0]['args'];invalid=[]
for missing in ['--rear-box-inward-correction','--rear-joint-edge-command','--rear-joint-edge-analytic-retry','--rear-joint-edge-parent-seed-retry','--edge-clearance-intersection']:
 args=list(base);assert missing in args;args.remove(missing)
 try:parse(S/'collect_paired_sorting.py',args+[cli])
 except SystemExit as e:assert e.code!=0;invalid.append(missing)
 else:raise AssertionError('missing prerequisite accepted '+missing)
tree=ast.parse((S/'collect_paired_sorting.py').read_text());nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and 'args.'+flag in ast.unparse(n.test)]
meta=next(n for n in nodes if 'episode.collect_meta' in ast.unparse(n));archive=next(n for n in nodes if 'paths.extend' in ast.unparse(n));dispatch=next(n for n in nodes if 'from joint_edge_inward_analytic_adapter_v1' in ast.unparse(n));native=[]
for enabled in [False,True]:
 env=dict(args=NS(**{flag:enabled}),episode=NS(collect_meta={}),paths=[],STAGE=S)
 for node in [meta,archive]:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<native meta/archive>','exec'),env)
 if enabled:
  assert env['episode'].collect_meta[flag] is True
  spec=env['episode'].collect_meta[flag+'_spec'];assert spec['emitted_stationarity_max']==1e-6 and spec['original_solver_ftol']==1e-11 and spec['original_solver_maxiter']==300
  assert env['paths']==[S/name for name in prep['helpers']]
 else:assert env['episode'].collect_meta=={} and env['paths']==[]
 for side in ['left','right']:
  sentinel=object();d=dict(args=NS(**{flag:enabled}),side=side,refine_record=sentinel);exec(compile(ast.fix_missing_locations(ast.Module(body=[dispatch],type_ignores=[])),'<native dispatch>','exec'),d)
  selected=enabled and side=='right';assert (d['refine_record'] is not sentinel)==selected
  if selected:
   assert Path(inspect.getfile(d['refine_record'])).resolve()==S/'joint_edge_inward_analytic_adapter_v1.py'
   import joint_edge_inward_analytic_adapter_v1 as a
   assert a.refine_rear_command.keywords==dict(analytic_first=True)
   assert Path(inspect.getfile(a.refine_rear_command.func)).resolve()==S/'joint_edge_inward_analytic_first_candidate_v3.py'
  native.append(dict(enabled=enabled,side=side,new_adapter_selected=selected))
for p,h in prep['parent_sources_sha256'].items():assert sha(p)==h,p
for p,h in prep['stage_sources_sha256'].items():assert sha(p)==h,p
sources={str(p):sha(p) for p in [Path(__file__),D/'STAGE_PREPARATION.json',W/'prepare_closed_peak_trial.py',W/'front_effective_height_physical_r1/PROTOCOL.json']};sources.update(prep['stage_sources_sha256'])
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,parser_cases=cases,invalid_missing_prerequisite_rejections=invalid,native_dispatch=native,native_metadata_and_archive_checked=True,source_sha256=sources,physics_started=False,training_ready=False,remaining='Full native action chain, source/stream/all audit consumers and rejection lifecycle; no launch permission implied by this check.')
with (D/'COLLECTOR_WIRING_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,commands=len(cases),missing_prerequisites_rejected=len(invalid),native_dispatch_cases=len(native),physics_started=False)))
