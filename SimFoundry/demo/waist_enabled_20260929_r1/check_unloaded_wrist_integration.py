"""Actual default-off AST equality and CLI/source wiring for wrist prior candidate."""
from pathlib import Path
import ast,copy,types,json,hashlib
w=Path(__file__).resolve().parent;parent=w/'staged_rear_short_recovery';stage=w/'staged_unloaded_wrist_prior';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='unloaded_wrist_prior' or isinstance(x,ast.Name) and x.id=='wrist_prior_context' for x in ast.walk(n.test)):
   assert not n.orelse;return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  c=n.value
  if isinstance(c,ast.Call) and c.args and isinstance(c.args[0],ast.Constant) and c.args[0].value=='--unloaded-wrist-prior':return None
  return self.generic_visit(n)
 def visit_arguments(self,n):
  for i in reversed(range(len(n.kwonlyargs))):
   if n.kwonlyargs[i].arg=='wrist_prior_context':assert isinstance(n.kw_defaults[i],ast.Constant) and n.kw_defaults[i].value is None;n.kwonlyargs.pop(i);n.kw_defaults.pop(i)
  return self.generic_visit(n)
for name in ['collect_paired_sorting.py','waist_coordination_clearance.py']:
 a=ast.parse((parent/name).read_text());b=ast.parse((stage/name).read_text());assert ast.dump(a)==ast.dump(Strip().visit(copy.deepcopy(b))),name
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','waist_coordination_clearance.py']:assert sha(p)==sha(stage/p.name)
assert sha(stage/'unloaded_wrist_prior.py')==sha(w/'staged_unloaded_wrist_prior_probe/unloaded_wrist_prior.py')
a=ast.parse((stage/'collect_paired_sorting.py').read_text());guard=next(n for n in a.body if isinstance(n,ast.If) and 'args.unloaded_wrist_prior and' in ast.unparse(n.test));cfg=dict(unloaded_wrist_prior=True,rear_short_recovery=True,self_clearance_task_ik=True,rear_joint_xy_progress=True,expert_top_contact_normal_hold=True,role='diagnostic',waist_coordinated_expert=True,bounded_coupled_ik=True,policy_port=0,waist_probe=False,idle=False)
class Parser:
 def error(self,msg):raise ValueError(msg)
checks=[]
for key,value in [('valid',None),('unloaded_wrist_prior',False)]+[(k,False) for k in ['rear_short_recovery','self_clearance_task_ik','rear_joint_xy_progress','expert_top_contact_normal_hold','waist_coordinated_expert','bounded_coupled_ik']]+[('role','train'),('policy_port',8000),('waist_probe',True),('idle',True)]:
 c=cfg.copy()
 if key!='valid':c[key]=value
 rejected=False
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),'<actual guard>','exec'),dict(args=types.SimpleNamespace(**c),parser=Parser()))
 except ValueError:rejected=True
 assert rejected==(key not in ['valid','unloaded_wrist_prior']);checks.append(dict(case=key,rejected=rejected))
archive=next(n for n in ast.walk(a) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_wrist_prior' and any(isinstance(x,ast.Name) and x.id=='paths' for x in ast.walk(n)))
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(unloaded_wrist_prior=enabled),paths=[],STAGE=stage);exec(compile(ast.Module(body=[archive],type_ignores=[]),'<actual archive>','exec'),ns);assert ns['paths']==([stage/'unloaded_wrist_prior.py',stage/'unloaded_wrist_task.py'] if enabled else [])
report=dict(passed=True,default_off_collector_and_coordination_ast_exact=True,unchanged_original_helpers=True,argument_checks=checks,actual_archive_switch_checked=True,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),parent/'collect_paired_sorting.py',parent/'waist_coordination_clearance.py',stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',stage/'unloaded_wrist_prior.py',stage/'unloaded_wrist_task.py']},physical_validation=False,training_ready=False)
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(report,indent=2));print('passed default-off AST,',len(checks),'CLI branches, actual archival switch')
