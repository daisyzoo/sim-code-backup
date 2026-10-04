"""Additional precision source/argument/metadata binding; never runs its solver.
The enclosing versioned native and KKT audits retain original mathematics.
This source binding alone does not verify executed actions or task success.
"""
from pathlib import Path
import json,hashlib
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_front_recontact_v1_stage_source(ep):
 from front_normal_stage_source_binding_v3 import verify_observation_binding
 verify_observation_binding(ep)
 ep=Path(ep);prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];source=prov['source_sha256'];snap=ep.parent/'source_snapshot';stage=W/'staged_front_normal_nondegradation_v3'
 assert args.get('rear_box_inward_correction') is True,'inward option missing'
 assert args.get('rear_box_entry_lift') is True,'entry-lift option missing'
 assert args.get('rear_box_center_preference') is True,'box center option missing'
 assert args.get('rear_slow_drag') is True,'rear slow drag flag missing/disabled'
 assert args.get('expert_frontal_top_drag_step_m')==.003
 assert args.get('minimum_motion_recontact') is True,'minimum-motion flag missing/disabled'
 assert args.get('rear_joint_edge_parent_seed_retry') is True,'parent-seed flag missing/disabled'
 assert args.get('rear_joint_edge_analytic_retry') is True,'parent-seed requires original analytic retry'
 assert args.get('precise_clearance_task_ik') is True,'precision flag missing/disabled'
 assert args['self_clearance_task_ik'] is True and args['unloaded_recontact_pose'] is True and args['recontact_interior_preference'] is True
 names=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py','recontact_plan.py','recontact_lifecycle.py','minimum_motion_recontact.py','minimum_motion_lifecycle.py','rear_cop_route.py','box_center_preference_plan.py','box_recovery_entry_lift.py','box_entry_lift_recontact_guarded.py','joint_edge_inward_command.py','joint_edge_inward_adapter.py'];bound={}
 for name in names:
  keys=[n for n in source if n.endswith('/'+name)];assert len(keys)==1,('missing/duplicate precision source',name);key=keys[0]
  assert sha(snap/key)==source[key]==sha(stage/name),('precision source mismatch',name);bound[name]=source[key]
 parent=(W/'staged_recontact_interior/task_ik.py').read_text();ordinary=(stage/'task_ik.py').read_text();assert ordinary==parent and ordinary.count('ftol=1e-11')==1
 assert (stage/'task_ik_precision.py').read_text()==ordinary.replace('ftol=1e-11','ftol=1e-13'),'precision changed more than stopping tolerance'
 with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']))
 assert meta.get('task_ik_optimizer_ftol')==1e-13,'raw precision setting missing/incorrect'
 assert meta.get('self_clearance_task_ik') is True and meta.get('unloaded_recontact_pose') is True and meta.get('recontact_interior_preference') is True
 assert meta.get('rear_box_inward_correction') is True,'raw inward option missing'
 assert meta.get('rear_box_entry_lift') is True,'raw entry-lift option missing'
 assert meta.get('rear_box_center_preference') is True,'raw box center option missing'
 assert meta.get('rear_slow_drag') is True,'raw rear slow drag flag missing'
 assert meta.get('minimum_motion_recontact') is True,'raw minimum-motion flag missing/disabled'
 assert meta.get('rear_joint_edge_parent_seed_retry') is True,'raw parent-seed setting missing/disabled'
 if (ep/'frontal_bypass.json').exists():
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
  if plan.get('rear_joint_edge_command',{}).get('enabled'):
   expected=dict(enabled=True,prior_solver_status=8,finite_endpoint_required=True,maximum_extra_retries=1,initializer='bounded_parent_delta',original_attempts_preserved=True,objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command')
   assert plan.get('rear_joint_edge_parent_seed_retry')==expected
   assert all(type(plan['rear_joint_edge_parent_seed_retry'][k]) is type(v) for k,v in expected.items())
  else:assert 'rear_joint_edge_parent_seed_retry' not in plan
 if (ep/'frontal_bypass.json').exists():
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
  if plan.get('rear_joint_xy_progress',{}).get('enabled'):
   expected=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],lift_heights_m=[.015,.030,.060],original_fallback=True,whole_sampled_path_check=True,maximum_ticks=240,training_ready=False)
   actual=plan['unloaded_recontact_pose'].get('minimum_motion_pose');assert actual==expected
   assert all(type(actual[k]) is type(v) for k,v in expected.items())
  else:assert 'minimum_motion_pose' not in plan.get('unloaded_recontact_pose',{})
 if (ep/'frontal_bypass.json').exists():
  from box_inward_step_contract import verify_declared_step
  verify_declared_step(args,plan,meta)
  expected_center=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)
  center=plan.get('unloaded_recontact_pose',{}).get('box_center_preference')
  enabled=plan.get('rear_joint_xy_progress',{}).get('enabled',False) and plan['direction']==-1
  if enabled:
   assert center==expected_center and all(type(center[k]) is type(v) for k,v in expected_center.items())
  else:assert center is None
  expected_entry=dict(enabled=True,side='right',original_entry_height_m=.84,nominal_lift_height_m=.845,measured_ready_frames=3,maximum_lift_ticks=40,combined_maximum_ticks=240,measured_unloaded_required=True,phase_boundary_guards=True,training_ready=False)
  entry=plan.get('unloaded_recontact_pose',{}).get('entry_lift')
  if enabled:
   assert entry==expected_entry and all(type(entry[k]) is type(v) for k,v in expected_entry.items())
  else:assert entry is None
  from audit_closed_peak_trial_refinement import verify_plan
  verify_plan(args,plan,meta)
 return dict(passed=True,ftol=1e-13,source_sha256=bound,scope=__doc__,training_ready=False)
