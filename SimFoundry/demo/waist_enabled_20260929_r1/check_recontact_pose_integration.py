"""Actual default-off AST/CLI/archive and original-helper source equivalence."""
from pathlib import Path
import ast,copy,types,json,hashlib
w=Path(__file__).resolve().parent;parent=w/'staged_rear_short_recovery';stage=w/'staged_recontact_pose';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='unloaded_recontact_pose' or isinstance(x,ast.Name) and x.id=='recontact_override' for x in ast.walk(n.test)):
   assert not n.orelse;return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  c=n.value
  if isinstance(c,ast.Call) and c.args and isinstance(c.args[0],ast.Constant) and c.args[0].value=='--unloaded-recontact-pose':return None
  return self.generic_visit(n)
 def visit_arguments(self,n):
  for i in reversed(range(len(n.kwonlyargs))):
   if n.kwonlyargs[i].arg=='recontact_override':assert isinstance(n.kw_defaults[i],ast.Constant) and n.kw_defaults[i].value is None;n.kwonlyargs.pop(i);n.kw_defaults.pop(i)
  return self.generic_visit(n)
for name in ['collect_paired_sorting.py','waist_coordination_clearance.py']:
 a=ast.parse((parent/name).read_text());b=ast.parse((stage/name).read_text());assert ast.dump(a)==ast.dump(Strip().visit(copy.deepcopy(b))),name
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','waist_coordination_clearance.py']:assert sha(p)==sha(stage/p.name)
for name in ['recontact_lifecycle.py','recontact_plan.py','recontact_scene.py','recontact_tracking.py']:assert sha(stage/name)==sha(w/'staged_recontact_pose_probe'/name)
a=ast.parse((stage/'collect_paired_sorting.py').read_text());guard=next(n for n in a.body if isinstance(n,ast.If) and 'args.unloaded_recontact_pose and' in ast.unparse(n.test));cfg=dict(unloaded_recontact_pose=True,rear_short_recovery=True,self_clearance_task_ik=True,rear_joint_xy_progress=True,region_causal_response=True,region_separate_measured_bounds=True,expert_top_contact_normal_hold=True,waist_coordinated_expert=True,bounded_coupled_ik=True,waist_limit_rad=1.0,role='diagnostic',policy_port=0,waist_probe=False,idle=False)
class Parser:
 def error(self,msg):raise ValueError(msg)
checks=[]
for key,value in [('valid',None),('unloaded_recontact_pose',False)]+[(k,False) for k in ['rear_short_recovery','self_clearance_task_ik','rear_joint_xy_progress','region_causal_response','region_separate_measured_bounds','expert_top_contact_normal_hold','waist_coordinated_expert','bounded_coupled_ik']]+[('waist_limit_rad',.8),('role','pilot'),('policy_port',8000),('waist_probe',True),('idle',True)]:
 c=cfg.copy()
 if key!='valid':c[key]=value
 rejected=False
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),'<actual CLI guard>','exec'),dict(args=types.SimpleNamespace(**c),parser=Parser()))
 except ValueError:rejected=True
 assert rejected==(key not in ['valid','unloaded_recontact_pose']);checks.append(dict(case=key,rejected=rejected))
archive=next(n for n in ast.walk(a) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose' and any(isinstance(x,ast.Name) and x.id=='paths' for x in ast.walk(n)))
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(unloaded_recontact_pose=enabled),paths=[],STAGE=stage);exec(compile(ast.Module(body=[archive],type_ignores=[]),'<actual archive>','exec'),ns);assert ns['paths']==([stage/name for name in ['recontact_tracking.py','recontact_scene.py','recontact_plan.py','recontact_lifecycle.py','recontact_adapter.py']] if enabled else [])
report=dict(passed=True,scope=__doc__,default_off_collector_and_coordinator_ast_exact=True,original_helper_sources_unchanged=True,argument_checks=checks,actual_archive_switch_checked=True,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',*[stage/n for n in ['recontact_tracking.py','recontact_scene.py','recontact_plan.py','recontact_lifecycle.py','recontact_adapter.py']]]},physical_validation=False,training_ready=False)
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(report,indent=2));print('default-off AST exact;',len(checks),'CLI branches; actual archive switch passed')
