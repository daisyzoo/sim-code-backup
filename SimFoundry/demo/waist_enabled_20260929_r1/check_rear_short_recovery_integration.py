"""Actual collector AST checks for rear-only default-off short recovery wiring."""
from pathlib import Path
import ast,copy,json,hashlib,types
w=Path(__file__).resolve().parent;parent=w/'staged_micro_clearance_return';stage=w/'staged_rear_short_recovery';a=ast.parse((parent/'collect_paired_sorting.py').read_text());b=ast.parse((stage/'collect_paired_sorting.py').read_text())
def contains_flag(node):return any(isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='args' and n.attr=='rear_short_recovery' for n in ast.walk(node))
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,node):
  if contains_flag(node.test):assert not node.orelse;return None
  return self.generic_visit(node)
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and node.value.args and isinstance(node.value.args[0],ast.Constant) and node.value.args[0].value=='--rear-short-recovery':return None
  return self.generic_visit(node)
assert ast.dump(a,include_attributes=False)==ast.dump(RemoveNew().visit(copy.deepcopy(b)),include_attributes=False)
guard=next(n for n in b.body if isinstance(n,ast.If) and contains_flag(n.test));switch=next(n for n in ast.walk(b) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_short_recovery')
base=dict(rear_short_recovery=True,region_top_approach=True,rear_cop_centering=True,rear_joint_edge_analytic_retry=True,self_clearance_task_ik=True,expert_frontal_top_guarded_descent=True,expert_frontal_top_continuous_drag=True,expert_frontal_top_recovery_clearance_m=0.,role='diagnostic',policy_port=0,idle=False)
class Parser:
 def error(self,msg):raise ValueError(msg)
checks=[]
for key,value in [('valid',None),('rear_short_recovery',False)]+[(k,False) for k in ['region_top_approach','rear_cop_centering','rear_joint_edge_analytic_retry','self_clearance_task_ik','expert_frontal_top_guarded_descent','expert_frontal_top_continuous_drag']]+[('expert_frontal_top_recovery_clearance_m',.04),('role','train'),('policy_port',8000),('idle',True)]:
 cfg=base.copy()
 if key!='valid':cfg[key]=value
 rejected=False
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),'<actual CLI guard>','exec'),dict(args=types.SimpleNamespace(**cfg),parser=Parser()))
 except ValueError:rejected=True
 assert rejected==(key not in ['valid','rear_short_recovery']);checks.append(dict(case=key,rejected=rejected))
for enabled in [False,True]:
 ns=dict(args=types.SimpleNamespace(rear_short_recovery=enabled),top_extra={},frontal_plan={});exec(compile(ast.Module(body=[switch],type_ignores=[]),'<actual rear selection>','exec'),ns)
 assert ns['top_extra']==({'recontact_travel_z':.86} if enabled else {})
 if enabled:
  plan=ns['frontal_plan']['rear_short_recovery'];assert plan['initial_travel_z']==.91 and plan['release_min_z']==.91 and plan['original_guard_priority'] and plan['loaded_control_unchanged']
 else:assert ns['frontal_plan']=={}
def ancestors(tree,target,path=()):
 if tree is target:return path
 for child in ast.iter_child_nodes(tree):
  found=ancestors(child,target,path+(tree,))
  if found is not None:return found
conditions=[ast.unparse(n.test) for n in ancestors(b,switch) if isinstance(n,ast.If)]
assert 'args.region_top_approach and (not front_route_selected) and (not initial_top_selected)' in conditions,conditions
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sources={str(Path(__file__)):sha(Path(__file__)),str(parent/'collect_paired_sorting.py'):sha(parent/'collect_paired_sorting.py')}
for p in stage.iterdir():
 if p.suffix=='.py' or p.name in ['causal_response_parameters.json','elbow_torso_hulls.json']:
  if p.name!='collect_paired_sorting.py':assert sha(p)==sha(parent/p.name)
  sources[str(p)]=sha(p)
out=dict(passed=True,default_off_ast_equal=True,argument_checks=checks,rear_only_selection=True,unchanged_helper_sources=True,scope=__doc__,source_sha256=sources,physical_validation=False,training_ready=False);(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(out,indent=2));print('passed default-off AST,',len(checks),'argument branches, rear-only scope, helper hashes')
