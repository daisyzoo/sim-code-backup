"""Verify isolated default-off code and complete task/route flag selections.
No simulation or training approval. Whole original AST restored independently.
"""
from pathlib import Path
import ast,copy,json,hashlib
from types import SimpleNamespace
w=Path(__file__).resolve().parent;parent=w/'staged_rear_slow_drag';stage=w/'staged_box_center_preference';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dump=lambda n:ast.dump(n,include_attributes=False)
class StripCollector(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--rear-box-center-preference':return None
  return self.generic_visit(n)
 def visit_If(self,n):
  if 'args.rear_box_center_preference' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Assign(self,n):
  names=[ast.unparse(t) for t in n.targets]
  if names==['recontact_extra']:return None
  if names==['effective_drag_step_m']:
   n.value=ast.parse(".0015 if args.rear_slow_drag and frontal_plan.get('rear_cop_centering',{}).get('enabled',False) else args.expert_frontal_top_drag_step_m",mode='eval').body
  return self.generic_visit(n)
 def visit_keyword(self,n):
  if n.arg is None and ast.unparse(n.value)=='recontact_extra':return None
  if n.arg=='rear_slow_drag' and 'rear_box_center_preference' in ast.unparse(n.value):n.value=ast.parse('args.rear_slow_drag',mode='eval').body
  return self.generic_visit(n)
new=ast.parse((stage/'collect_paired_sorting.py').read_text());restored=StripCollector().visit(copy.deepcopy(new));assert dump(restored)==dump(ast.parse((parent/'collect_paired_sorting.py').read_text()))
life=ast.parse((stage/'minimum_motion_lifecycle.py').read_text());cls=next(n for n in life.body if isinstance(n,ast.ClassDef));init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');assert init.args.kwonlyargs[-1].arg=='box_center_preference';init.args.kwonlyargs.pop();init.args.kw_defaults.pop();init.body=[n for n in init.body if not ('box_center_preference' in ast.unparse(n))]
for n in ast.walk(life):
 if isinstance(n,ast.Call):n.keywords=[k for k in n.keywords if k.arg!='box_center_preference']
assert dump(life)==dump(ast.parse((parent/'minimum_motion_lifecycle.py').read_text()))
wrapper=ast.parse((stage/'recontact_plan.py').read_text());fn=next(n for n in wrapper.body if isinstance(n,ast.FunctionDef));assert fn.args.kwonlyargs[-1].arg=='box_center_preference';fn.args.kwonlyargs.pop();fn.args.kw_defaults.pop();assert all(isinstance(n,ast.If) and 'box_center_preference' in ast.unparse(n.test) for n in fn.body[:2]);fn.body=fn.body[2:];assert dump(wrapper)==dump(ast.parse((parent/'recontact_plan.py').read_text()))
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','minimum_motion_lifecycle.py','recontact_plan.py']:assert sha(p)==sha(stage/p.name),p.name
helper=(stage/'box_center_preference_plan.py').read_text().replace('box_center_preference_pose','minimum_motion_pose').replace('box_center_preference=True','offline_center_penalty=True');helper=helper.replace("    if scene.side!='right':raise ValueError('Box center preference requires right hand')\n",'');assert dump(ast.parse(helper))==dump(ast.parse((w/'offline_center_penalty_plan.py').read_text()))
expr=next(n.value for n in ast.walk(new) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='effective_drag_step_m' for t in n.targets));cases=[]
for flag in [False,True]:
 for slow in [False,True]:
  if flag and not slow:continue
  for rear in [False,True]:
   for side in ['left','right']:
    args=SimpleNamespace(rear_box_center_preference=flag,rear_slow_drag=slow,expert_frontal_top_drag_step_m=.003);actual=eval(compile(ast.Expression(expr),'<actual route selection>','eval'),dict(args=args,side=side,frontal_plan={'rear_cop_centering':{'enabled':rear}}));expected=.0015 if slow and rear and (not flag or side=='right') else .003;assert actual==expected;cases.append(dict(new_flag=flag,slow_flag=slow,rear=rear,side=side,step_m=actual))
assert len(cases)==12
files=[Path(__file__),w/'prepare_box_center_stage.py',w/'offline_center_penalty_plan.py',*stage.glob('*.py')];(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,default_off_full_collector_lifecycle_wrapper_ast_exact=True,unchanged_other_runtime_files=True,helper_math_matches_independently_screened_preference=True,task_route_selection_cases=cases,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('PASS defaultoff AST/12route selections')
