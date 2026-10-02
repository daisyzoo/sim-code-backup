"""Isolation and task-selection proof; no new physical success claim."""
from pathlib import Path
import ast,json,hashlib
from types import SimpleNamespace
w=Path(__file__).resolve().parent;stage=w/'staged_rear_box_rate';parent=w/'staged_rear_slow_drag';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();tree=lambda s:ast.dump(ast.parse(s),include_attributes=False)
s=(stage/'collect_paired_sorting.py').read_text().replace('rear_box_slow_drag','rear_slow_drag').replace('--rear-box-slow-drag','--rear-slow-drag').replace('Diagnostic rear-box-only1mm drag; rear bag and front/initial routes retain3mm.','Diagnostic rear-region only 1.5mm drag; original front and initial routes preserved.')
s=s.replace("rear_slow_drag=bool(args.rear_slow_drag and side=='right'), rear_cop_enabled=True",'rear_slow_drag=args.rear_slow_drag, rear_cop_enabled=True').replace(".001 if args.rear_slow_drag and side=='right' and frontal_plan.get",'.0015 if args.rear_slow_drag and frontal_plan.get')
assert tree(s)==tree((parent/'collect_paired_sorting.py').read_text())
s=(stage/'rear_cop_route.py').read_text().replace('rear_box_slow_drag','rear_slow_drag').replace('.001 if self.rear_slow_drag else .003','.0015 if self.rear_slow_drag else .003').replace('rear-box-only1mm','rear-only 1.5mm');assert tree(s)==tree((parent/'rear_cop_route.py').read_text())
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','rear_cop_route.py']:assert sha(p)==sha(stage/p.name),p.name
mapping=json.loads((w/'BOX_RATE_AUDIT_VERSION_MAP.json').read_text())
def reverse(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[1])):s=s.replace(b,a)
 return s.replace('rear_box_slow_drag','rear_slow_drag')
checked=[]
for a,b in mapping.items():
 if a=='slow_drag_step_contract' or not (w/(a+'.py')).exists():continue
 assert tree(reverse((w/(b+'.py')).read_text()))==tree((w/(a+'.py')).read_text()),b;checked.append(b)
from box_rate_step_contract import verify_declared_step
expr=next(n.value for n in ast.walk(ast.parse((stage/'collect_paired_sorting.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='effective_drag_step_m' for v in n.targets));selections=[]
for flag in [False,True]:
 for rear in [False,True]:
  for side in ['left','right']:
   expected=.001 if flag and rear and side=='right' else .003;args=SimpleNamespace(rear_box_slow_drag=flag,expert_frontal_top_drag_step_m=.003);val=eval(compile(ast.Expression(expr),'<selection>','eval'),dict(args=args,side=side,frontal_plan={'rear_cop_centering':{'enabled':rear}}));assert val==expected
   selections.append(dict(enabled=flag,rear=rear,side=side,effective_step_m=val))
   if flag:
    plan={'rear_cop_centering':{'enabled':rear},'direction':-1 if side=='right' else 1,'top_recontact':{'drag_step_m':val,'continuous_drag':True}}
    assert verify_declared_step(vars(args),plan,{'rear_box_slow_drag':True})==expected
sources=[Path(__file__),w/'build_box_rate_versions.py',w/'BOX_RATE_AUDIT_VERSION_MAP.json',w/'box_rate_step_contract.py',*[p for p in stage.glob('*.py')],*[w/(b+'.py') for b in mapping.values() if (w/(b+'.py')).is_file()]]
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,only_two_runtime_files_changed=True,all_other_stage_files_identical=True,independent_audit_math_unchanged=checked,task_route_selection_cases=selections,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));print('PASS2runtime/8selection cases/audit math unchanged')
