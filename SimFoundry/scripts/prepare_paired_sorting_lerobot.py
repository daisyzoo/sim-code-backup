#!/usr/bin/env python3
"""Convert explicitly reviewed paired NPZ demonstrations; never overwrite data.

Run in the existing PI0.5 Python environment. Source roots are collector output
folders with a review.json binding every approved raw.npz to its SHA256. Idle
physics probes and any failed numeric/pair check are rejected before conversion.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS, VLA_SORTING_UNIFIED_PROMPT
from simfoundry.data.paired_sorting import audit_pair, audit_rollout
from simfoundry.data.schema import load_episode
from simfoundry.data.recovery_protocol import validate_contract, audit_force_trace
from simfoundry.data.diverse_layouts import validate_geometry_split, validate_diagnostic_layout, contact_offset_for_distance
from simfoundry.data.spatial_protocol import validate_spatial_contract
from simfoundry.data.short_first_pilot_audit import audit_pilot_episode
from simfoundry.data.waist_pilot_audit import audit_waist_pilot_episode
from simfoundry.data.waist_pilot_protocol import PROTOCOL as WAIST_PROTOCOL

INDICES = [*range(13, 23), 12]
JOINT_ORDER = [*[f'left_arm_joint_{i}' for i in range(5)],
               *[f'right_arm_joint_{i}' for i in range(5)], 'waist_yaw_joint']


def record_geometry_metadata(task_id, layout):
    """Preserve wait provenance without treating empty scenes as push swaps."""
    if 'geometry_group' not in layout:
        return {}
    if task_id == 'wait_no_package':
        return {'wait_geometry_group': layout['geometry_group'],
                'wait_assignment': layout.get('assignment')}
    return {'geometry_group': layout['geometry_group'],
            'assignment': layout.get('assignment')}


def checked_sources(roots):
    records = []
    waist_contracts = {}
    for root in roots:
        status = json.loads((root / 'STATUS.json').read_text())
        if status['status'] != 'numeric_pass_visual_review_pending':
            raise ValueError(f'{root}: collection did not pass all numeric gates')
        review = json.loads((root / 'review.json').read_text())
        if review.get('approved') is not True or not review.get('method'):
            raise ValueError(f'{root}: missing explicit visual review')
        paths = sorted(root.glob('layout_*/raw.npz'))
        provenance = json.loads((root/'provenance.json').read_text())
        config = provenance.get('release_scope', provenance['args'])
        if len(paths) != config['layouts']*2 + config['wait_episodes']:
            raise ValueError(f'{root}: incomplete collected episode coverage')
        if set(review.get('episodes', {})) != {str(p.relative_to(root)) for p in paths}:
            raise ValueError(f'{root}: review does not cover exactly the collected episodes')
        for path in paths:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if review.get('episodes', {}).get(str(path.relative_to(root))) != digest:
                raise ValueError(f'{path}: raw data not bound to the visual review')
            ep = load_episode(path)
            if ep.collect_meta.get('layout', {}).get('planned_split') == 'test':
                raise ValueError(f'{path}: preassigned test geometry cannot enter training conversion')
            if (ep.collect_meta.get('collection_role') != 'pilot'
                    or ep.collect_meta.get('idle_diagnostic')
                    or ep.collect_meta.get('assist_frames') != 0):
                raise ValueError(f'{path}: diagnostic or assisted data cannot train')
            twopass_audit = None
            waist_audit = None
            motion_protocol = ep.collect_meta.get('motion_protocol', 'waist_locked_v1')
            if motion_protocol not in ('waist_locked_v1', WAIST_PROTOCOL):
                raise ValueError(f'{path}: unknown motion protocol')
            if motion_protocol == WAIST_PROTOCOL:
                if ep.collect_meta.get('twopass_expert') is not None:
                    raise ValueError(f'{path}: conflicting waist/twopass protocols')
                waist_audit = audit_waist_pilot_episode(path, ep, provenance)
                contract = json.loads((root/'waist_pilot_contract.json').read_text())
                expected = {(entry['layout_id'], task)
                    for entry in contract['layouts']
                    for task in ('push_box_to_bin', 'nudge_mailer_to_bin')}
                expected.update((entry['layout_id'], 'wait_no_package')
                    for entry in contract['wait_layouts'])
                binding = waist_audit['contract_sha256']
                if binding in waist_contracts and waist_contracts[binding] != expected:
                    raise ValueError('Waist contract coverage changed')
                waist_contracts[binding] = expected
                if waist_audit['planned_split'] not in ('train', 'validation'):
                    raise ValueError('Waist pilot split is not train/validation')
            elif ep.collect_meta.get('twopass_expert') is not None:
                twopass_audit = audit_pilot_episode(path, ep, provenance)
                if twopass_audit['planned_split'] == 'test':
                    raise ValueError(f'{path}: preassigned test group cannot enter training conversion')
            elif 'geometry_group' in ep.collect_meta.get('layout', {}):
                settings = provenance['args']
                layout, contract_hash = validate_spatial_contract(root/'spatial_pilot_contract.json',
                    layout_id=ep.collect_meta['layout_id'], steps=len(ep.q),
                    staging_z=settings['expert_staging_z'], contact_offset=settings['expert_contact_offset'],
                    far_contact_offset=settings.get('expert_far_contact_offset', 0.))
                validate_diagnostic_layout(layout, ep.collect_meta['layout_id'])
                if layout != ep.collect_meta['layout'] or contract_hash != ep.collect_meta.get('spatial_pilot_contract_sha256'):
                    raise ValueError('Spatial pilot metadata/contract mismatch')
                target_key = 'box_xyz' if ep.task_id == 'push_box_to_bin' else 'mailer_xyz'
                expected_offset = contact_offset_for_distance(ep.collect_meta[target_key][0],
                    settings['expert_contact_offset'], settings.get('expert_far_contact_offset', 0.))
                if (ep.collect_meta['staging_palm_z'] != settings['expert_staging_z']
                        or ep.collect_meta['contact_side_offset'] != expected_offset
                        or ep.collect_meta.get('far_contact_offset', 0.) != settings.get('expert_far_contact_offset', 0.)
                        or ep.collect_meta.get('base_contact_offset', settings['expert_contact_offset']) != settings['expert_contact_offset']
                        or any(ep.collect_meta.get(k, 0) for k in ('max_contact_x', 'finger_heading_weight',
                            'bounded_servo_memory', 'object_feedback_lead', 'contact_confirmed_sweep', 'settled_contact', 'recover_contact_height', 'wait_force_n', 'push_force_n'))):
                    raise ValueError('Unregistered spatial expert setting')
            if ep.collect_meta.get('wait_force_n', 0) or ep.collect_meta.get('push_force_n', 0):
                settings = provenance['args']
                digest_contract = validate_contract(root/'recovery_pilot_contract.json',
                    layouts=range(settings['layout_start'], settings['layout_start']+settings['layouts']),
                    waits=range(settings['wait_layout_start'], settings['wait_layout_start']+settings['wait_episodes']),
                    push_force=settings.get('push_force_n',0), wait_force=settings.get('wait_force_n',0),
                    wait_side=settings.get('wait_force_side','left'),wait_start=settings.get('wait_force_start',20))
                if digest_contract != ep.collect_meta.get('recovery_contract_sha256'):
                    raise ValueError('Recovery contract hash mismatch')
                for key in ('push_force_n','wait_force_n','wait_force_side','wait_force_start'):
                    if ep.collect_meta.get(key) != settings.get(key):
                        raise ValueError('Recovery metadata differs from collection arguments')
                audit_force_trace(ep.collect_meta,ep.task_id,len(ep.q),
                                  json.loads((path.parent/'external_force.json').read_text()))
            if waist_audit is not None:
                report = waist_audit['original_audit']
            else:
                with np.load(path.parent / 'trace.npz') as tr:
                    report = audit_rollout(ep.task_id, ep.q, ep.action, dict(tr))
            saved = json.loads((path.parent / 'quality.json').read_text())
            if not report['passed'] or not saved['passed']:
                raise ValueError(f'{path}: numeric gate failed')
            if ep.instruction != PAIRED_SORTING_PROMPTS[ep.task_id]:
                raise ValueError(f'{path}: instruction was overwritten')
            records.append({'path': path, 'hash': digest, 'layout_id': ep.collect_meta['layout_id'],
                            'task_id': ep.task_id, 'instruction': ep.instruction,
                            'motion_protocol': motion_protocol})
            layout_split = ep.collect_meta.get('layout', {}).get('planned_split')
            if layout_split in ('train', 'validation'):
                records[-1]['planned_split'] = layout_split
            if waist_audit is not None:
                records[-1].update(planned_split=waist_audit['planned_split'],
                    waist_pilot_contract_sha256=waist_audit['contract_sha256'])
            if twopass_audit is not None:
                records[-1].update(planned_split=twopass_audit['planned_split'],
                    twopass_contract_sha256=twopass_audit['contract_sha256'])
            layout = ep.collect_meta.get('layout', {})
            records[-1].update(record_geometry_metadata(ep.task_id, layout))
    if not records:
        raise ValueError('no approved episodes')
    if len({r['motion_protocol'] for r in records}) != 1:
        raise ValueError('Locked and waist-enabled pilots cannot silently mix')
    for binding, expected in waist_contracts.items():
        actual = [(r['layout_id'], r['task_id']) for r in records
                  if r.get('waist_pilot_contract_sha256') == binding]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            raise ValueError('Incomplete or duplicate waist contract episode coverage')
    groups = defaultdict(list)
    for r in records:
        groups[r['layout_id']].append(r)
    for layout, group in groups.items():
        tids = [r['task_id'] for r in group]
        if tids == ['wait_no_package']:
            continue
        if sorted(tids) != ['nudge_mailer_to_bin', 'push_box_to_bin']:
            raise ValueError(f'layout {layout}: incomplete or duplicate task pair')
        report = audit_pair(*(load_episode(r['path']) for r in group))
        if not report['passed']:
            raise ValueError(f'layout {layout}: {report}')
    return sorted(records, key=lambda r: (r['layout_id'], r['task_id']))


def make_split(records, validation_layouts):
    geometry_groups = validate_geometry_split(records, validation_layouts)
    known = {r['layout_id'] for r in records}
    if not validation_layouts or not validation_layouts < known:
        raise ValueError('validation layout IDs must be a nonempty proper subset of collected layouts')
    split = {'grouping': 'layout_id', 'train': [], 'validation': [],
             'validation_layouts': sorted(validation_layouts), 'joint_order': JOINT_ORDER}
    if geometry_groups:
        split['grouping'] = 'geometry_group (legacy records: layout_id)'
        split['geometry_groups'] = geometry_groups
    for i, r in enumerate(records):
        name = 'validation' if r['layout_id'] in validation_layouts else 'train'
        if r.get('planned_split', name) != name:
            raise ValueError(f"layout {r['layout_id']}: requested split differs from preassigned pilot split")
        split[name].append(i)
    for name in ('train', 'validation'):
        if {records[i]['task_id'] for i in split[name]} != set(PAIRED_SORTING_PROMPTS):
            raise ValueError(f'{name} must contain both pushing tasks and wait')
    return split


def stats(arr):
    arr = np.concatenate(arr, axis=0).astype(np.float64)
    return {'min': arr.min(0).tolist(), 'max': arr.max(0).tolist(),
            'mean': arr.mean(0).tolist(), 'std': arr.std(0).tolist(), 'count': [len(arr)],
            **{f'q{n:02d}': np.quantile(arr, n/100., axis=0).tolist() for n in (1,10,50,90,99)}}


def build_query_phase_records(records):
    """Called only after source admission/split checks; never approves data."""
    from simfoundry.data.query_phases import episode_query_phases
    rows = []
    for i, record in enumerate(records):
        if (record.get('motion_protocol') != WAIST_PROTOCOL
                or not record.get('waist_pilot_contract_sha256')):
            raise ValueError('Phase export requires explicit admitted waist pilot records')
        raw_path = Path(record['path'])
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record['hash']:
            raise ValueError('Raw source changed before phase export')
        control_path = raw_path.parent/'expert_control.json'
        control_bytes = control_path.read_bytes()
        with np.load(raw_path) as raw:
            labels = episode_query_phases(record['task_id'], raw['q'], raw['action'],
                                          json.loads(control_bytes))
        rows.append(dict(episode_index=i, task_id=record['task_id'],
            raw_sha256=record['hash'], expert_control_sha256=hashlib.sha256(control_bytes).hexdigest(),
            **labels))
    source = ROOT/'simfoundry/data/query_phases.py'
    return dict(version=1, records=rows, labeler_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                training_ready=False, scope='Full-frame query phase metadata, no cropping or action changes. Train sampler must use train split only and separately frozen exposure quotas.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, nargs='+', required=True)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--repo-id', required=True)
    parser.add_argument('--validation-layouts', required=True)
    parser.add_argument('--variant', choices=('short', 'unified_ablation'), default='short')
    parser.add_argument('--export-query-phases', action='store_true', help='Optional admitted-waist query phase metadata; retains every original frame/action.')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.out_root.exists():
        raise FileExistsError(args.out_root)
    records = checked_sources(args.source)
    split = make_split(records, {int(x) for x in args.validation_layouts.split(',')})
    query_phases = build_query_phase_records(records) if args.export_query_phases else None
    print(json.dumps({'episodes': len(records), 'split': split, 'variant': args.variant, 'query_phase_export': query_phases is not None}, indent=2))
    if args.check_only:
        return
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    repo = ROOT.parent / 'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth'
    sys.path.insert(0, str(repo / 'unitree_lerobot/lerobot/src'))
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    features = {key: {'dtype': 'float32', 'shape': (11,), 'names': [JOINT_ORDER]}
                for key in ('observation.state', 'action')}
    features['observation.images.color_0'] = {'dtype': 'video', 'shape': (480,640,3),
                                             'names': ['height','width','channel']}
    ds = LeRobotDataset.create(repo_id=args.repo_id, root=args.out_root, fps=15,
         robot_type='Unitree_G1_23Dof_Arms5_Waist1', features=features,
         use_videos=True, image_writer_processes=0, image_writer_threads=4)
    train_q, train_a = [], []
    for i, r in enumerate(records):
        ep = load_episode(r['path'])
        prompt = ep.instruction if args.variant == 'short' else VLA_SORTING_UNIFIED_PROMPT
        q, a = ep.q[:, INDICES], ep.action[:, INDICES]
        for t in range(len(q)):
            ds.add_frame({'observation.state': q[t], 'action': a[t],
                          'observation.images.color_0': ep.rgb[t].transpose(1,2,0), 'task': prompt})
        ds.save_episode()
        if i in split['train']:
            train_q.append(q)
            train_a.append(a)
        r['exported_prompt'] = prompt
    ds.finalize()
    meta = args.out_root / 'meta'
    if query_phases is not None:
        (meta / 'episode_query_phases.json').write_text(json.dumps(query_phases, indent=2))
    (meta / 'train_validation_split.json').write_text(json.dumps(split, indent=2))
    (meta / 'train_only_stats.json').write_text(json.dumps({
        'observation.state': stats(train_q), 'action': stats(train_a),
        'episode_indices': split['train'], 'joint_order': JOINT_ORDER}, indent=2))
    (meta / 'paired_provenance.json').write_text(json.dumps({
        'variant': args.variant, 'records': records, 'training_ready': False,
        'next_gate': 'verify exported task_index text, frames and zero state/action before training'}, indent=2, default=str))
    print('Conversion complete; exported text/frame verification still required before training.')

if __name__ == '__main__':
    main()
