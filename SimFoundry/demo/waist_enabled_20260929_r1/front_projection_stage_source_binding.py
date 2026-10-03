"""Source/profile binding for isolated edge/clearance diagnostic stage.
No old data promotion, fixture labels or automatic admission. Every current
source and archived source must match its separately reviewed stage/preparation.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_projection';sys.path.insert(0,str(ROOT))
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_trial_provenance(case):
 case=Path(case);prep=json.loads((S/'PREPARATION.json').read_text());parent=Path(prep['parent_stage'])
 assert prep['simulation_started'] is False and prep['training_ready'] is False
 assert sha(parent/'PREPARATION.json')==prep['parent_preparation_sha256']
 assert sha(W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json')=='cba631ea8c08a9a1f09a8bf1a05e2aa71fa3b1521b0207f5f4ccce8fe66d6ed3'
 check=json.loads((S/'CHECK.json').read_text());assert check['passed'] is True and check['stage_sha256']==prep['stage_sha256']
 parent_prep=json.loads((parent/'PREPARATION.json').read_text())
 for name,h in parent_prep['stage_sha256'].items():assert sha(parent/name)==h
 for name,h in prep['stage_sha256'].items():assert sha(S/name)==h
 for name,h in prep['parent_stage_sha256'].items():
  assert sha(parent/name)==h
  recovered=(S/name).read_text()
  for edit in reversed(prep['edits']):
   if edit['file']==name:
    assert recovered.count(edit['new'])==1
    recovered=recovered.replace(edit['new'],edit['old'])
  assert recovered==(parent/name).read_text()
 assert json.loads((parent/'CHECK.json').read_text())['stage_sha256']==parent_prep['stage_sha256']
 for original,h in prep['new_helper_source_sha256'].items():
  assert sha(original)==h and sha(S/Path(original).name)==h
 for check_name in ['FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json']:
  checked=json.loads((W/check_name).read_text());assert checked['passed'] is True
  for original,h in checked['source_sha256'].items():assert sha(original)==h
 helpers={Path(name).name for name in parent_prep['helper_source_sha256']}|{'front_loaded_material_projection.py'}

 prov=json.loads((case/'provenance.json').read_text());args=prov['args'];assert args['front_initial_center_landing'] is True;assert args['terminal_release_margin'] is True and args['expert_top_confirmed_release'] is True and args['edge_clearance_intersection'] is True and args['role']=='diagnostic' and not args['waist_pilot_contract'];profile=json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text());assert args['front_loaded_material_projection'] is True;assert args['front_loaded_reference_cap'] is True;settings=semantic_settings(args);assert settings.pop('front_loaded_material_projection') is True;assert settings.pop('front_loaded_reference_cap') is True;assert settings.pop('front_initial_center_landing') is True;assert settings.pop('terminal_release_margin') is True;assert settings.pop('edge_clearance_intersection') is True;assert settings==profile['resolved_settings']
 source=prov['source_sha256'];expected=dict(profile=sha(W/'staged_closed_peak_trial/TRIAL_PROFILE.json'),preparation=sha(S/'PREPARATION.json'));stage_rel=str(S.relative_to(ROOT))+'/'
 for name,h in source.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts;assert sha(case/'source_snapshot'/rel)==h==sha(ROOT/rel)
  if name.startswith(stage_rel):assert prep['stage_sha256'][rel.name]==h
 collectors=[k for k in source if Path(k).name=='collect_paired_sorting.py'];assert collectors==[stage_rel+'collect_paired_sorting.py']
 grandparent_prep=json.loads((Path(parent_prep['parent_stage'])/'PREPARATION.json').read_text())
 inherited_helpers={Path(name).name for name in grandparent_prep['helper_source_sha256']}
 for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py',*sorted(helpers|inherited_helpers)]:assert source[stage_rel+name]==prep['stage_sha256'][name]
 return prov,None,None

def verify_observation_binding(ep):
 ep=Path(ep).resolve();case=ep.parent;prov,_,_=verify_trial_provenance(case);args=prov['args'];sources=prov['source_sha256']
 with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);frames=len(z['q'])
 assert meta['front_loaded_material_projection'] is True and meta['front_loaded_projection_strategy']=='nearest_parent_in_slew_hand_material_intersection'
 assert meta['front_loaded_reference_cap'] is True
 assert meta['front_initial_center_landing'] is True;assert meta['front_initial_center_failure'] is None;assert meta['terminal_release_margin'] is True and meta['terminal_release_zone_m']==.205 and meta['terminal_release_progress_m']==.16;assert meta['collection_role']=='diagnostic' and meta['edge_clearance_intersection'] is True and meta['assist_frames']==0 and not meta['push_assist'];assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']
 runtime=json.loads((case/'SUBSTEP_RUNTIME_BINDING.json').read_text());record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text());assert runtime['observer_installed'] and runtime['original_graph_setting'];assert runtime['training_ready'] is False and record['training_ready'] is False;assert record['metadata']==runtime['metadata'];m=runtime['metadata']
 assert m['fixture_cpu'] is False and m['expected_substeps']==24 and m['control_decimation']==8 and m['substeps_per_physics_tick']==3 and abs(m['solver_dt_s']-1/360)<1e-12
 assert m['expected_manager_steps']==(1 if m['all_graphable'] else 8) and len(m['geom_to_shape'])==1
 helpers={'substep_contact_observer_prototype.py','substep_contact_runtime_bridge.py','substep_contact_recording.py','substep_contact_setup.py'};assert {Path(k).name for k in runtime['source_files']}==helpers|{'newton_manager.py','mjwarp_manager.py','solver_mujoco.py','support.py'}
 for path,row in runtime['source_files'].items():
  assert sha(path)==row['sha256']==sha(case/row['snapshot'])
  if Path(path).name in helpers:assert Path(path).parent==S and row['sha256']==sources[str(Path(path).relative_to(ROOT))]
 with np.load(case/'runtime_collision_arrays.npz') as z:assert np.array_equal(z['shape_body'],m['shape_body'])
 assert record['recording_sha256']==sha(ep/'substep_contacts.npz');assert meta['peak_load_bias_guard'] is True
 pressure=json.loads((ep/'peak_load_updates.json').read_text());assert pressure['training_ready'] is False and pressure['executed_action_count']==frames and pressure['wait']==(task=='wait_no_package')
 if task=='wait_no_package':assert not pressure['rows'] and not pressure['final_control_states']
 else:
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];expected=dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False);assert plan['peak_load_bias_guard']==meta['frontal_bypass_plan']['peak_load_bias_guard']==expected;assert plan['top_recontact']['desired_vertical_load_n']==5.;assert plan['confirmed_release_margin']==meta['frontal_bypass_plan']['confirmed_release_margin']==dict(enabled=True,zone_m=.205,minimum_progress_m=.16,original_confirmation_window=10,original_window_xy_m=.01,quality_thresholds_unchanged=True)
 front=json.loads((ep/'front_initial_center.json').read_text());assert front['training_ready'] is False
 selected=False if task=='wait_no_package' else bool(plan.get('front_route_selected'))
 assert front['selected'] is selected
 if selected:
  cap_expected=dict(enabled=True,cap_world_xy_axis_m=.010,max_command_step_axis_m=.003,max_hand_reference_lead_axis_m=.030,min_normal_load_n=.3,scope='Only measured initial-front capture, loaded top_push, after parent safety/COP',empty_intersection='stop_before_current_action_and_record_failed_episode',parent_pressure_and_z_unchanged=True,no_physical_success_claim=True,training_ready=False)
  cap_expected.update(projection_strategy='nearest_parent_in_slew_hand_material_intersection',stop_observation_archive=True)
  assert plan['front_loaded_reference_cap']==meta['frontal_bypass_plan']['front_loaded_reference_cap']==cap_expected
  declaration=plan['front_initial_center_landing'];assert declaration==meta['frontal_bypass_plan']['front_initial_center_landing']
  assert declaration['enabled'] is True and declaration['maximum_ticks']==240 and declaration['actual_ready_frames']==3
  assert declaration['center_xy_m']==.002 and declaration['precontact_height_m']==[.006,.007] and declaration['measured_height_m']==[.004,.010]
  assert declaration['alignment_abs_min']==.8 and declaration['numerical_tolerance']==2e-7 and declaration['causal_preflight_only'] is True
  assert declaration['no_plan_behavior']=='original_parent_before_any_override' and declaration['parameter_sha256']==sha(S/'causal_response_parameters.json')
  assert declaration['actual_core']==plan['front_cop_slip_following']['edge_speed']['actual_core']
  assert front['rows'] and all(r['kind']!='stop' for r in front['rows'])
 else:
  assert not front['rows']
  if task!='wait_no_package':assert 'front_initial_center_landing' not in plan and 'front_loaded_reference_cap' not in plan
 files=[ep/'front_initial_center.json',S/'CHECK.json',case/'provenance.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'peak_load_updates.json',ep/'raw.npz',S/'PREPARATION.json',Path(__file__)]
 return dict(passed=True,diagnostic_only=True,source_sha256={str(p):sha(p) for p in files},training_ready=False)
