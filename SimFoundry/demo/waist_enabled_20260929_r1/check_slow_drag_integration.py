"""Verify isolated default behavior and unchanged independent audit mathematics."""
from pathlib import Path
import ast,json,hashlib,sys
w=Path(__file__).resolve().parent;stage=w/'staged_rear_slow_drag';parent=w/'staged_minimum_motion_recontact';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(s):return ast.dump(ast.parse(s),include_attributes=False)
s=(stage/'collect_paired_sorting.py').read_text()
s=s.replace("parser.add_argument('--rear-slow-drag', action='store_true', help='Diagnostic rear-region only 1.5mm drag; original front and initial routes preserved.')\n",'')
s=s.replace("if args.rear_slow_drag and not (args.minimum_motion_recontact and args.rear_cop_centering and args.expert_frontal_top_drag_step_m==.003 and args.expert_frontal_top_continuous_drag and args.role=='diagnostic'):\n    parser.error('Rear slow drag requires complete minimum-motion diagnostic, original global3mm continuous drag and rear COP')\n",'')
s=s.replace('rear_slow_drag=args.rear_slow_drag, ','').replace("                effective_drag_step_m = .0015 if args.rear_slow_drag and frontal_plan.get('rear_cop_centering',{}).get('enabled',False) else args.expert_frontal_top_drag_step_m\n",'').replace('drag_step_m=effective_drag_step_m','drag_step_m=args.expert_frontal_top_drag_step_m')
s=s.replace("    if args.rear_slow_drag:\n        episode.collect_meta['rear_slow_drag']=True\n",'')
assert tree(s)==tree((parent/'collect_paired_sorting.py').read_text())
s=(stage/'rear_cop_route.py').read_text().replace('    rear_slow_drag: bool = False\n','').replace("        if type(self.rear_slow_drag) is not bool or (self.rear_slow_drag and not self.rear_cop_enabled):\n            raise ValueError('Rear slow drag requires enabled rear COP')\n",'').replace('(.0015 if self.rear_slow_drag else .003)','.003').replace('Rear COP requires declared 3mm or rear-only 1.5mm continuous drag','Rear COP requires original 3mm continuous drag')
assert tree(s)==tree((parent/'rear_cop_route.py').read_text())
for p in parent.glob('*.py'):
 if p.name not in ['collect_paired_sorting.py','rear_cop_route.py']:assert sha(p)==sha(stage/p.name),p.name
mapping=json.loads((w/'SLOW_DRAG_AUDIT_VERSION_MAP.json').read_text())
def reverse(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[1])):s=s.replace(b,a)
 return s
special={'audit_minimum_motion_source_contract','audit_minimum_motion_plan','audit_minimum_motion_region_continuity','audit_minimum_motion_rear_xy','audit_minimum_motion_pose_loaded_execution'};unchanged=[]
for a,b in mapping.items():
 if not (w/(a+'.py')).exists():continue
 if a in special:continue
 assert tree(reverse((w/(b+'.py')).read_text()))==tree((w/(a+'.py')).read_text()),b;unchanged.append(b)
assert tree((w/'audit_slow_drag_plan.py').read_text())==tree((w/'audit_minimum_motion_plan_reentrant.py').read_text())
s=reverse((w/'audit_slow_drag_pose_loaded_execution.py').read_text()).replace('from audit_minimum_motion_rear_xy import reconstruct','from audit_rear_joint_xy_live import reconstruct')
assert tree(s)==tree((w/'audit_minimum_motion_pose_loaded_execution.py').read_text())
for a in ['region_continuity','rear_xy']:
 s=reverse((w/f'audit_slow_drag_{a}.py').read_text()).replace('base[1]+np.clip(direction*min(.34,direction*base[1]+drag_step)-base[1],-drag_step,drag_step)','base[1]+np.clip(direction*min(.34,direction*base[1]+.003)-base[1],-.003,.003)')
 s=s.replace('\nfrom slow_drag_step_contract import declared_step\ndrag_step=declared_step(plan)','').replace('    from slow_drag_step_contract import declared_step\n    drag_step=declared_step(plan)\n','').replace('unchanged X2mm and declared rear Y increment','unchanged X2mm/Y3mm')
 assert tree(s)==tree((w/f'audit_minimum_motion_{a}.py').read_text()),a
# Effective step is selected only from a causal route declaration; default false gives original3mm.
t=ast.parse((stage/'collect_paired_sorting.py').read_text());expr=next(n.value for n in ast.walk(t) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='effective_drag_step_m' for x in n.targets));from types import SimpleNamespace
selections=[]
for flag in [False,True]:
 for rear in [False,True]:
  val=eval(compile(ast.Expression(expr),'<declared-selection>','eval'),dict(args=SimpleNamespace(rear_slow_drag=flag,expert_frontal_top_drag_step_m=.003),frontal_plan={'rear_cop_centering':{'enabled':rear}}));assert val==(.0015 if flag and rear else .003);selections.append([flag,rear,val])
sources=[Path(__file__),w/'build_slow_drag_versions.py',w/'SLOW_DRAG_AUDIT_VERSION_MAP.json',w/'slow_drag_step_contract.py',*[p for p in stage.glob('*.py')],*[w/(b+'.py') for b in mapping.values() if (w/(b+'.py')).is_file()]]
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(dict(passed=True,default_runtime_ast_unchanged_except_explicit_two_file_changes=True,all_other_stage_sources_identical=True,unchanged_audit_math=unchanged,reentrant_plan_exact_checked_supplement=True,loaded_math_unchanged_except_parameterized_reference=True,step_selection=selections,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));print('PASS isolated runtime and independent mathematical invariants')
