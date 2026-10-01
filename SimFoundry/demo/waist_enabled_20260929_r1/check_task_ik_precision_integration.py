"""Prove default-off collector/coordination parity and one stopping-tolerance change.
Execute actual AST argument/selector branches; unchanged objective, bounds,
float32 output, geometry and task rows are checked structurally and by replay.
"""
from pathlib import Path
import ast,copy,hashlib,json,sys,types
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'staged_micro_clearance_return';stage=w/'staged_task_ik_precision';sys.path[:0]=[str(stage),str(repo)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Strip(ast.NodeTransformer):
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='precise_clearance_task_ik' or isinstance(x,ast.Name) and x.id=='precise_task_ik' for x in ast.walk(n.test)):
   assert not n.orelse;return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  c=n.value
  if isinstance(c,ast.Call) and c.args and isinstance(c.args[0],ast.Constant) and c.args[0].value=='--precise-clearance-task-ik':return None
  return self.generic_visit(n)
 def visit_arguments(self,n):
  for i in reversed(range(len(n.kwonlyargs))):
   if n.kwonlyargs[i].arg=='precise_task_ik':assert isinstance(n.kw_defaults[i],ast.Constant) and n.kw_defaults[i].value is False;n.kwonlyargs.pop(i);n.kw_defaults.pop(i)
  return self.generic_visit(n)
for name in ['collect_paired_sorting.py','waist_coordination_clearance.py']:
 before=ast.parse((parent/name).read_text());after=ast.parse((stage/name).read_text());assert ast.dump(before,include_attributes=False)==ast.dump(Strip().visit(copy.deepcopy(after)),include_attributes=False),name
assert (stage/'task_ik_precision.py').read_text()==(parent/'task_ik.py').read_text().replace('ftol=1e-11','ftol=1e-13')
assert sha(stage/'task_ik_precision.py')==sha(w/'staged_task_ik_precision_probe/task_ik.py')
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','waist_coordination_clearance.py']:assert sha(p)==sha(stage/p.name)
a=ast.parse((stage/'collect_paired_sorting.py').read_text());guard=next(n for n in a.body if isinstance(n,ast.If) and 'args.precise_clearance_task_ik and' in ast.unparse(n.test));base=dict(precise_clearance_task_ik=True,self_clearance_task_ik=True,role='diagnostic',waist_coordinated_expert=True,bounded_coupled_ik=True,policy_port=0,waist_probe=False,idle=False)
class Parser:
 def error(self,msg):raise ValueError(msg)
checks=[]
for key,value in [('valid',None),('precise_clearance_task_ik',False),('self_clearance_task_ik',False),('role','train'),('waist_coordinated_expert',False),('bounded_coupled_ik',False),('policy_port',8000),('waist_probe',True),('idle',True)]:
 cfg=base.copy()
 if key!='valid':cfg[key]=value
 rejected=False
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),'<actual guard>','exec'),dict(args=types.SimpleNamespace(**cfg),parser=Parser()))
 except ValueError:rejected=True
 assert rejected==(key not in ['valid','precise_clearance_task_ik']);checks.append(dict(case=key,rejected=rejected))
coord=ast.parse((stage/'waist_coordination_clearance.py').read_text());selector=next(n for n in ast.walk(coord) if isinstance(n,ast.If) and ast.unparse(n.test)=='precise_task_ik' and isinstance(n.body[0],ast.ImportFrom));source_switch=next(n for n in ast.walk(a) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.precise_clearance_task_ik' and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='append' for c in ast.walk(n)))
from task_ik import solve as ordinary
from task_ik_precision import solve as precise
for enabled in [False,True]:
 ns=dict(precise_task_ik=enabled,solve=ordinary);exec(compile(ast.Module(body=[selector],type_ignores=[]),'<actual solve selection>','exec'),ns);assert ns['solve'] is (precise if enabled else ordinary)
 ns=dict(args=types.SimpleNamespace(precise_clearance_task_ik=enabled),paths=[],STAGE=stage);exec(compile(ast.Module(body=[source_switch],type_ignores=[]),'<actual source selection>','exec'),ns);assert ns['paths']==([stage/'task_ik_precision.py'] if enabled else [])
out=dict(passed=True,scope=__doc__,default_off_collector_ast_equal=True,default_off_coordination_ast_equal=True,solver_only_ftol_changed=True,objective_bounds_normal_rows_unchanged=True,argument_checks=checks,solver_selection_and_archival_verified=True,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'collect_paired_sorting.py',stage/'waist_coordination_clearance.py',stage/'task_ik.py',stage/'task_ik_precision.py',w/'staged_task_ik_precision_probe/RESULT.json']},physical_validation=False,training_ready=False);(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(out,indent=2));print('passed exact default-off AST, single ftol difference,9 argument branches, actual solver/source branches')
