"""Original loaded replay mathematics exactly retained. Replays all eight frozen
rear-short parent files using their actual collector source identity. New-stage
public inspect additionally requires independent new-path native-file audit.
"""
from pathlib import Path
import sys,ast,json,hashlib,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_pose_loaded_execution import replay
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ast.parse((w/'audit_unloaded_wrist_loaded_execution.py').read_text());new=ast.parse((w/'audit_recontact_pose_loaded_execution.py').read_text())
for name in ['near','verify_refinement','verify_retry_metadata']:
 a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='inspect');b=copy.deepcopy(next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='replay'))
class RestoreBinding(ast.NodeTransformer):
 def visit_Call(self,node):
  if isinstance(node.func,ast.Name) and node.func.id=='sha' and len(node.args)==1 and isinstance(node.args[0],ast.IfExp) and ast.unparse(node.args[0].body)=='expected_collector':
   return ast.parse("sha(w/('staged_unloaded_wrist_prior' if name=='collect_paired_sorting.py' else 'staged_micro_clearance_return')/name)",mode='eval').body
  return self.generic_visit(node)
b=RestoreBinding().visit(b);assert ast.dump(ast.Module(body=a.body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=b.body,type_ignores=[]),include_attributes=False),'Loaded audit mathematics changed'
results=[]
for ep in sorted((w/'rear_short_recovery_groups_r1').glob('case_*/layout_*')):
 if not (ep/'frontal_bypass.json').exists():continue
 out=replay(ep,w/'staged_rear_short_recovery/collect_paired_sorting.py');assert out['passed'];results.append(dict(episode=ep.name,selected=out['selected'],loaded_frames=out['parent_full_push_replay_frames'],refinements=out['refinement_frames'],source_sha256=out.get('source_sha256',{})));print(results[-1]['episode'],out['parent_full_push_replay_frames'],'passed',flush=True)
assert len(results)==8
out=dict(passed=True,scope=__doc__,loaded_math_ast_exact=True,parent_replays=results,loaded_frames=sum(r['loaded_frames'] for r in results),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_recontact_pose_loaded_execution.py',w/'audit_unloaded_wrist_loaded_execution.py',w/'audit_rear_coupled_execution_live.py',w/'audit_rear_joint_xy_live.py']},physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/LOADED_EXECUTION_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),out['loaded_frames'],flush=True)
