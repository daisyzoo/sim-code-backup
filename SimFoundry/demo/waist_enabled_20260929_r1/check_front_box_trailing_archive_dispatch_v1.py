"""Execute collector archive and task-dispatch branches without physics.
Checks source completeness and isolation of the new right-front recovery.
Does not assert contact success, task success, or training admission.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,sys,json,hashlib,datetime,copy,contextlib,io,inspect
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v1';D=W/'front_box_trailing_preparation_r1';P=W/'staged_joint_transport_reserve_v1'
sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from front_box_trailing_stage_source_binding_v1 import verify_preparation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected,bound=verify_preparation();collector=S/'collect_paired_sorting.py';tree=ast.parse(collector.read_text());nodes=list(ast.walk(tree));test=lambda n:ast.unparse(n.test) if isinstance(n,ast.If) else ''
code=lambda ns:compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(ns),type_ignores=[])),str(collector),'exec')
main=next(n for n in nodes if isinstance(n,ast.FunctionDef) and any(isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='paths' for z in x.targets) for x in n.body))
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='paths' for z in n.targets))
end=next(i for i,n in enumerate(main.body) if i>start and isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='path')
archive_code=code(main.body[start:end])
left=next(n for n in nodes if test(n)=="args.front_recontact_center_landing and side == 'left'")
right=next(n for n in nodes if test(n)=="args.front_box_recenter and side == 'right'")
parents={id(c):n for n in nodes for c in ast.iter_child_nodes(n)};anc=[];n=right
while id(n) in parents:
 n=parents[id(n)]
 if isinstance(n,ast.If):anc.append(ast.unparse(n.test))
assert 'front_route_selected' in anc and "args.expert_frontal_bypass and task_id != 'wait_no_package'" in anc
assert not any(isinstance(n,ast.Name) and n.id=='front_recontact_runtime' and isinstance(n.ctx,ast.Store) for n in nodes if isinstance(n,ast.Assign) and n.lineno>right.end_lineno and n.lineno<1005)
plan=W/'joint_transport_reserve_physical_preparation_r1/PLAN.json';cli=json.loads(plan.read_text())['commands'][0]['args'];all_sources=dict(bound);all_sources.update({str(p):sha(p) for p in [Path(__file__),plan,collector]});rows=[];guard=ClearanceGuard(ROOT,S)
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';rec=next(r for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r.get('planning'));scene=rec['context']['scene'];decay=rec['context']['decay'];all_sources[str(ep/'front_recontact_center.json')]=sha(ep/'front_recontact_center.json')
for enabled in [False,True]:
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):parsed,_=parser_namespace(collector,cli+(['--front-box-trailing-landing'] if enabled else []),full=True)
 args=SimpleNamespace(**parsed);sys.path[:0]=[str(S),str(W),str(ROOT)]
 env=dict(args=args,ROOT=ROOT,STAGE=S,Path=Path,json=json,__file__=str(collector),waist_admission=None);exec(archive_code,env);paths=set(env['paths']);stage={p.name:sha(p) for p in paths if p.parent==S};want={n:h for n,h in expected.items() if enabled or not n.startswith('trailing_')};assert stage==want,(set(stage)-set(want),set(want)-set(stage))
 for p in paths:assert p.is_file();all_sources[str(p)]=sha(p)
 # Every direct local import from all six new helpers must be archived.
 for name in [x for x in expected if x.startswith('trailing_')]:
  for n in ast.walk(ast.parse((S/name).read_text())):
   names=([n.module] if isinstance(n,ast.ImportFrom) and n.module else [x.name for x in n.names] if isinstance(n,ast.Import) else [])
   for module in names:
    p=S/(module.split('.')[0]+'.py')
    if p.exists() and enabled:assert p in paths,(name,p)
 branches=[]
 for task,side,front in [('push_box_to_bin','right',True),('nudge_mailer_to_bin','left',True),('push_box_to_bin','right',False),('nudge_mailer_to_bin','left',False),('wait_no_package','left',False)]:
  # Execute actual ancestor conditions relevant to dispatch, preserving original branch bodies.
  wrapped=ast.If(test=ast.parse("args.expert_frontal_bypass and task_id != 'wait_no_package' and front_route_selected and args.front_initial_center_landing",mode='eval').body,body=[copy.deepcopy(left),copy.deepcopy(right)],orelse=[])
  env=dict(args=args,side=side,task_id=task,front_route_selected=front,front_recontact_runtime=None,frontal_plan={},clearance_guard=guard,edge_size=scene['core_size'],obstacle_size=scene['other_size'],parameters={'tasks':{task:{'decay':decay}}})
  exec(code([wrapped]),env);rt=env['front_recontact_runtime'];want_name=None if not front else ('trailing_runtime.py' if side=='right' and enabled else 'front_box_recenter_runtime.py' if side=='right' else 'front_recontact_center_runtime.py');actual=None if rt is None else Path(inspect.getfile(type(rt))).name;assert actual==want_name,(enabled,task,front,actual,want_name)
  branches.append(dict(task=task,front=front,runtime=actual))
 rows.append(dict(enabled=enabled,archived_stage_sources=len(stage),archived_unique_sources=len(paths),branches=branches))
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,dispatch_ancestor_conditions=anc,source_sha256=all_sources,physical_started=False,training_ready=False)
with (D/'ARCHIVE_DISPATCH_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},ensure_ascii=False),flush=True)
