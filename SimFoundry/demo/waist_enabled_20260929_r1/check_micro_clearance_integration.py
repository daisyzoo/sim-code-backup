"""Verify actual collector's opt-in wiring and immutable parent/default-off path.
AST execution checks configuration rejection and front controller selection;
full recorded input replay runs separately. Neither is physical evidence.
"""
from pathlib import Path
import ast,copy,json,hashlib,sys,types
w=Path(__file__).resolve().parent;stage=w/'staged_micro_clearance_return';parent=w/'staged_front_diagonal_entry';repo=w.parents[1];sys.path[:0]=[str(stage),str(repo)]
a=ast.parse((parent/'collect_paired_sorting.py').read_text());b=ast.parse((stage/'collect_paired_sorting.py').read_text());flag='front_micro_repair_retention'
class Strip(ast.NodeTransformer):
 def visit_If(self,node):
  if flag in ast.unparse(node.test):assert not node.orelse;return None
  return self.generic_visit(node)
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and '--front-micro-repair-retention' in ast.unparse(node):return None
  return self.generic_visit(node)
assert ast.dump(a,include_attributes=False)==ast.dump(Strip().visit(copy.deepcopy(b)),include_attributes=False),'Unexpected parent path edit'
arg=next(n.value for n in b.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and '--front-micro-repair-retention' in ast.unparse(n));assert next(k.value.value for k in arg.keywords if k.arg=='action')=='store_true'
guard=next(n for n in b.body if isinstance(n,ast.If) and flag in ast.unparse(n.test))
class Parser:
 def error(self,msg):raise ValueError(msg)
valid=dict(front_micro_repair_retention=True,front_diagonal_entry=True,front_direction_recontact=True,self_clearance_task_ik=True,front_cop_edge_speed=True,expert_front_top_route=True,role='diagnostic',policy_port=None,idle=False)
checks=[]
for name,value in [('valid',None),('front_diagonal_entry',False),('front_direction_recontact',False),('self_clearance_task_ik',False),('front_cop_edge_speed',False),('expert_front_top_route',False),('role','train'),('policy_port',9000),('idle',True)]:
 d=dict(valid)
 if name!='valid':d[name]=value
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),'<actual argument gate>','exec'),dict(args=types.SimpleNamespace(**d),parser=Parser()))
 except ValueError:assert name!='valid';checks.append(dict(case=name,rejected=True))
 else:assert name=='valid';checks.append(dict(case=name,accepted=True))
# Execute real nested selection with front/COP prerequisites true. Default-off
# leaves original class, kwargs, and plan untouched; enabled injects actual class.
from front_cop_route_diagonal import FrontCopRouteState as Parent
from front_cop_route_micro import FrontCopRouteState as Candidate
switch=next(n for n in ast.walk(b) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_micro_repair_retention' and any(isinstance(x,ast.ImportFrom) for x in n.body))
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(front_micro_repair_retention=enabled),top_cls=Parent,top_extra={'recontact_on_route_change':True,'diagonal_entry':True},frontal_plan={})
 exec(compile(ast.Module(body=[switch],type_ignores=[]),'<actual class selection>','exec'),ns)
 assert ns['top_cls'] is (Candidate if enabled else Parent)
 assert ns['top_extra']==({'recontact_on_route_change':True,'diagonal_entry':True,'retain_micro_repair_contact':True} if enabled else {'recontact_on_route_change':True,'diagonal_entry':True})
 assert bool(ns['frontal_plan'])==enabled
 if enabled:
  gate=ns['frontal_plan']['front_micro_repair_retention'];assert gate['minimum_normal_load_n']==.3 and gate['original_guard_priority'] and gate['initial_turn_keeps_recontact'] and gate['whole_repair_excursion'] and gate['maximum_excursion_m']==.005 and gate['minimum_core_margin_m']==.01
# Candidate class switch must be nested below original front-only + COP blocks.
def ancestors(tree,target,path=()):
 if tree is target:return path
 for child in ast.iter_child_nodes(tree):
  found=ancestors(child,target,path+(tree,))
  if found is not None:return found
chain=ancestors(b,switch);tests=[ast.unparse(n.test) for n in chain if isinstance(n,ast.If)]
assert 'front_route_selected' in tests and 'args.front_cop_slip_following' in tests
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in parent.glob('*.py'):
 if p.name!='collect_paired_sorting.py':assert sha(p)==sha(stage/p.name)
report=dict(passed=True,scope=__doc__,default_off_ast_equal=True,argument_checks=checks,front_only_class_selection=True,physics_not_run=True,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'collect_paired_sorting.py',stage/'front_top_route_micro.py',stage/'front_cop_route_micro.py',stage/'micro_clearance_return.py']})
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(report,indent=2));print('passed default-off exact AST,9 argument branches,2 class selections,front-only nesting')
