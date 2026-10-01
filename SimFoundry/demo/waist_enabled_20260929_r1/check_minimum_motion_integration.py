"""Actual default-off collector, lifecycle, plan/raw/source archive integration.
No AppLauncher or physical run. Existing parent files stay unchanged.
"""
from pathlib import Path
import ast,argparse,types,json,hashlib,datetime,copy
w=Path(__file__).resolve().parent;parent=w/'staged_precise_parent_seed';stage=w/'staged_minimum_motion_recontact';flag='minimum_motion_recontact';path=stage/'collect_paired_sorting.py';tree=ast.parse(path.read_text())
class Strip(ast.NodeTransformer):
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='--minimum-motion-recontact' for a in node.value.args):return None
  return self.generic_visit(node)
 def visit_If(self,node):
  if any(isinstance(x,ast.Attribute) and x.attr==flag for x in ast.walk(node.test)):return None
  return self.generic_visit(node)
assert ast.dump(Strip().visit(copy.deepcopy(tree)))==ast.dump(ast.parse((parent/path.name).read_text()))
changed=[p.name for p in parent.glob('*.py') if p.read_bytes()!=(stage/p.name).read_bytes()];assert set(changed)=={'collect_paired_sorting.py','recontact_plan.py'}
lifecycle=ast.parse((stage/'minimum_motion_lifecycle.py').read_text());calls=[n for n in ast.walk(lifecycle) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='plan'];assert len(calls)==1 and calls[0].keywords[-1].arg=='minimum_motion_pose' and ast.literal_eval(calls[0].keywords[-1].value) is True;calls[0].keywords.pop();assert ast.dump(lifecycle)==ast.dump(ast.parse((parent/'recontact_lifecycle.py').read_text()))
for p in stage.glob('*.py'):compile(p.read_text(),str(p),'exec')
opt=next(n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='--minimum-motion-recontact' for a in n.value.args));parser=argparse.ArgumentParser();exec(compile(ast.Module(body=[opt],type_ignores=[]),str(path),'exec'),{'parser':parser});assert vars(parser.parse_args([]))[flag] is False and vars(parser.parse_args(['--minimum-motion-recontact']))[flag] is True
ifs=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(x,ast.Attribute) and x.attr==flag for x in ast.walk(n.test))];assert len(ifs)==5;guard=next(n for n in ifs if isinstance(n.test,ast.BoolOp));guard_code=compile(ast.Module(body=[guard],type_ignores=[]),str(path),'exec')
base=dict(minimum_motion_recontact=True,rear_joint_edge_parent_seed_retry=True,rear_joint_edge_analytic_retry=True,precise_clearance_task_ik=True,recontact_interior_preference=True,unloaded_recontact_pose=True,role='diagnostic',policy_port=None,waist_probe=False,idle=False)
def check(a):exec(guard_code,dict(args=types.SimpleNamespace(**a)))
check(base);check(dict(base,minimum_motion_recontact=False,rear_joint_edge_parent_seed_retry=False));bad=[]
for k,v in [('rear_joint_edge_parent_seed_retry',False),('rear_joint_edge_analytic_retry',False),('precise_clearance_task_ik',False),('recontact_interior_preference',False),('unloaded_recontact_pose',False),('role','pilot'),('policy_port',9999),('waist_probe',True),('idle',True)]:
 try:check(dict(base,**{k:v}))
 except ValueError:bad.append(k)
 else:raise AssertionError(k)
select=next(n for n in ifs if isinstance(n.body[0],ast.ImportFrom));assert select.body[0].module=='minimum_motion_lifecycle' and select.body[0].names[0].name=='RecontactLifecycle'
for enabled in [False,True]:
 env=dict(args=types.SimpleNamespace(**dict(base,minimum_motion_recontact=enabled)),frontal_plan={'unloaded_recontact_pose':{}},episode=types.SimpleNamespace(collect_meta={}),paths=[],STAGE=stage)
 for n in ifs:
  if n is not guard and n is not select:exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),env)
 assert ('minimum_motion_pose' in env['frontal_plan']['unloaded_recontact_pose']) is enabled and (flag in env['episode'].collect_meta) is enabled
 assert env['paths']==([stage/'minimum_motion_recontact.py',stage/'minimum_motion_lifecycle.py'] if enabled else [])
 if enabled:assert env['frontal_plan']['unloaded_recontact_pose']['minimum_motion_pose']['maximum_ticks']==240 and env['episode'].collect_meta[flag] is True
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources=[Path(__file__),parent/'collect_paired_sorting.py',parent/'recontact_lifecycle.py',w/'parent_seed_groups_r1/RESULT.json']+list(stage.glob('*.py'));out=dict(passed=True,scope=__doc__,default_off_collector_ast_exact=True,lifecycle_only_plan_keyword_changed=True,changed_parent_files=changed,actual_default_false=True,unsupported_modes_rejected=bad,actual_plan_raw_and_archive_checked=True,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,versioned_auditors_ready=False,full_run_protocol_ready=False,training_ready=False);(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS default-off collector, lifecycle, metadata/archive,9 unsupported configurations')
