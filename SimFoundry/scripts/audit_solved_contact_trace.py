#!/usr/bin/env python3
"""Audit final-tick force observations; do not infer integrated impulses."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
results = []
for raw in sorted(a.root.glob('case_*/layout_*/raw.npz')):
    f = raw.parent / 'solved_contact_forces.json'
    if not f.exists():
        continue
    rows = json.loads(f.read_text())['rows']
    control = json.loads((raw.parent / 'expert_control.json').read_text())
    with np.load(raw) as z:
        meta = json.loads(str(z['collect_meta']))
        assert len(rows) == len(z['q']) == len(control) == 160
    target = 'box' if 'push_box' in raw.parent.name else 'mailer'
    target_label = '/parcel_box/' if target == 'box' else '/mailer/'
    side = 'right' if target == 'box' else 'left'
    groups = collections.defaultdict(list)
    alignment_error = 0.
    with np.load(raw.parent / 'trace.npz') as trace:
        for t, row in enumerate(rows):
            assert row['after_action_step'] == t
            assert row['solver_force_buffer_unchanged']
            if t + 1 < len(rows):
                for key in ('box', 'mailer', 'palm_left', 'palm_right'):
                    e = float(np.max(np.abs(trace[key][t+1] - row['post_action_pose'][key])))
                    alignment_error = max(alignment_error, e)
            contacts = row['parcel_contacts']
            hand_target = [c for c in contacts if any(target_label in n for n in c['shapes'])
                           and any(side + '_wrist_roll' in n for n in c['shapes'])]
            normal = tangent = 0.
            for c in hand_target:
                force = np.asarray(c['force_torque_contact'], dtype=float)
                frame = np.asarray(c['contact_frame'], dtype=float)
                assert force.shape == (6,) and frame.shape == (3, 3)
                assert np.isfinite(force).all()
                assert np.allclose(force[:3] @ frame, c['force_world_N'], atol=1e-6)
                assert np.allclose(frame @ frame.T, np.eye(3), atol=1e-4)
                normal += abs(float(force[0]))
                tangent += float(np.linalg.norm(force[1:3]))
            groups[control[t]['mode']].append(dict(step=t, points=len(hand_target),
                                                  normal_abs_sum_N=normal,
                                                  tangent_norm_sum_N=tangent))
    assert alignment_error < 1e-6, alignment_error
    summary = {}
    for mode, values in groups.items():
        normal = np.array([v['normal_abs_sum_N'] for v in values])
        tangent = np.array([v['tangent_norm_sum_N'] for v in values])
        summary[mode] = dict(samples=len(values), candidate_samples=sum(v['points'] > 0 for v in values),
                             load_above_001N_samples=int((normal > .01).sum()),
                             normal_mean_N=float(normal.mean()), normal_max_N=float(normal.max()),
                             tangent_mean_N=float(tangent.mean()), tangent_max_N=float(tangent.max()))
    results.append(dict(episode=str(raw.parent.relative_to(a.root)), primitive_applies=bool(meta['front_reposition_distance']),
                        raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                        force_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                        post_to_next_pre_max_error_m=alignment_error,
                        phases=summary, samples=dict(groups)))
    print(raw.parent.name, summary.get('retreat_x'), flush=True)
a.out.write_text(json.dumps(dict(rows=results, training_ready=False, goal_complete=False,
    scope='Final physics tick samples only. Absolute contact normal and tangential magnitudes; no net force sign, impulse, friction identification or causal inference. Hand filter wrist_roll labels includes rubber hand and wrist collisions.'), indent=2))
