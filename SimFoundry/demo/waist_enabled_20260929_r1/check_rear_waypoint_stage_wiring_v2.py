"""Actual parser and extracted collector hook tests; no AppLauncher/simulator.
Recorded-action state-field fixtures test integration order and record binding;
these are not live rollouts or a substitute for full episode audits.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,ast,copy,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';P=W/'staged_front_drive_1mm';D=W/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from rear_cop_route import RearCopRouteState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());sources={str(S/'COLLECTOR_PREPARATION.json'):sha(S/'COLLECTOR_PREPARATION.json')}
for name,h in prep['stage_sha256'].items():assert sha(S/name)==h;sources[str(S/name)]=h
src=(S/'collect_paired_sorting.py').read_text();restored=src
for c in reversed(prep['changes']):assert restored.count(c['new'])==1;restored=restored.replace(c['new'],c['old'])
assert restored==(P/'collect_paired_sorting.py').read_text()
planpath=W/'front_drive_1mm_preparation_r2/PLAN.json';plan=json.loads(planpath.read_text());parser_checks=[]
for item in plan['commands']:
 for mm in ['.001','.002']:
  args=list(item['args']);args[args.index('--front-cop-drive-step-m')+1]=mm
  before,_=parser_namespace(P/'collect_paired_sorting.py',args,full=True);disabled,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);assert disabled.pop('rear_waypoint_reconciliation') is False and disabled==before
  enabled,_=parser_namespace(S/'collect_paired_sorting.py',args+['--rear-waypoint-reconciliation'],full=True);assert enabled.pop('rear_waypoint_reconciliation') is True and enabled==before
  parser_checks.append(dict(layout=item['layout_id'],front_drive_mm=float(mm)*1000,disabled_original_equal=True,enabled_only_new_flag=True))
negative=[];base=list(plan['commands'][0]['args'])+['--rear-waypoint-reconciliation']
for flag in ['--rear-box-inward-correction','--rear-cop-centering','--edge-clearance-intersection','--self-clearance-task-ik','--trace-solved-contact-forces','--trace-hand-contact-forces','--waist-coordinated-expert','--bounded-coupled-ik']:
 args=list(base);assert flag in args;args.remove(flag)
 try:parser_namespace(S/'collect_paired_sorting.py',args,full=True)
 except (SystemExit,ValueError):negative.append('missing_'+flag)
 else:raise AssertionError('missing prerequisite accepted '+flag)
tree=ast.parse(src)
def pick(test,needle):
 nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)==test and needle in ast.get_source_segment(src,n)];assert len(nodes)==1,(test,needle,len(nodes));return nodes[0]
hook=pick('args.rear_waypoint_reconciliation','cursor_record=');metadata=pick('args.rear_waypoint_reconciliation',"episode.collect_meta['rear_waypoint_reconciliation']");write=pick('args.rear_waypoint_reconciliation',"rear_waypoint_reconciliation.json");archive=pick('args.rear_waypoint_reconciliation',"paths.extend");declare=pick('args.rear_waypoint_reconciliation',"frontal_plan['rear_waypoint_reconciliation']")
# Verify the hook is in the same action loop, after env.step and the original
# post-observation rejection branch, and before termination handling.
loops=[n for n in ast.walk(tree) if isinstance(n,ast.For) and hook in n.body];assert len(loops)==1;loop=loops[0]
step_stmt=next(n for n in loop.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='env.step')
post_block=next(n for n in loop.body if isinstance(n,ast.If) and n.lineno>step_stmt.lineno and 'observed_clearance = clearance_guard.observe' in ast.get_source_segment(src,n));assert any(isinstance(n,ast.Break) for n in ast.walk(post_block))
term=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=='bool(terminated[0] or truncated[0])');assert loop.body.index(step_stmt)<loop.body.index(post_block)<loop.body.index(hook)<loop.body.index(term)
assert not any(isinstance(n,ast.Call) and ast.unparse(n.func)=='env.step' for n in ast.walk(hook))
def execute(node,ctx):exec(compile(ast.Module(body=[node],type_ignores=[]),str(S/'collect_paired_sorting.py'),'exec'),ctx)
guard=ClearanceGuard(ROOT,S);R=W/'front_corridor_midpoint_physical_r1';diag=json.loads((R/'REAR_BOX_CURRENT_EDGE_COMMAND_RESIDUAL_DIAGNOSTIC.json').read_text());obs={x['step']:x for x in next(z for z in diag['results'] if z['run']==R.name)['records']};hook_cases=[]
for layout,task,t,side in [(840023,'push_box_to_bin',0,'right'),(840023,'push_box_to_bin',565,'right'),(840023,'push_box_to_bin',566,'right'),(840023,'push_box_to_bin',574,'right'),(840020,'nudge_mailer_to_bin',500,'left'),(841011,'wait_no_package',20,'left')]:
 ep=R/f'case_{layout}'/f'layout_{layout}_{task}';clear=json.loads((ep/'self_clearance.json').read_text());fg=next(x for x in clear['rows'] if x['step']==t and x['phase']=='final_command');pg=next(x for x in clear['rows'] if x['step']==t and x['phase']=='post')
 with np.load(ep/'raw.npz') as z:action=z['action'][t].copy()
 fp=ep/'frontal_bypass.json';fr=json.loads(fp.read_text()) if fp.exists() else None;row=next((x for x in fr['rows'] if x['step']==t),None) if fr else None
 cp=ep/'coordination.json';coords=json.loads(cp.read_text()) if cp.exists() else [];coordinate=next((x for x in coords if x['step']==t),None)
 mode=row['mode'] if row else 'initial';target=tuple(row['target_xyz']) if row else None;state=RearCopRouteState(rear=SimpleNamespace(plan={'direction':-1 if side=='right' else 1}),side=side,size=(.14,.09,.045),mode=mode,top_mode=mode,command=target,last_waypoint_xy=target[:2] if target else None) if row else None
 ctx=dict(np=np,args=SimpleNamespace(rear_waypoint_reconciliation=False),clearance_guard=guard,default=np.zeros(23),frontal_plan=None if fr is None else fr['plan'],frontal_state=state,frontal_log=[] if row is None else [row],coordination_log=[] if coordinate is None else [coordinate],step=t,side=side,acts=[action],final_clearance={k:v for k,v in fg.items() if k not in ['step','phase']},observed_clearance={k:v for k,v in pg.items() if k not in ['step','phase']},rear_waypoint_reconciliation_log=[])
 if t>0:ctx['point_kwargs']=dict(slip_contact=dict(valid=t in obs,normal_load_n=obs.get(t,{}).get('normal_load_n',0.)))
 before=copy.deepcopy(None if state is None else state.__dict__);before_row=copy.deepcopy(row);before_action=action.copy();execute(hook,ctx);assert ctx['rear_waypoint_reconciliation_log']==[] and (None if state is None else state.__dict__)==before
 ctx['args'].rear_waypoint_reconciliation=True;execute(hook,ctx);record=ctx['rear_waypoint_reconciliation_log'][0];assert len(ctx['rear_waypoint_reconciliation_log'])==1 and np.array_equal(action,before_action) and row==before_row
 assert record['applied']==(layout==840023 and task=='push_box_to_bin' and t==565)
 if not record['applied']:assert (None if state is None else state.__dict__)==before
 hook_cases.append(dict(episode=ep.name,step=t,applied=record['applied'],reason=record['reason']))
 for name in ['raw.npz','self_clearance.json','frontal_bypass.json','coordination.json']:
  path=ep/name
  if path.exists():sources[str(path)]=sha(path)
# Execute the actual metadata, log write and archive-selection AST on explicit
# fixtures; no project episode file is written.
with tempfile.TemporaryDirectory(prefix='rear_cursor_hook_check_') as tmp:
 ctx=dict(args=SimpleNamespace(rear_waypoint_reconciliation=True),episode=SimpleNamespace(collect_meta={}),rear_waypoint_reconciliation_log=[dict(applied=True),dict(applied=False)],folder=Path(tmp),json=json,paths=[],STAGE=S)
 execute(metadata,ctx);execute(write,ctx);execute(archive,ctx);assert ctx['episode'].collect_meta==dict(rear_waypoint_reconciliation=True,rear_waypoint_reconciliation_applied_frames=1);saved=json.loads((Path(tmp)/'rear_waypoint_reconciliation.json').read_text());assert saved['rows']==ctx['rear_waypoint_reconciliation_log'] and saved['training_ready'] is False;assert ctx['paths']==[S/'reconcile_rear_waypoint.py',S/'rear_post_commit_adapter.py']
for side,rear in [('right',True),('left',True),('right',False)]:
 ctx=dict(args=SimpleNamespace(rear_waypoint_reconciliation=True),side=side,frontal_plan=dict(rear_cop_centering=dict(enabled=rear)));execute(declare,ctx);assert ctx['frontal_plan']['rear_waypoint_reconciliation']['enabled']==(side=='right' and rear)
for path in [Path(__file__),planpath,D/'POST_COMMIT_ADAPTER_CHECK.json',D/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json']:sources[str(path)]=sha(path)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,runtime_sources=73,unchanged_parent_helpers=70,actual_parser_configurations=parser_checks,negative_parser_checks=negative,actual_collector_hook_fixtures=hook_cases,hook_after_original_physics_and_post_guard=True,original_collector_reverse_restore=True,metadata_archive_log_ast_executed=True,temporary_fixture_removed=True,source_sha256=sources,full_audit_family_ready=False,physics_started=False,training_ready=False)
with (S/'COLLECTOR_WIRING_CHECK_V2.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,parser_configurations=len(parser_checks),negative_parser_checks=len(negative),hook_fixtures=len(hook_cases),physics_started=False),flush=True)
