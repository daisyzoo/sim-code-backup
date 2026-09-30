"""Independent admission checks for fresh short-first two-pass pilot episodes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.short_first_twopass_protocol import EXPERT, validate_twopass_contract


def audit_pilot_episode(path, episode, provenance):
    path = Path(path)
    root = path.parent.parent
    meta = episode.collect_meta
    contract_path = root/'twopass_pilot_contract.json'
    layout, digest = validate_twopass_contract(contract_path, layout_id=meta['layout_id'], steps=len(episode.q))
    contract = json.loads(contract_path.read_text())
    settings = provenance['args']
    if (meta.get('collection_role') != 'pilot' or meta.get('layout') != layout
            or meta.get('twopass_contract_sha256') != digest or meta.get('twopass_expert') != EXPERT):
        raise ValueError('Two-pass pilot metadata/contract mismatch')
    collector = Path(contract['pilot_collector'])
    if provenance['source_sha256'].get('scripts/'+collector.name) != contract['pilot_collector_sha256']:
        raise ValueError('Unregistered pilot collector source')
    required = dict(role='pilot', steps=320, policy_port=0, idle=False,
                    expert_staging_z=.92, expert_contact_offset=-.13,
                    expert_far_contact_offset=-.11, expert_crossed_contact_offset=0.,
                    expert_exit_y=.30, newton_contacts=True, wait_force_n=0., push_force_n=0.)
    for key, value in required.items():
        if settings.get(key) != value:
            raise ValueError(f'Unregistered two-pass setting: {key}')
    if (meta.get('first_far_exit_y') != .28 or meta.get('assist_frames') != 0
            or meta.get('push_assist') is not False or meta.get('collision_pipeline') != 'newton'):
        raise ValueError('Two-pass endpoint/physics/assistance mismatch')
    for key in ('max_contact_x','finger_heading_weight','bounded_servo_memory',
                'object_feedback_lead','contact_confirmed_sweep','settled_contact',
                'recover_contact_height','wait_force_n','push_force_n',
                'front_reposition_distance','front_reposition_measured_start',
                'front_reposition_hold_yz','crossed_contact_offset'):
        if meta.get(key,0):
            raise ValueError(f'Unregistered pilot expert feature: {key}')
    q, action = episode.q, episode.action
    if q.shape != (320,23) or action.shape != q.shape or len(episode.rgb) != 320:
        raise ValueError('Incomplete pilot trajectory')
    if not np.isfinite(q).all() or not np.isfinite(action).all():
        raise ValueError('Nonfinite state/action')
    if (np.abs(q[0,12:]).max() >= 1e-4 or np.abs(action[0,12:]).max() >= 1e-4
            or np.any(action[:,12] != 0) or np.abs(np.diff(action,axis=0)).max() > .055001):
        raise ValueError('Zero-start/waist/slew constraint failed')
    target = 'box' if episode.task_id == 'push_box_to_bin' else 'mailer'
    if episode.task_id not in ('push_box_to_bin','nudge_mailer_to_bin'):
        raise ValueError('Unexpected two-pass task')
    far = layout[target+'_xyz'][0] >= .48
    expected_meta = dict(staging_palm_z=1. if far else .92,
                         contact_x_bias=.04 if far else 0.,
                         contact_palm_z=(.825 if target=='box' else .820) if far else (.845 if target=='box' else .840),
                         contact_side_offset=-.11 if far else -.13, exit_y=.30,
                         far_contact_offset=-.11, base_contact_offset=-.13)
    for key,value in expected_meta.items():
        if not np.isclose(meta[key],value,rtol=0,atol=1e-7):
            raise ValueError(f'Unexpected final expert state: {key}')
    with np.load(path.parent/'trace.npz') as tr, np.load(path.parent/'parcel_orientation.npz') as ori:
        trace = {k:tr[k] for k in tr.files}
        event = json.loads((path.parent/'recontact_event.json').read_text())['event']
        if far:
            if (event is None or event['step'] != 160 or event['height_offset_m'] != -.02
                    or not np.allclose(event['target_xyz'],trace[target][160],rtol=0,atol=1e-6)):
                raise ValueError('Invalid measured-target recontact event')
        elif event is not None or not np.array_equal(action[160:],np.broadcast_to(action[159],(160,23))):
            raise ValueError('Near-object second phase must hold exactly')
        original = audit_rollout(episode.task_id,q,action,trace)
        saved = json.loads((path.parent/'quality.json').read_text())
        _, fitness = terminal_search_scores([saved],[0 if target=='box' else 1],
            {k:v[:,None] for k,v in trace.items()}, {k:ori[k][:,None] for k in ori.files})
    if not original['passed'] or not saved['passed'] or not fitness[0]['search_success']:
        raise ValueError(f'Pilot quality/support/upright gate failed: {path}')
    groups = [g for g in contract['groups'] if meta['layout_id'] in g['layout_ids']]
    if len(groups)!=1 or groups[0]['group'] != layout['geometry_group']:
        raise ValueError('Missing or ambiguous pilot split assignment')
    return dict(planned_split=groups[0]['split'], contract_sha256=digest,
                raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                original_audit=original, fitness=fitness[0])
