"""Prepare isolated default-off0.5mm nominal inward correction, no physics launch.
Right rear only, existing joint-XY eligibility; original limits/guards/quality.
"""
from pathlib import Path
import ast,json,hashlib,datetime
w=Path(__file__).resolve().parent;parent=w/'staged_box_entry_lift';stage=w/'staged_box_inward_correction';assert not stage.exists()
check=w/'box_entry_lift_groups_r1/INWARD_COMMAND_INDEPENDENT_CHECK.json';d=json.loads(check.read_text());assert d['complete'] and d['summary']['0.0005']['independent_passed']==d['summary']['0.0005']['n']==63;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in d['source_sha256'].items():assert sha(Path(name))==h,name
stage.mkdir()
for p in [*parent.glob('*.py'),parent/'causal_response_parameters.json',parent/'elbow_torso_hulls.json']:(stage/p.name).write_bytes(p.read_bytes())
s=(w/'joint_edge_inward_probe.py').read_text().replace('def refine_rear_command(', 'def _refine_rear_command(')
s+='''\n\ndef refine_rear_command(**kwargs):
    """Fixed requirement for explicitly selected right-rear diagnostic adapter."""
    if 'inward_step_m' in kwargs:raise ValueError('Diagnostic requirement is fixed')
    out=_refine_rear_command(**kwargs,inward_step_m=.0005)
    out['nominal_inward_requirement_m']=.0005
    out['physical_motion_prediction']=False
    for key,residual in [('parent_nominal_edge_inward_m','parent_edge_constraint_residual_m'),('nominal_edge_inward_m','edge_constraint_residual_m')]:
        if key in out:
            out[residual]=out[key]
            out[key]=[x+.0005 for x in out[key]]
    return out
'''
(stage/'joint_edge_inward_command.py').write_text(s)
s=(parent/'joint_edge_adapter.py').read_text().replace('from joint_edge_command import refine_rear_command','from joint_edge_inward_command import refine_rear_command');(stage/'joint_edge_inward_adapter.py').write_text(s)
p=stage/'collect_paired_sorting.py';s=p.read_text();s=s.replace("parser.add_argument('--rear-box-entry-lift'","parser.add_argument('--rear-box-inward-correction',action='store_true',help='Default-off0.5mm nominal inward correction, right rear existing edge refinement only.')\nparser.add_argument('--rear-box-entry-lift'",1);s=s.replace('args = parser.parse_args()',"args = parser.parse_args()\nif args.rear_box_inward_correction and not (args.rear_box_entry_lift and args.rear_joint_edge_parent_seed_retry and args.role=='diagnostic'):\n    parser.error('Box inward correction requires complete entry-lift diagnostic')",1)
a="            from joint_edge_adapter import refine_record";assert s.count(a)==1;s=s.replace(a,a+"\n            if args.rear_box_inward_correction and side=='right':\n                from joint_edge_inward_adapter import refine_record")
a="                        frontal_plan['rear_joint_edge_command']=dict(enabled=True,core_inset_m=.01,waist_command_limit_rad=.98,waist_step_rad=.015,arm_step_rad=.04,final_slew_rad=.055,original_guard_priority=True,first_loaded_preserved=True,requires_joint_xy_override=True,reference='current_offset_frozen_virtual_reference_not_physical_contact',fallback='preserve_parent_command',full_push_ik_trace=True)";assert s.count(a)==1;s=s.replace(a,a+"\n                        if args.rear_box_inward_correction and side=='right':\n                            frontal_plan['rear_box_inward_correction']=dict(enabled=True,side='right',nominal_inward_requirement_m=.0005,existing_joint_xy_eligibility=True,original_task_objective=True,original_bounds_and_guards=True,physical_motion_prediction=False,training_ready=False)")
a="    if args.rear_box_entry_lift:\n        episode.collect_meta['rear_box_entry_lift']=True";assert s.count(a)==1;s=s.replace(a,a+"\n    if args.rear_box_inward_correction:\n        episode.collect_meta['rear_box_inward_correction']=True")
a="    if args.rear_box_entry_lift:\n        paths.extend([STAGE/'box_recovery_entry_lift.py',STAGE/'box_entry_lift_recontact_guarded.py'])";assert s.count(a)==1;s=s.replace(a,a+"\n    if args.rear_box_inward_correction:\n        paths.extend([STAGE/'joint_edge_inward_command.py',STAGE/'joint_edge_inward_adapter.py'])");ast.parse(s);p.write_text(s)
class Off(ast.NodeTransformer):
 def visit_If(self,n):
  if any(isinstance(x,ast.Attribute) and x.attr=='rear_box_inward_correction' for x in ast.walk(n.test)):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='add_argument' and any(isinstance(x,ast.Constant) and x.value=='--rear-box-inward-correction' for x in n.value.args):return None
  return self.generic_visit(n)
assert ast.dump(Off().visit(ast.parse(s)))==ast.dump(ast.parse((parent/p.name).read_text()))
for q in parent.glob('*.py'):
 if q.name!=p.name:assert sha(q)==sha(stage/q.name)
files=[Path(__file__),check,w/'joint_edge_inward_probe.py',*[q for q in stage.iterdir() if q.suffix in ['.py','.json']]]
(stage/'INTEGRATION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,default_off_collector_ast_identical=True,all_other_existing_sources_identical=True,fixed_requirement_m=.0005,left_dispatch_unchanged=True,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False),indent=2));print('prepared_not_frozen_not_launched',stage)
