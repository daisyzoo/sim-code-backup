"""Independent AST regression of all unchanged control math and native file loop.
The added lift events are independently verified in separate event checks.
"""
from pathlib import Path
import ast,copy,json,sys,hashlib
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_box_entry_source_contract import verify_box_entry_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'BOX_ENTRY_AUDIT_VERSION_MAP.json').read_text());same=[];sources=[]
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s.replace('BOX_CENTER_','BOX_ENTRY_')
skip=['audit_box_center_plan','audit_box_center_events','box_center_step_contract','audit_box_center_source_contract','audit_box_center_pose_live']
for a,b in mapping.items():
 p=w/(a+'.py');q=w/(b+'.py')
 if not p.exists() or a in skip:continue
 assert ast.dump(ast.parse(rename(p.read_text())))==ast.dump(ast.parse(q.read_text())),b;same.append(b);sources.extend([p,q])
old=ast.parse(rename((w/'audit_box_center_pose_live.py').read_text()));new=ast.parse((w/'audit_box_entry_pose_live.py').read_text())
def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
class RemoveNativeAdditions(ast.NodeTransformer):
 def visit_If(self,n):
  text=ast.unparse(n.test)
  if text=="raw.get('entry_lift_phase') is not None" or text=="event and 'rejected_entry_lift_attempt' in event":return None
  return self.generic_visit(n)
for name in ['unique','loads','verify_files']:
 restored=RemoveNativeAdditions().visit(copy.deepcopy(fn(new,name)))
 assert ast.dump(restored)==ast.dump(fn(old,name)),name
step=(w/'box_entry_step_contract.py').read_text().replace(" assert args.get('rear_box_entry_lift') is True and meta.get('rear_box_entry_lift') is True\n",'');assert ast.dump(ast.parse(step))==ast.dump(ast.parse((w/'box_center_step_contract.py').read_text()))
legacy=[]
for ep in sorted((w/'rear_box_rate_groups_r1').glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 try:verify_box_entry_source(ep)
 except AssertionError as ex:assert str(ex)=='entry-lift option missing';legacy.append(ep.name)
 else:raise AssertionError('Old source admitted as entry lift')
assert len(legacy)==10
for p in [Path(__file__),w/'build_box_entry_audits.py',w/'BOX_ENTRY_AUDIT_VERSION_MAP.json',w/'audit_box_entry_pose_live.py',w/'audit_box_center_pose_live.py',w/'audit_box_entry_source_contract.py',w/'audit_box_entry_events.py',w/'audit_box_entry_lift_events.py',w/'audit_box_entry_plan.py',w/'box_entry_step_contract.py',w/'box_center_step_contract.py']:sources.append(p)
(w/'staged_box_entry_lift/AUDIT_VERSION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,unchanged_math_versions=same,native_original_loop_ast_exact_except_explicit_entry_blocks=True,original_step_math_exact=True,legacy_source_rejections=legacy,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));print('PASS',len(same),'unchanged versions; native loop and step math exact;10old sources rejected')
