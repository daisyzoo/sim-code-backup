"""Explicit candidate and unchanged observer provenance; no controller execution.
Pressure mathematics, state transitions and task success need separate audits.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_observation_binding(ep):
    ep=Path(ep).resolve();case=ep.parent;repo=W.parents[1]
    stage=W/'staged_peak_load_guard';parent=W/'staged_substep_observer'
    reference=W/'substep_reference03_groups_r1'
    prep=json.loads((stage/'PREPARATION.json').read_text())
    protocol=json.loads((reference/'PROTOCOL.json').read_text())
    result=json.loads((reference/'RESULT.json').read_text())
    assert result['status']=='diagnostic_closed_not_training_admission'
    assert len(result['rows'])==10 and all(r['all_audits_passed'] for r in result['rows'])
    assert prep['parent_result_sha256']==sha(reference/'RESULT.json')
    expected_helpers={'peak_load_bias_guard.py','peak_load_control_adapter.py',
                      'peak_load_observation.py','peak_load_update_trace.py'}
    assert set(prep['helpers'])==expected_helpers
    source=(stage/'collect_paired_sorting.py').read_text()
    for block in prep['candidate_blocks']:
        assert source.count(block)==1;source=source.replace(block,'')
    assert len(prep['candidate_blocks'])==9 and source==(parent/'collect_paired_sorting.py').read_text()
    assert sha(parent/'collect_paired_sorting.py')==protocol['frozen_files_sha256'][str(parent/'collect_paired_sorting.py')]
    assert sha(stage/'collect_paired_sorting.py')==prep['new_collector_sha256']
    prov=json.loads((case/'provenance.json').read_text());args=prov['args'];sources=prov['source_sha256']
    assert args['peak_load_bias_guard'] is True and args['trace_substep_contacts'] is True
    assert args['trace_solved_contact_forces'] is True and args['expert_frontal_top_recontact'] is True
    assert args['role']=='diagnostic' and args['expert_frontal_top_load_n']==5. and args['expert_top_tilt_recontact_rad']==.03
    for name in ['policy_port','idle','expert_contact_load_n','expert_frontal_load_n','wait_force_n','push_force_n']:
        assert not args[name],name
    for rel,digest in sources.items():
        path=repo/rel
        assert sha(case/'source_snapshot'/rel)==digest==sha(path),rel
        if path.parent==stage and path.name in expected_helpers:
            assert digest==prep['source_sha256'][str(path)]==sha(W/path.name)
        elif path==stage/'collect_paired_sorting.py':
            assert digest==prep['new_collector_sha256']
        else:
            normalized=str(path).replace('/staged_peak_load_guard/','/staged_substep_observer/')
            assert digest==protocol['frozen_files_sha256'][normalized],rel
    observer_helpers={'substep_contact_observer_prototype.py','substep_contact_runtime_bridge.py',
                      'substep_contact_recording.py','substep_contact_setup.py'}
    for name in expected_helpers|observer_helpers|{'collect_paired_sorting.py'}:
        assert str((stage/name).relative_to(repo)) in sources,name
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
    files=[case/'provenance.json',case/'SUBSTEP_RUNTIME_BINDING.json',ep/'SUBSTEP_CONTACT_RECORDING.json',
           ep/'substep_contacts.npz',ep/'peak_load_updates.json',ep/'raw.npz',
           stage/'PREPARATION.json',reference/'RESULT.json',Path(__file__)]
    return dict(passed=True,parent_collector_recovered_byte_exact=True,original_observer_unchanged=True,
                source_sha256={str(f):sha(f) for f in files},training_ready=False)
