"""Actual parser, metadata and archive nodes without AppLauncher."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,contextlib,datetime,hashlib,io,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v2';P=W/'staged_front_effective_height_v1';D=W/'front_normal_preparation_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=read(D/'STAGE_PREPARATION.json');protocol=read(W/'front_effective_height_physical_r1/PROTOCOL.json');flag='front_normal_nondegradation';cli='--front-normal-nondegradation'
def parse(p,args):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(p,args,full=True)[0]
 finally:sys.path[:]=before
rows=[]
for c in protocol['plan']['commands']:
 original=parse(P/'collect_paired_sorting.py',c['args']);off=parse(S/'collect_paired_sorting.py',c['args']);assert off.pop(flag) is False and off==original;on=parse(S/'collect_paired_sorting.py',c['args']+[cli]);assert on.pop(flag) is True and on==original;rows.append(dict(layout_id=c['layout_id'],tasks=c['tasks'],defaultoff_equal=True,only_flag_changed=True))
invalid=[]
for missing in ['--joint-transport-clearance','--joint-transport-effective-quarter-height','--front-loaded-z-quarter','--self-clearance-task-ik','--front-cop-route-axis']:
 a=list(protocol['plan']['commands'][0]['args']);a.remove(missing)
 try:parse(S/'collect_paired_sorting.py',a+[cli])
 except SystemExit as e:assert e.code!=0;invalid.append(missing)
 else:raise AssertionError(missing)
tree=ast.parse((S/'collect_paired_sorting.py').read_text());nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.'+flag];meta=next(n for n in nodes if 'episode.collect_meta' in ast.unparse(n));archive=next(n for n in nodes if 'paths.extend' in ast.unparse(n));e=dict(args=NS(**{flag:True}),episode=NS(collect_meta={}),normal_planning_log=[dict(applied=True),dict(applied=False)],paths=[],STAGE=S)
for node in [meta,archive]:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual metadata/archive>','exec'),e)
assert e['episode'].collect_meta['front_normal_planning_applied_frames']==1 and e['paths']==[S/name for name in prep['helpers']]
for key in ['parent_sources_sha256','stage_sources_sha256']:
 for p,h in prep[key].items():assert sha(p)==h,p
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,parser_cases=rows,invalid_prerequisites_rejected=invalid,actual_metadata_archive_checked=True,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'STAGE_PREPARATION.json',S/'collect_paired_sorting.py',W/'prepare_closed_peak_trial.py']},physics_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,commands=len(rows),invalid=len(invalid),physics_started=False)))
