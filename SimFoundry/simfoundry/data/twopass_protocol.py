"""Separate fail-closed admission contract for fresh two-pass expert pilots.

This module does not approve diagnostics or change existing spatial admission.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from simfoundry.data.diverse_layouts import validate_diagnostic_layout

EXPERT = {
    'kind': 'cartesian_twopass_v1', 'steps': 320, 'switch_frame': 160,
    'far_initial_x_threshold': .48, 'near_second_phase': 'hold_last_action',
    'first': {'staging_z': .92, 'contact_x_bias': 0., 'box_contact_z': .845,
              'mailer_contact_z': .840, 'near_contact_offset': -.13,
              'far_contact_offset': -.11, 'exit_y': .30},
    'second': {'staging_z': 1., 'contact_x_bias': .04, 'box_contact_z': .825,
               'mailer_contact_z': .820, 'contact_offset': -.11, 'exit_y': .30,
               'anchor': 'measured_target_xyz_at_switch'},
    'joint_target_slew_rad': .055, 'assist_frames': 0, 'waist_action': 0.,
}
TASKS = {'push_box_to_bin', 'nudge_mailer_to_bin'}


def _read_bound(root, name, digest):
    path = root/name
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f'Changed two-pass evidence: {name}')
    return json.loads(payload)


def _validate_twopass_contract(path, *, layout_id, steps, expected_expert):
    path = Path(path)
    payload = path.read_bytes()
    contract = json.loads(payload)
    if contract.get('version') != 1 or contract.get('approved_for_pilot') is not True:
        raise ValueError('Two-pass pilot has not passed feasibility review')
    if contract.get('expert') != expected_expert or steps != expected_expert['steps']:
        raise ValueError('Unregistered two-pass expert settings')
    layouts = contract.get('layouts', [])
    ids = [d['layout_id'] for d in layouts]
    if not layouts or len(ids) != len(set(ids)) or ids.count(layout_id) != 1:
        raise ValueError('Missing, duplicate or unregistered two-pass layout')
    groups = {}
    for d in layouts:
        validate_diagnostic_layout(d, d['layout_id'])
        groups.setdefault(d['geometry_group'], []).append(d)
    for key, pair in groups.items():
        if not key or len(pair) != 2 or {d['assignment'] for d in pair} != {'normal','swapped'}:
            raise ValueError('Two-pass pilot requires complete category-swap groups')
        a, b = pair
        if (a['box_xyz'][:2] != b['mailer_xyz'][:2] or a['mailer_xyz'][:2] != b['box_xyz'][:2]
                or a['seed'] != b['seed'] or any(a.get(k,0.) != b.get(k,0.) for k in ['box_yaw','mailer_yaw'])):
            raise ValueError('Category assignments must exchange identical slots and preserve yaw/seed')
    declared = contract.get('groups', [])
    if len(declared) != len(groups) or {g['group'] for g in declared} != set(groups):
        raise ValueError('Missing or duplicate preassigned pilot groups')
    for group in declared:
        expected_ids = {d['layout_id'] for d in groups[group['group']]}
        if (group.get('split') not in {'train','validation','test'}
                or len(group.get('layout_ids', [])) != 2
                or set(group['layout_ids']) != expected_ids):
            raise ValueError('Invalid preassigned group membership/split')
    evidence = contract.get('feasibility', [])
    if not evidence:
        raise ValueError('Missing reviewed two-pass feasibility evidence')
    diagnostic_ids = set()
    for source in evidence:
        root = Path(source['root'])
        audit = _read_bound(root, 'FINAL_AUDIT.json', source['audit_sha256'])
        review = _read_bound(root, 'visual_review.json', source['visual_review_sha256'])
        protocol = _read_bound(root, 'PROTOCOL.json', source['protocol_sha256'])
        expected_exit = expected_expert['first'].get('far_exit_y', expected_expert['first']['exit_y'])
        if protocol.get('first_far_exit_y',.30) != expected_exit:
            raise ValueError('Feasibility evidence uses a different first-far endpoint')
        frozen_collector = root/'collector_source.py'
        if hashlib.sha256(frozen_collector.read_bytes()).hexdigest() != protocol['collector_sha256']:
            raise ValueError('Feasibility collector snapshot changed')
        if not audit.get('complete') or not review.get('complete') or review.get('reviewed') is not True:
            raise ValueError('Two-pass feasibility audit/review is incomplete')
        expected = set()
        for group in protocol['groups']:
            for case in group['layouts']:
                diagnostic_ids.add(case['layout_id'])
                expected.update((case['layout_id'],task) for task in TASKS)
        rows = audit['rows']
        if len(rows) != len(expected) or {(r['layout_id'],r['task']) for r in rows} != expected:
            raise ValueError('Incomplete two-pass feasibility task coverage')
        if (len(audit['groups']) != len(protocol['groups']) or
                {g['group'] for g in audit['groups']} != {g['group'] for g in protocol['groups']} or
                not all(g['numeric_and_pair_passed'] for g in audit['groups'])):
            raise ValueError('Failed or incomplete feasibility groups')
        hashes = set()
        for row in rows:
            raw = (root/f"case_{row['layout_id']}/layout_{row['layout_id']}_{row['task']}/raw.npz")
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()
            if digest != row['raw_sha256'] or not row['fitness']['search_success']:
                raise ValueError('Changed or failed two-pass feasibility trajectory')
            hashes.add(digest)
        if len(hashes) != len(rows) or hashes != set(review.get('raw_sha256', [])):
            raise ValueError('Visual review does not cover exact feasibility trajectories')
        if review.get('reviewed_episodes') != len(rows) or not review.get('source_reviews'):
            raise ValueError('Missing actual per-layout image review records')
        for recorded in review['source_reviews']:
            actual = Path(recorded['path']).read_bytes()
            if hashlib.sha256(actual).hexdigest() != recorded['sha256'] or json.loads(actual).get('reviewed') is not True:
                raise ValueError('Changed actual image review record')
    if diagnostic_ids.intersection(ids):
        raise ValueError('Fresh pilot must use new layout IDs')
    return next(d for d in layouts if d['layout_id']==layout_id), hashlib.sha256(payload).hexdigest()


def validate_twopass_contract(path, *, layout_id, steps):
    return _validate_twopass_contract(path, layout_id=layout_id, steps=steps, expected_expert=EXPERT)
