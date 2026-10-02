"""Fresh-v2 closed-expert source/observer binding, never a training approval.
Does not relabel old diagnostics or weaken original independent control math.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
RESULT_SHA='5f1ee4d4d1efa03db9493ae561e93b851335d65547fa0a8fa1a9c616c70d67b4'

def verify_trial_provenance(case):
    from simfoundry.data.waist_pilot_protocol import validate_waist_contract,semantic_settings
    case=Path(case);stage=W/'staged_closed_peak_trial';parent=W/'staged_peak_load_guard';reference=W/'peak_guard_groups_r1'
    prep=json.loads((stage/'PREPARATION.json').read_text());profile=json.loads((stage/'TRIAL_PROFILE.json').read_text())
    assert sha(reference/'RESULT.json')==RESULT_SHA==profile['reference_result_sha256']==prep['reference_result_sha256']
    assert sha(reference/'PROTOCOL.json')==profile['reference_protocol_sha256']
    result=json.loads((reference/'RESULT.json').read_text())
    assert result['status']=='diagnostic_closed_not_training_admission' and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and all(r['all_audits_passed'] and r['full_length'] for r in result['rows'])
    assert sha(stage/'collect_paired_sorting.py')==prep['collector_sha256']
    restored=(stage/'collect_paired_sorting.py').read_text()
    for edit in reversed(prep['admission_only_edits']):
        if edit['new']:
            assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'])
        else:
            marker='if args.expert_top_object_relative_lead_m and not ('
            assert restored.count(marker)==1;restored=restored.replace(marker,edit['old']+marker)
    assert restored==(parent/'collect_paired_sorting.py').read_text()
    for name,digest in prep['copied_source_sha256'].items():
        assert sha(parent/name)==digest
        if name!='collect_paired_sorting.py':assert sha(stage/name)==digest
    prov=json.loads((case/'provenance.json').read_text());args=prov['args'];sources=prov['source_sha256']
    assert args['role']=='pilot' and not args['extended_waist_diagnostic']
    contract,digest=validate_waist_contract(case/'waist_pilot_contract.json',settings=args)
    assert contract['version']==2 and contract['closed_expert_profile_sha256']==sha(stage/'TRIAL_PROFILE.json')
    assert contract['pilot_collector_sha256']==prep['collector_sha256']
    assert semantic_settings(args)==profile['resolved_settings']==contract['collector_settings']
    assert profile['prelaunch_settings']==contract['prelaunch_collector_settings']
    expected={**contract['controller_source_sha256'],str((stage/'collect_paired_sorting.py').relative_to(ROOT)):contract['pilot_collector_sha256']}
    assert all(sources.get(k)==v for k,v in expected.items()),'Missing bound runtime/profile source'
    for rel,h in sources.items():
        p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
        assert sha(case/'source_snapshot'/p)==h==sha(ROOT/p),rel
    assert len([p for p in sources if Path(p).name=='collect_paired_sorting.py'])==1
    assert args['peak_load_bias_guard'] is True and args['trace_substep_contacts'] is True
    assert args['trace_solved_contact_forces'] is True and args['expert_frontal_top_recontact'] is True
    assert args['expert_frontal_top_load_n']==5. and args['expert_top_tilt_recontact_rad']==.03
    for name in ['policy_port','idle','expert_contact_load_n','expert_frontal_load_n','wait_force_n','push_force_n']:
        assert not args[name],name
    return prov,contract,digest

def verify_observation_binding(ep):
    ep=Path(ep).resolve();case=ep.parent;stage=W/'staged_closed_peak_trial';repo=ROOT
    prov,contract,digest=verify_trial_provenance(case);args=prov['args'];sources=prov['source_sha256']
    with np.load(ep/'raw.npz') as z:
        meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);frames=len(z['q'])
    assert meta['collection_role']=='pilot' and meta['waist_pilot_contract_sha256']==digest
    entries=contract['wait_layouts'] if task=='wait_no_package' else contract['layouts']
    assert sum(d==meta['layout'] and d['layout_id']==meta['layout_id'] for d in entries)==1
    assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']
    observer_helpers={'substep_contact_observer_prototype.py','substep_contact_runtime_bridge.py','substep_contact_recording.py','substep_contact_setup.py'}
    runtime=json.loads((case/'SUBSTEP_RUNTIME_BINDING.json').read_text())
    record=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())
    assert runtime['observer_installed'] is True and runtime['original_graph_setting'] is True
    assert runtime['training_ready'] is False and record['training_ready'] is False
    assert record['metadata']==runtime['metadata'];m=runtime['metadata']
    assert m['fixture_cpu'] is False and m['expected_substeps']==24
    assert m['control_decimation']==8 and m['substeps_per_physics_tick']==3 and abs(m['solver_dt_s']-1/360)<1e-12
    assert m['expected_manager_steps']==(1 if m['all_graphable'] else 8) and len(m['geom_to_shape'])==1
    assert {Path(k).name for k in runtime['source_files']}==observer_helpers|{'newton_manager.py','mjwarp_manager.py','solver_mujoco.py','support.py'}
    for path,row in runtime['source_files'].items():
        assert sha(path)==row['sha256']==sha(case/row['snapshot'])
        if Path(path).name in observer_helpers:
            assert Path(path).parent==stage and row['sha256']==sources[str(Path(path).relative_to(repo))]
    with np.load(case/'runtime_collision_arrays.npz') as z:assert np.array_equal(z['shape_body'],m['shape_body'])
    assert record['recording_sha256']==sha(ep/'substep_contacts.npz')
    with np.load(ep/'raw.npz') as z:
        meta=json.loads(str(z['collect_meta']));task=str(z['task_id']);frames=len(z['q'])
    assert meta['peak_load_bias_guard'] is True and meta['assist_frames']==0 and not meta['push_assist']
    pressure=json.loads((ep/'peak_load_updates.json').read_text())
    assert pressure['training_ready'] is False and pressure['executed_action_count']==frames
    assert pressure['wait']==(task=='wait_no_package')
    if task=='wait_no_package':
        assert not pressure['rows'] and not pressure['final_control_states']
    else:
        plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
        expected=dict(enabled=True,previous_action_substeps=24,peak_threshold_multiplier=2.,
                      negative_increment_only=True,original_filter_and_upward_relief=True,
                      original_guard_priority=True,training_ready=False)
        assert plan['peak_load_bias_guard']==meta['frontal_bypass_plan']['peak_load_bias_guard']==expected
        assert plan['top_recontact']['desired_vertical_load_n']==5.
    files=[case/'provenance.json',case/'waist_pilot_contract.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'substep_contacts.npz',ep/'peak_load_updates.json',ep/'raw.npz',stage/'PREPARATION.json',stage/'TRIAL_PROFILE.json',W/'peak_guard_groups_r1/RESULT.json',Path(__file__)]
    return dict(passed=True,parent_collector_recovered_byte_exact=True,original_observer_unchanged=True,fresh_v2_contract_sha256=digest,source_sha256={str(p):sha(p) for p in files},training_ready=False)
