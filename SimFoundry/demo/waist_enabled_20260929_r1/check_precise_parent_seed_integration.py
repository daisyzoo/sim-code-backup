"""Isolated collector wiring, actual new option/guard/metadata; not a simulator run."""
from pathlib import Path
import ast,argparse,types,json,hashlib,datetime,contextlib,io
w=Path(__file__).resolve().parent;parent=w/'staged_interior_task_precision';stage=w/'staged_precise_parent_seed';probe=w/'staged_rear_edge_parent_seed_probe';flag='rear_joint_edge_parent_seed_retry';path=stage/'collect_paired_sorting.py';tree=ast.parse(path.read_text())
class Strip(ast.NodeTransformer):
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='--rear-joint-edge-parent-seed-retry' for x in node.value.args):return None
  return self.generic_visit(node)
 def visit_If(self,node):
  if any(isinstance(x,ast.Attribute) and x.attr==flag for x in ast.walk(node.test)):return None
  return self.generic_visit(node)
 def visit_Call(self,node):
  if isinstance(node.func,ast.Name) and node.func.id=='refine_record':node.keywords=[k for k in node.keywords if k.arg!='parent_seed_retry']
  return self.generic_visit(node)
assert ast.dump(Strip().visit(ast.parse(path.read_text())),include_attributes=False)==ast.dump(ast.parse((parent/path.name).read_text()),include_attributes=False)
changed=[]
for p in parent.iterdir():
 if not p.is_file():continue
 if p.read_bytes()!=(stage/p.name).read_bytes():changed.append(p.name)
assert set(changed)=={'collect_paired_sorting.py','joint_edge_command.py','joint_edge_adapter.py'}
for name in ['joint_edge_command.py','joint_edge_adapter.py']:assert (stage/name).read_bytes()==(probe/name).read_bytes()
for p in stage.glob('*.py'):compile(p.read_text(),str(p),'exec')
opt=next(n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='--rear-joint-edge-parent-seed-retry' for a in n.value.args))
parser=argparse.ArgumentParser();exec(compile(ast.Module(body=[opt],type_ignores=[]),str(path),'exec'),{'parser':parser});assert vars(parser.parse_args([]))[flag] is False and vars(parser.parse_args(['--rear-joint-edge-parent-seed-retry']))[flag] is True
ifs=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(x,ast.Attribute) and x.attr==flag for x in ast.walk(n.test))];assert len(ifs)==3
guard=next(n for n in ifs if isinstance(n.test,ast.BoolOp));guard_code=compile(ast.Module(body=[guard],type_ignores=[]),str(path),'exec')
base=dict(rear_joint_edge_parent_seed_retry=True,rear_joint_edge_analytic_retry=True,precise_clearance_task_ik=True,recontact_interior_preference=True,unloaded_recontact_pose=True,role='diagnostic',policy_port=None,waist_probe=False,idle=False)
def check(args):
 with contextlib.redirect_stderr(io.StringIO()):exec(guard_code,dict(args=types.SimpleNamespace(**args),parser=parser))
check(base);check(dict(base,rear_joint_edge_parent_seed_retry=False,rear_joint_edge_analytic_retry=False));bad=[]
for k,v in [('rear_joint_edge_analytic_retry',False),('precise_clearance_task_ik',False),('recontact_interior_preference',False),('unloaded_recontact_pose',False),('role','pilot'),('policy_port',9999),('waist_probe',True),('idle',True)]:
 try:check(dict(base,**{k:v}))
 except SystemExit as e:assert e.code==2;bad.append(k)
 else:raise AssertionError(k)
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='refine_record');kw=next(k.value for k in call.keywords if k.arg=='parent_seed_retry')
for enabled in [False,True]:
 args=types.SimpleNamespace(**dict(base,rear_joint_edge_parent_seed_retry=enabled));assert eval(compile(ast.Expression(kw),str(path),'eval'),dict(args=args)) is enabled
 env=dict(args=args,frontal_plan={},episode=types.SimpleNamespace(collect_meta={}))
 for n in ifs:
  if n is not guard:exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),env)
 assert (flag in env['frontal_plan']) is enabled and (flag in env['episode'].collect_meta) is enabled
 if enabled:assert env['frontal_plan'][flag]['maximum_extra_retries']==1 and env['episode'].collect_meta[flag] is True
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources=[Path(__file__),parent/'collect_paired_sorting.py',probe/'joint_edge_command.py',probe/'joint_edge_adapter.py',w/'precise_interior_groups_r1/RESULT.json']+list(stage.glob('*.py'))
out=dict(passed=True,scope=__doc__,default_off_collector_ast_exact=True,changed_parent_files=sorted(changed),helper_adapter_exact_verified_probe=True,actual_option_default_false=True,rejected_unsupported_modes=bad,actual_call_keyword_and_plan_raw_metadata_checked=True,source_sha256={str(p):sha(p) for p in sources},created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_archive_not_physically_executed=True,versioned_auditors_ready=False,full_run_protocol_ready=False,physical_validation=False,training_ready=False);(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS default-off AST, option/guard/plan/raw/call; unsupported',len(bad))
