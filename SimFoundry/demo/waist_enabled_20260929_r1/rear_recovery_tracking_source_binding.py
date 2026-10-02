"""Source/profile binding for isolated rear corridor recovery diagnostic stage.
No old data promotion, fixture labels or automatic admission. Every current
source and archived source must match its separately reviewed stage/preparation.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_recovery_tracking';sys.path.insert(0,str(ROOT))
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_preparation():
 from rear_corridor_latched_source_binding import verify_preparation as verify_parent
 parent_prep,ancestor_prep=verify_parent()
 prep=json.loads((S/'PREPARATION.json').read_text());parent=Path(prep['parent_stage'])
 assert parent==W/'staged_rear_corridor_latched'
 assert sha(parent/'PREPARATION.json')==prep['parent_preparation_sha256']
 for name,h in prep['stage_sha256'].items():assert sha(S/name)==h,name
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 restored=(S/'rear_recovery_tracking_adapter.py').read_text()
 for e in reversed(prep['adapter_edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'rear_corridor_latched_adapter.py').read_text()
 assert set(prep['stage_sha256'])==set(parent_prep['stage_sha256'])|set(prep['new_helpers'])
 for name,h in parent_prep['stage_sha256'].items():
  if name!='collect_paired_sorting.py':assert prep['stage_sha256'][name]==h
 checks=[S/'CHECK.json',W/'REAR_RECOVERY_TRACKING_SOLVER_V2_CHECK.json',W/'REAR_RECOVERY_TRACKING_RECORDS_CHECK.json',W/'REAR_RECOVERY_TRACKING_NATIVE_FALLBACK_FIXTURE_CHECK.json',W/'REAR_RECOVERY_TRACKING_NATIVE_PAIR_FIXTURE_CHECK.json']
 for check in checks:
  report=json.loads(check.read_text());assert report['passed'] and report['status']=='complete',str(check)
  for field in ['frozen_sha256','source_sha256']:
   for path,h in report.get(field,{}).items():assert sha(path)==h,path
 return prep,dict(helpers=ancestor_prep['helpers']+parent_prep['new_helpers'])

def verify_trial_provenance(case):
 case=Path(case);prep,previous=verify_preparation()
 prov=json.loads((case/'provenance.json').read_text());args=prov['args'];assert args['rear_corridor_recovery'] is True and args['rear_corridor_hysteresis'] is True and args['rear_recovery_tracking'] is True and args['role']=='diagnostic' and not args['waist_pilot_contract'];profile=json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text());settings=semantic_settings(args);assert settings.pop('rear_corridor_recovery') is True;assert settings.pop('rear_corridor_hysteresis') is True;assert settings.pop('rear_recovery_tracking') is True;assert settings==profile['resolved_settings']
 source=prov['source_sha256'];expected=dict(profile=sha(W/'staged_closed_peak_trial/TRIAL_PROFILE.json'),preparation=sha(S/'PREPARATION.json'));stage_rel=str(S.relative_to(ROOT))+'/'
 for name,h in source.items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts;assert sha(case/'source_snapshot'/rel)==h==sha(ROOT/rel)
  if name.startswith(stage_rel):assert prep['stage_sha256'][rel.name]==h
 collectors=[k for k in source if Path(k).name=='collect_paired_sorting.py'];assert collectors==[stage_rel+'collect_paired_sorting.py']
 for name in previous['helpers']+prep['new_helpers']:assert source[stage_rel+name]==prep['stage_sha256'][name]
 return prov,None,None

def verify_observation_binding(ep):
 ep=Path(ep).resolve();case=ep.parent;prov,_,_=verify_trial_provenance(case);args=prov['args'];sources=prov['source_sha256']
 with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);frames=len(z['q'])
 assert meta['collection_role']=='diagnostic' and meta['rear_corridor_recovery'] is True and meta['rear_corridor_hysteresis'] is True and meta['rear_corridor_exit_reserve_m']==.002 and meta['rear_recovery_tracking'] is True and meta['rear_recovery_tracking_max_bias_xy_m']==[.0015,.0005] and meta['assist_frames']==0 and not meta['push_assist'];assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']
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
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];expected=dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,negative_increment_only=True,original_filter_and_upward_relief=True,original_guard_priority=True,training_ready=False);assert plan['peak_load_bias_guard']==meta['frontal_bypass_plan']['peak_load_bias_guard']==expected;assert plan['top_recontact']['desired_vertical_load_n']==5.
 files=[case/'provenance.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'peak_load_updates.json',ep/'raw.npz',S/'PREPARATION.json',Path(__file__)]
 return dict(passed=True,diagnostic_only=True,source_sha256={str(p):sha(p) for p in files},training_ready=False)
