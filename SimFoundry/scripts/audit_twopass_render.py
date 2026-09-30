#!/usr/bin/env python3
"""Independently audit paired two-pass diagnostics; never admit training data."""
import argparse, hashlib, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from simfoundry.data.paired_sorting import audit_rollout, audit_pair
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.diverse_layouts import load_diagnostic_layout
p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--allow-partial', action='store_true')
a = p.parse_args()
protocol = json.loads((a.root/'PROTOCOL.json').read_text())
rows, groups = [], []
for group in protocol['groups']:
    expected = [a.root/f"case_{c['layout_id']}/layout_{c['layout_id']}_{task}/quality.json" for c in group['layouts'] for task in ['push_box_to_bin', 'nudge_mailer_to_bin']]
    if a.allow_partial and not all(path.exists() for path in expected):
        continue
    group_rows, pairs = [], []
    for case in group['layouts']:
        lid = case['layout_id']
        layout = load_diagnostic_layout(case['path'], lid)
        assert hashlib.sha256(Path(case['path']).read_bytes()).hexdigest() == case['sha256']
        run = a.root/f'case_{lid}'
        provenance = json.loads((run/'provenance.json').read_text())
        assert provenance['source_sha256']['scripts/'+Path(protocol['collector']).name] == protocol['collector_sha256']
        args = provenance['args']
        assert args['policy_port'] == 0 and args['steps'] == 320 and args['role'] == 'diagnostic'
        assert args['expert_staging_z'] == .92 and args['expert_contact_offset'] == -.13 and args['expert_far_contact_offset'] == -.11
        episodes = []
        for task in ['push_box_to_bin', 'nudge_mailer_to_bin']:
            ep = run/f'layout_{lid}_{task}'
            with np.load(ep/'raw.npz') as raw, np.load(ep/'trace.npz') as tr, np.load(ep/'parcel_orientation.npz') as ori:
                q, action = raw['q'], raw['action']
                meta = json.loads(str(raw['collect_meta']))
                trace = {k: tr[k] for k in tr.files}
                assert q.shape == action.shape == (320,23) and len(raw['rgb']) == 320
                assert np.isfinite(q).all() and np.isfinite(action).all()
                assert np.abs(q[0,12:]).max() < 1e-4 and np.abs(action[0,12:]).max() < 1e-4
                assert np.all(action[:,12] == 0) and np.abs(np.diff(action, axis=0)).max() <= .055001
                assert meta['assist_frames'] == 0 and not meta['push_assist'] and meta['collection_role'] == 'diagnostic'
                assert meta['wait_force_n'] == meta['push_force_n'] == 0
                assert meta.get('first_far_exit_y',.30) == protocol.get('first_far_exit_y',.30)
                target = 'box' if task == 'push_box_to_bin' else 'mailer'
                event = json.loads((ep/'recontact_event.json').read_text())['event']
                if layout[target+'_xyz'][0] < .48:
                    assert event is None and np.array_equal(action[160:], np.broadcast_to(action[159], (160,23)))
                else:
                    assert event['step'] == 160 and event['height_offset_m'] == -.02
                    assert np.allclose(event['target_xyz'], trace[target][160], atol=1e-6, rtol=0)
                original = audit_rollout(task, q, action, trace)
                quality = json.loads((ep/'quality.json').read_text())
                assert not quality['training_ready']
                assert all(reason in quality['reasons'] for reason in original['reasons'])
                _, fitness = terminal_search_scores([quality], [0 if target == 'box' else 1], {k:v[:,None] for k,v in trace.items()}, {k:ori[k][:,None] for k in ori.files})
                rows.append(dict(group=group['group'], layout_id=lid, task=task, path=str(ep.resolve()), raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest(), original_audit=original, quality=quality, fitness=fitness[0], training_ready=False))
                group_rows.append(rows[-1])
                episodes.append(SimpleNamespace(collect_meta=meta, rgb=raw['rgb'][:1].copy(), q=q[:1].copy(), task_id=task, instruction=str(raw['instruction'])))
        pair = audit_pair(*episodes)
        pairs.append(dict(layout_id=lid, **pair))
    passed = len(group_rows) == 4 and all(r['fitness']['search_success'] for r in group_rows) and all(p['passed'] for p in pairs)
    groups.append(dict(group=group['group'], split=group['split'], numeric_and_pair_passed=passed, pairs=pairs, visual_review='pending', training_ready=False))
a.out.write_text(json.dumps(dict(rows=rows, groups=groups, complete=len(groups)==len(protocol['groups']), expected_groups=len(protocol['groups']), training_ready=False, goal_complete=False, scope='Independent original rollout/pair audits, full footprint support and uprightness, zero start/waist/no-assist/source provenance. Visual review remains required.'), indent=2))
print('Audited',len(rows),'episodes;',sum(g['numeric_and_pair_passed'] for g in groups),'/',len(groups),'complete groups')
