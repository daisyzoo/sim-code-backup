"""Actual parser/state-selection/metadata/archive AST checks; no simulator launch.
Reject unsupported flags. Default-off uses identical state kwargs and metadata.
Bound existing route/IK evidence is reused only after checking all hashes.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,contextlib,copy,datetime,hashlib,inspect,io,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_midpoint_integrated';D=W/'staged_front_corridor_midpoint';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from front_initial_center_cop_route import FrontCopRouteState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();p=S/'collect_paired_sorting.py';prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
for name,h in prep['stage_sha256'].items():assert sha(S/name)==h,name
for name,h in prep['source_sha256'].items():assert sha(name)==h,name
restored=p.read_text()
for e in reversed(prep['edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(D/'collect_paired_sorting.py').read_text()
plan=W/'front_z_priority_physical_preparation_r1/PLAN.json';base=json.loads(plan.read_text())['commands'][0]['args'];flag='--front-corridor-midpoint-replan';rows=[];parsed={}
cases=[('off',base,True),('on',base+[flag],True)]
for required in ['--front-loaded-z-priority','--front-initial-center-landing','--front-diagonal-entry','--front-micro-repair-retention','--self-clearance-task-ik','--expert-top-contact-normal-hold']:
 assert required in base;cases.append(('missing_'+required,[x for x in base if x!=required]+[flag],False))
bad=list(base)+[flag];bad[bad.index('--role')+1]='pilot';cases.append(('wrong_role',bad,False))
for label,cli,expected in cases:
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):args,_=parser_namespace(p,cli,full=True)
  accepted=True
 except (ValueError,SystemExit):accepted=False
 assert accepted==expected,(label,accepted);rows.append(dict(case=label,accepted=accepted))
 if accepted:parsed[label]=SimpleNamespace(**args)
assert parsed['off'].front_corridor_midpoint_replan is False and parsed['on'].front_corridor_midpoint_replan is True
oldvars=vars(parsed['off']).copy();oldvars.pop('front_corridor_midpoint_replan')
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):oldargs,_=parser_namespace(D/'collect_paired_sorting.py',base,full=True)
assert oldvars==oldargs
collector=ast.parse(p.read_text());nodes=list(ast.walk(collector));select=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_initial_center_landing' and any(isinstance(v,ast.Name) and v.id=='CenterFrontState' for v in ast.walk(n)))
metadata=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_corridor_midpoint_replan' and any(isinstance(v,ast.Attribute) and v.attr=='collect_meta' for v in ast.walk(n)))
archive=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_initial_center_landing' and any(isinstance(v,ast.Name) and v.id=='paths' for v in ast.walk(n)))
def program(nodes):return compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(p),'exec')
ep=W/'front_z_priority_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());edge=fr['plan']['front_cop_slip_following']['edge_speed'];guard=ClearanceGuard(ROOT,S);selections=[]
for label in ['off','on']:
 env=dict(args=parsed[label],np=np,json=json,hashlib=hashlib,STAGE=S,side='left',task_id='nudge_mailer_to_bin',edge_size=np.asarray(edge['actual_core_size_xyz']),edge_core=edge['actual_core'],obstacle_size=[.14,.09,.045],clearance_guard=guard,frontal_plan={},top_extra={})
 exec(program([select]),env);assert env['top_cls'] is FrontCopRouteState
 kw=env['top_extra'];assert kw==({} if label=='off' else {'corridor_midpoint_replan':True})
 state=env['top_cls'](SimpleNamespace(plan=copy.deepcopy(fr['plan'])),'left',(.15,.145,.04),**kw);assert state.corridor_midpoint_replan==(label=='on')
 assert ('front_corridor_midpoint' in env['frontal_plan'])==(label=='on')
 # Real class identity and new dependency resolution, not merely matching names.
 assert Path(inspect.getfile(type(state))).parent==S
 assert Path(inspect.getfile(sys.modules['front_corridor_midpoint_runtime'])).parent==S
 meta=SimpleNamespace(collect_meta={});x=dict(args=parsed[label],episode=meta,frontal_log=[{},dict(front_corridor_midpoint=dict(changed=False)),dict(front_corridor_midpoint=dict(changed=True))]);exec(program([metadata]),x)
 assert meta.collect_meta==({} if label=='off' else dict(front_corridor_midpoint_replan=True,front_corridor_midpoint_replanned_frames=1))
 archive_env=dict(args=parsed[label],paths=[],STAGE=S);exec(program([archive]),archive_env);assert S/'front_corridor_midpoint_runtime.py' in archive_env['paths'];assert all(n.exists() for n in archive_env['paths'])
 selections.append(dict(flag=label,actual_class_kwargs=kw,metadata_checked=True,new_dependency_archived=True))
sources={str(p):sha(p) for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',plan,D/'DRAFT_CHECK.json',D/'SINGLE_STEP_JOINT_PROPOSAL_CHECK.json',ep/'frontal_bypass.json']};sources.update({str(S/n):h for n,h in prep['stage_sha256'].items()})
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parser_cases=rows,default_off_original_arguments_exact=True,actual_collector_ast_checks=selections,source_sha256=sources,complete_episode_replay_verified=False,new_route_audit_family_ready=False,physical_started=False,training_ready=False)
with (S/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
