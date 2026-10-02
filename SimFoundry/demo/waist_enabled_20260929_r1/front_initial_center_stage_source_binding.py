"""Source/profile binding for isolated edge/clearance diagnostic stage.
No old data promotion, fixture labels or automatic admission. Every current
source and archived source must match its separately reviewed stage/preparation.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path.insert(0,str(ROOT))
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
 recovered=(S/'collect_paired_sorting.py').read_text()
 for edit in reversed(prep['edits']):assert recovered.count(edit['new'])==1;recovered=recovered.replace(edit['new'],edit['old'])
 assert recovered==(parent/'collect_paired_sorting.py').read_text()
 coordinated=(S/'waist_coordination_clearance.py').read_text();e=prep['coordination_edits']
 assert coordinated.count(e['added_branch'])==1
 assert coordinated.replace(e['added_branch'],'').replace(e['signature_new'],e['signature_old'])==(parent/'waist_coordination_clearance.py').read_text()
 helpers={Path(name).name for name in prep['helper_source_sha256']}
 for name in prep['stage_sha256']:
  if name not in {'collect_paired_sorting.py','waist_coordination_clearance.py'}|helpers:assert sha(S/name)==sha(parent/name)
 for original,h in prep['helper_source_sha256'].items():
  assert sha(original)==h
  name=Path(original).name;content=Path(original).read_text()
  if name=='front_initial_center_top_contact.py':content=content.replace('Path(__file__).resolve().parents[2]','Path(__file__).resolve().parents[3]')
  assert (S/name).read_text()==content

 prov=json.loads((case/'provenance.json').read_text());args=prov['args'];assert args['front_initial_center_landing'] is True;assert args['terminal_release_margin'] is True and args['expert_top_confirmed_release'] is True and args['edge_clearance_intersection'] is True and args['role']=='diagnostic' and not args['waist_pilot_contract'];profile=json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text());settings=semantic_settings(args);assert settings.pop('front_initial_center_landing') is True;assert settings.pop('terminal_release_margin') is True;assert settings.pop('edge_clearance_intersection') is True;assert settings==profile['resolved_settings']
 source=prov['source_sha256'];expected=dict(profile=sha(W/'staged_closed_peak_trial/TRIAL_PROFILE.json'),preparation=sha(S/'PREPARATION.json'));stage_rel=str(S.relative_to(ROOT))+'/'
 for name,h in source.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts;assert sha(case/'source_snapshot'/rel)==h==sha(ROOT/rel)
  if name.startswith(stage_rel):assert prep['stage_sha256'][rel.name]==h
 collectors=[k for k in source if Path(k).name=='collect_paired_sorting.py'];assert collectors==[stage_rel+'collect_paired_sorting.py']
 for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py',*sorted(helpers)]:assert source[stage_rel+name]==prep['stage_sha256'][name]
 return prov,None,None

def verify_observation_binding(ep):
 ep=Path(ep).resolve();case=ep.parent;prov,_,_=verify_trial_provenance(case);args=prov['args'];sources=prov['source_sha256']
 with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);frames=len(z['q'])
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
  declaration=plan['front_initial_center_landing'];assert declaration==meta['frontal_bypass_plan']['front_initial_center_landing']
  assert declaration['enabled'] is True and declaration['maximum_ticks']==240 and declaration['actual_ready_frames']==3
  assert declaration['center_xy_m']==.002 and declaration['precontact_height_m']==[.006,.007] and declaration['measured_height_m']==[.004,.010]
  assert declaration['alignment_abs_min']==.8 and declaration['numerical_tolerance']==2e-7 and declaration['causal_preflight_only'] is True
  assert declaration['no_plan_behavior']=='original_parent_before_any_override' and declaration['parameter_sha256']==sha(S/'causal_response_parameters.json')
  assert declaration['actual_core']==plan['front_cop_slip_following']['edge_speed']['actual_core']
  assert front['rows'] and all(r['kind']!='stop' for r in front['rows'])
 else:
  assert not front['rows']
  if task!='wait_no_package':assert 'front_initial_center_landing' not in plan
 files=[ep/'front_initial_center.json',S/'CHECK.json',case/'provenance.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'peak_load_updates.json',ep/'raw.npz',S/'PREPARATION.json',Path(__file__)]
 return dict(passed=True,diagnostic_only=True,source_sha256={str(p):sha(p) for p in files},training_ready=False)
