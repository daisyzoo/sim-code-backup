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
from simfoundry.data.diverse_layouts import validate_geometry_split

INDICES = [*range(13, 23), 12]
JOINT_ORDER = [*[f'left_arm_joint_{i}' for i in range(5)],
               *[f'right_arm_joint_{i}' for i in range(5)], 'waist_yaw_joint']


def checked_sources(roots):
    records = []
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
            if (ep.collect_meta.get('collection_role') != 'pilot'
                    or ep.collect_meta.get('idle_diagnostic')
                    or ep.collect_meta.get('assist_frames') != 0):
                raise ValueError(f'{path}: diagnostic or assisted data cannot train')
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
            with np.load(path.parent / 'trace.npz') as tr:
                report = audit_rollout(ep.task_id, ep.q, ep.action, dict(tr))
            saved = json.loads((path.parent / 'quality.json').read_text())
            if not report['passed'] or not saved['passed']:
                raise ValueError(f'{path}: numeric gate failed')
            if ep.instruction != PAIRED_SORTING_PROMPTS[ep.task_id]:
                raise ValueError(f'{path}: instruction was overwritten')
            records.append({'path': path, 'hash': digest, 'layout_id': ep.collect_meta['layout_id'],
                            'task_id': ep.task_id, 'instruction': ep.instruction})
            layout = ep.collect_meta.get('layout', {})
            if 'geometry_group' in layout:
                records[-1].update(geometry_group=layout['geometry_group'], assignment=layout.get('assignment'))
    if not records:
        raise ValueError('no approved episodes')
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
        split['validation' if r['layout_id'] in validation_layouts else 'train'].append(i)
    for name in ('train', 'validation'):
        if {records[i]['task_id'] for i in split[name]} != set(PAIRED_SORTING_PROMPTS):
            raise ValueError(f'{name} must contain both pushing tasks and wait')
    return split


def stats(arr):
    arr = np.concatenate(arr, axis=0).astype(np.float64)
    return {'min': arr.min(0).tolist(), 'max': arr.max(0).tolist(),
            'mean': arr.mean(0).tolist(), 'std': arr.std(0).tolist(), 'count': [len(arr)],
            **{f'q{n:02d}': np.quantile(arr, n/100., axis=0).tolist() for n in (1,10,50,90,99)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, nargs='+', required=True)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--repo-id', required=True)
    parser.add_argument('--validation-layouts', required=True)
    parser.add_argument('--variant', choices=('short', 'unified_ablation'), default='short')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    if args.out_root.exists():
        raise FileExistsError(args.out_root)
    records = checked_sources(args.source)
    split = make_split(records, {int(x) for x in args.validation_layouts.split(',')})
    print(json.dumps({'episodes': len(records), 'split': split, 'variant': args.variant}, indent=2))
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
