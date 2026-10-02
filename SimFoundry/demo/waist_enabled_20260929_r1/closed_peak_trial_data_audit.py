"""Fresh waist pilot episode audit, prepared but not yet wired to conversion."""
from pathlib import Path
import json
import numpy as np
from simfoundry.data.waist_pilot_protocol import validate_waist_contract, file_sha256, PROTOCOL
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS


def audit_waist_pilot_episode(path, episode, provenance):
    meta = episode.collect_meta
    # Do this before even opening a contract. Successful diagnostic trajectories
    # remain diagnostics; a new registered pilot must collect its own samples.
    if (meta.get('collection_role') != 'pilot'
            or meta.get('motion_protocol') != PROTOCOL
            or meta.get('assist_frames') != 0 or meta.get('push_assist') is not False
            or meta.get('idle_diagnostic') is not False
            or meta.get('wait_force_n',0) or meta.get('push_force_n',0)
            or meta.get('collision_pipeline') != 'newton'):
        raise ValueError('Diagnostic, assisted, idle-probe or wrong-protocol episode cannot train')
    path = Path(path); settings = provenance['args']
    if settings.get('role') != 'pilot' or settings.get('policy_port'):
        raise ValueError('Provenance is not fresh expert pilot collection')
    contract, digest = validate_waist_contract(path.parent.parent/'waist_pilot_contract.json',
        settings=settings, layout_id=meta['layout_id'], require_live_sources=False)
    if meta.get('waist_pilot_contract_sha256') != digest:
        raise ValueError('Episode has no exact fresh waist contract binding')
    # Explicit new source location; never rewrite provenance to a legacy alias.
    collector_key = 'demo/waist_enabled_20260929_r1/staged_closed_peak_trial/collect_paired_sorting.py'
    profile_key = 'demo/waist_enabled_20260929_r1/staged_closed_peak_trial/TRIAL_PROFILE.json'
    if (contract.get('version') != 2 or not contract.get('closed_expert_profile_sha256')
            or provenance['source_sha256'].get(collector_key) != contract['pilot_collector_sha256']
            or provenance['source_sha256'].get(profile_key) != contract['closed_expert_profile_sha256']):
        raise ValueError('Collector/profile source differs from explicit closed-expert trial')
    profile_path = path.parent.parent/'source_snapshot'/profile_key
    if file_sha256(profile_path) != contract['closed_expert_profile_sha256']:
        raise ValueError('Archived closed-expert trial profile differs')
    profile = json.loads(profile_path.read_text())
    if (profile['resolved_settings'] != contract['collector_settings']
            or profile['prelaunch_settings'] != contract['prelaunch_collector_settings']
            or profile['reference_result_sha256'] != '5f1ee4d4d1efa03db9493ae561e93b851335d65547fa0a8fa1a9c616c70d67b4'):
        raise ValueError('Changed closed-expert trial control profile')
    for relative, sha in contract['controller_source_sha256'].items():
        if provenance['source_sha256'].get(relative) != sha:
            raise ValueError('Pilot controller dependency changed')
    # Validate every recorded pilot dependency, including the collector and
    # auditor snapshot. Metadata alone is not a source archive.
    for relative, sha in provenance['source_sha256'].items():
        name = Path(relative)
        if name.is_absolute() or '..' in name.parts:
            raise ValueError('Invalid recorded source snapshot path')
        snapshot = path.parent.parent/'source_snapshot'/name
        if file_sha256(snapshot) != sha:
            raise ValueError('Pilot recorded source snapshot differs')
    for key in ('motion_protocol','waist_limit_rad','waist_wait_tolerance_rad','environment_seed'):
        if meta.get(key) != settings[key]:raise ValueError('Episode/provenance motion settings differ')
    is_wait = episode.task_id == 'wait_no_package'
    entries = contract['wait_layouts'] if is_wait else contract['layouts']
    registered = next((d for d in entries if d['layout_id']==meta['layout_id']), None)
    if registered is None or meta.get('layout') != registered:
        raise ValueError('Episode task/layout differs from fresh contract')
    if episode.instruction != PAIRED_SORTING_PROMPTS[episode.task_id]:
        raise ValueError('Task instruction mismatch')
    frames = settings['wait_steps'] if is_wait else settings['steps']
    if (episode.q.shape != (frames,23) or episode.action.shape != (frames,23)
            or len(episode.rgb) != frames):
        raise ValueError('Incomplete pilot state/action/RGB alignment')
    with np.load(path.parent/'trace.npz') as trace:
        report = audit_rollout(episode.task_id, episode.q, episode.action, dict(trace),
            motion_protocol=PROTOCOL, waist_limit_rad=settings['waist_limit_rad'],
            waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'])
        pose = None
        if not is_wait:
            with np.load(path.parent/'parcel_orientation.npz') as orientation:
                _, poses = terminal_search_scores([report], [0 if episode.task_id=='push_box_to_bin' else 1],
                    {k:trace[k][:,None] for k in trace.files},
                    {k:orientation[k][:,None] for k in orientation.files})
                pose = poses[0]
    saved = json.loads((path.parent/'quality.json').read_text())
    if (not report['passed'] or not saved['passed'] or saved.get('motion_protocol') != PROTOCOL
            or (pose is not None and not pose['search_success'])):
        raise ValueError('Pilot failed original task/waist/pose gates')
    return dict(planned_split=registered['planned_split'], contract_sha256=digest,
                original_audit=report, pose=pose, motion_protocol=PROTOCOL)
