"""Execute real parser and actual collector AST statements without simulation.
Remove only new flag-controlled additions to prove default-off parent AST identity.
Replay real recorded frames through actual action/log/final-guard statements.
A deliberately invalid injected controller tests the original stop-before-action
branch; it is explicitly synthetic, never represented as observed physics.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,contextlib,copy,datetime,hashlib,io,json,sys,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_z_priority';P=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from front_loaded_z_priority import FrontLoadedZPriority
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();script=S/'collect_paired_sorting.py';tree=ast.parse(script.read_text());original=ast.parse((P/'collect_paired_sorting.py').read_text());checks=[];sources={str(script):sha(script),str(P/'collect_paired_sorting.py'):sha(P/'collect_paired_sorting.py')}
class RemoveAdditions(ast.NodeTransformer):
 def visit_If(self,node):
  if 'args.front_loaded_z_priority' in ast.unparse(node.test):return None
  return self.generic_visit(node)
 def visit_Assign(self,node):
  if any(isinstance(t,ast.Name) and t.id in ['front_loaded_z_priority_controller','front_loaded_z_priority_log'] for t in node.targets):return None
  return self.generic_visit(node)
 def visit_Expr(self,node):
  v=node.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value=='--front-loaded-z-priority':return None
  return self.generic_visit(node)
restored=RemoveAdditions().visit(copy.deepcopy(tree));assert ast.dump(restored,include_attributes=False)==ast.dump(original,include_attributes=False);checks.append(dict(kind='default_off_exact_parent_ast_identity',passed=True))
protocol=json.loads((W/'front_initial_physical_r1/PROTOCOL.json').read_text());parser_rows=[]
for item in protocol['plan']['commands']:
 cli=item['args']
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  base,_=parser_namespace(P/'collect_paired_sorting.py',cli,full=True);off,_=parser_namespace(script,cli,full=True);on,_=parser_namespace(script,cli+['--front-loaded-z-priority'],full=True)
 assert off.pop('front_loaded_z_priority') is False and off==base;assert on.pop('front_loaded_z_priority') is True and on==base
 parser_rows.append(dict(layout_id=item['layout_id'],passed=True))
cli=protocol['plan']['commands'][0]['args']+['--front-loaded-z-priority'];bad=[]
for flag in ['--front-initial-center-landing','--precise-clearance-task-ik','--peak-load-bias-guard','--expert-top-contact-normal-hold']:
 bad.append((f'missing{flag}',[v for v in cli if v!=flag]))
for label,extra in [('policy',['--policy-port','1234']),('idle',['--idle']),('waist_probe',['--waist-probe']),('role',['--role','train'])]:bad.append((label,cli+extra))
neg=[]
for label,args in bad:
 rejected=False
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):parser_namespace(script,args,full=True)
 except (SystemExit,ValueError,AssertionError):rejected=True
 assert rejected,label;neg.append(dict(case=label,rejected=True))
block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and 'priority_command, priority_record' in ast.unparse(n));guardblock=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'final_clearance = clearance_guard.command(' in ast.unparse(n) and ast.unparse(n.test)=='clearance_guard is not None');prevnode=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='previous' for t in n.targets) and guardblock.lineno<n.lineno<guardblock.end_lineno+5)
assert block.end_lineno<guardblock.lineno<prevnode.lineno
loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(0)],ctx=ast.Load()),body=[block,guardblock,prevnode,ast.Assign(targets=[ast.Name(id='reached_after_final_guard',ctx=ast.Store())],value=ast.Constant(True))],orelse=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual loadedZ collector statements>','exec')
class Tensor:
 def __init__(self,x):self.value=np.asarray(x);self.torch=self
 def __getitem__(self,k):return Tensor(self.value[k])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.value

guard=ClearanceGuard(ROOT,S);actual=[]
for i,task,t,case in [(840020,'push_box_to_bin',181,'apply_box'),(840023,'nudge_mailer_to_bin',166,'apply_bag'),(840020,'push_box_to_bin',305,'reject_upward_fk'),(840023,'nudge_mailer_to_bin',286,'keep_original_z_met'),(840020,'push_box_to_bin',181,'disabled'),(840020,'push_box_to_bin',181,'no_capture'),(840020,'push_box_to_bin',181,'synthetic_invalid_proposal'),(841010,'wait_no_package',0,'wait_zero')]:
 ep=W/f'front_initial_physical_r1/case_{i}/layout_{i}_{task}';wait=case=='wait_zero';side='right' if 'push_box' in task else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box'
 with np.load(ep/'raw.npz') as z:q=z['q'][t].copy();parent=z['action'][t].copy();previous=z['action'][t-1].copy() if t else np.zeros(23,dtype=np.float32)
 c=next((r for r in json.loads((ep/'coordination.json').read_text()) if r['step']==t),None) if (ep/'coordination.json').exists() else None
 f=next((r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows'] if r['step']==t),None) if not wait else None
 with np.load(ep/'trace.npz') as z:xyz={k:z[k][t].copy() for k in ['box','mailer']}
 with np.load(ep/'parcel_orientation.npz') as z:quats={k:z[k][t].copy() for k in ['box','mailer']}
 scene={name:NS(data=NS(root_quat_w=Tensor(quats[k][None]))) for name,k in [('parcel_box','box'),('mailer','mailer')]};runtime=NS(center_local=None if case=='no_capture' else np.array(c['active_support_reference']['center_local'])) if not wait else None;control=FrontLoadedZPriority(guard)
 if case=='synthetic_invalid_proposal':
  class Invalid:
   def refine(self,**kwargs):
    x=np.array(kwargs['parent_command']);x[0]=10.;return x,dict(applied=True,step=t,synthetic=True,output_command=x.tolist())
  control=Invalid()
 env=dict(args=NS(front_loaded_z_priority=case!='disabled'),front_initial_runtime=runtime,front_loaded_z_priority_controller=control,front_loaded_z_priority_log=[],coordination_log=[] if c is None else [copy.deepcopy(c)],frontal_log=[] if f is None else [copy.deepcopy(f)],side=side,step=t,default=np.zeros(23),previous=previous.copy(),action=parent.copy(),robot=NS(data=NS(joint_pos=Tensor(q[None]))),ordered_ids=list(range(23)),env=NS(scene=scene),obstacle_size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045],parcel_xyz=lambda unused,actor:xyz['box' if actor=='parcel_box' else 'mailer'],clearance_guard=guard,clearance_rows=[],clearance_failure=None,reached_after_final_guard=False,np=np)
 exec(program,env)
 if case=='synthetic_invalid_proposal':
  assert not env['reached_after_final_guard'] and env['clearance_failure']['reason']=='final_override_not_verified' and np.array_equal(env['previous'],previous)
 else:
  assert env['reached_after_final_guard'] and env['clearance_failure'] is None;assert env['clearance_rows'][-1]['accepted'];assert np.array_equal(env['action'][:12],parent[:12]);assert np.array_equal(env['previous'],env['action'])
  if case in ['apply_box','apply_bag']:
   assert env['front_loaded_z_priority_log'][-1]['applied'] and not np.array_equal(env['action'][12:23],parent[12:23]);assert env['coordination_log'][-1]['waist_target_rad']==float(env['action'][12])
  else:assert np.array_equal(env['action'],parent)
  if case=='disabled':assert env['front_loaded_z_priority_log']==[]
 actual.append(dict(case=case,episode=ep.name,step=t,passed=True,reached_after_final_guard=env['reached_after_final_guard'],applied=False if not env['front_loaded_z_priority_log'] else env['front_loaded_z_priority_log'][-1]['applied'],evidence='synthetic invalid proposal only' if case=='synthetic_invalid_proposal' else 'archived parent observation, unissued candidate'))
# Execute real metadata/archive statements with a declared temporary fixture.
metablock=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and "episode.collect_meta['front_loaded_z_priority']" in ast.unparse(n));saveblock=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and "folder / 'front_loaded_z_priority.json'" in ast.unparse(n));sourceblock=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and 'paths.extend' in ast.unparse(n))
with tempfile.TemporaryDirectory(prefix='front_z_collector_fixture_') as tmp:
 fake=dict(args=NS(front_loaded_z_priority=True),episode=NS(collect_meta={}),front_loaded_z_priority_log=[dict(applied=True,synthetic=True),dict(applied=False,synthetic=True)],folder=Path(tmp),json=json,STAGE=S,paths=[])
 for node in [metablock,saveblock,sourceblock]:exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual metadata source archive>','exec'),fake)
 assert fake['episode'].collect_meta==dict(front_loaded_z_priority=True,front_loaded_z_priority_applied_frames=1);saved=json.loads((Path(tmp)/'front_loaded_z_priority.json').read_text());assert saved['rows']==fake['front_loaded_z_priority_log'] and saved['training_ready'] is False
 assert sorted(p.name for p in fake['paths'])==sorted(['front_loaded_z_priority.py','loaded_z_priority_solver.py','loaded_z_priority_checks.py','loaded_z_priority_stationarity.py']);assert all(p.exists() for p in fake['paths'])
checks.append(dict(kind='actual_metadata_and_source_archive_fixture',passed=True,physical_observation=False))
for p in S.iterdir():
 if p.is_file() and (p.suffix=='.py' or p.name in ['elbow_torso_hulls.json','causal_response_parameters.json']):sources[str(p)]=sha(p)
for p in [Path(__file__),W/'prepare_closed_peak_trial.py',W/'front_initial_physical_r1/PROTOCOL.json']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,parser=parser_rows,negative_parser=neg,actual_statements=actual,statement_order=[block.lineno,guardblock.lineno,prevnode.lineno],source_sha256=sources,passed=True,simulation_started=False,full_live_action_audit_still_required=True,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_COLLECTOR_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parser_commands=len(parser_rows),negative_parser=len(neg),actual_statement_cases=len(actual),simulation_started=False),indent=2))
