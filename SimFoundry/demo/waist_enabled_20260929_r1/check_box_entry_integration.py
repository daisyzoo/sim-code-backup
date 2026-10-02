"""Default-off whole collector AST and actual side-specific class selection."""
from pathlib import Path
import ast,copy,json,hashlib,sys
from types import SimpleNamespace
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'staged_box_center_preference';stage=w/'staged_box_entry_lift';sys.path[:0]=[str(stage),str(w),str(repo)];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Strip(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--rear-box-entry-lift':return None
  return self.generic_visit(n)
 def visit_If(self,n):
  if 'args.rear_box_entry_lift' in ast.unparse(n.test):return None
  return self.generic_visit(n)
new=ast.parse((stage/'collect_paired_sorting.py').read_text());restored=Strip().visit(copy.deepcopy(new));assert ast.dump(restored)==ast.dump(ast.parse((parent/'collect_paired_sorting.py').read_text()))
for p in [*parent.glob('*.py'),parent/'causal_response_parameters.json',parent/'elbow_torso_hulls.json']:
 if p.name!='collect_paired_sorting.py':assert sha(p)==sha(stage/p.name),p.name
for name in ['box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py']:assert sha(w/name)==sha(stage/name)
node=next(n for n in ast.walk(new) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.unloaded_recontact_pose' and any(isinstance(x,ast.ImportFrom) and x.module=='recontact_lifecycle' for x in n.body));cases=[]
for center,entry in [(False,False),(True,False),(True,True)]:
 for side in ['left','right']:
  args=SimpleNamespace(unloaded_recontact_pose=True,minimum_motion_recontact=True,recontact_interior_preference=True,rear_box_center_preference=center,rear_box_entry_lift=entry);ctx=dict(args=args,side=side);exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual collector lifecycle>','exec'),ctx);obj=ctx['recontact_lifecycle'];expected='box_entry_lift_recontact_guarded' if entry and side=='right' else 'minimum_motion_lifecycle';assert type(obj).__module__==expected
  if entry and side=='right':assert obj.entry_lift and obj.original.box_center_preference and obj.original.maximum_ticks==240
  else:assert obj.box_center_preference==(center and side=='right') and obj.maximum_ticks==240
  cases.append(dict(center_flag=center,entry_flag=entry,side=side,lifecycle=expected))
files=[Path(__file__),w/'prepare_box_entry_stage.py',*stage.glob('*.py'),stage/'causal_response_parameters.json',stage/'elbow_torso_hulls.json'];(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,default_off_ast_exact=True,unchanged_other_runtime=True,cases=cases,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('PASS entire default-off AST and6 actual lifecycle selections')
