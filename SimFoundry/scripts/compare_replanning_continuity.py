#!/usr/bin/env python3
"""Compare existing teacher-observation replay audits, preserving their exact gates."""
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reports', type=Path, nargs='+', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    reference = None
    results = []
    for path in a.reports:
        d = json.loads(path.read_text())
        rows = d['rows']
        keys = [(r['raw_sha256'], r['seed']) for r in rows]
        assert len(keys) == len(set(keys))
        if reference is None:
            reference = set(keys)
        assert set(keys) == reference, 'Different source demonstrations or seeds'
        events = [e for r in rows for e in r['events']]
        active = 0
        inactive = 0
        for r in rows:
            left = r['task'] == 'nudge_mailer_to_bin'
            for e in r['events']:
                is_active = (e['joint11_index'] < 5) == left
                active += is_active
                inactive += not is_active
        with np.load(path.parent / 'predictions.npz') as z:
            chunks = [z[r['prediction_key']] for r in rows]
            assert all(x.shape[0] == 16 and x.shape[1] >= 10 and x.shape[2] == 11 for x in chunks)
            seams = np.array([np.max(np.abs(x[1:, 0, :10] - x[:-1, 9, :10]), axis=1) for x in chunks])
            within = np.concatenate([np.abs(np.diff(x[:, :10, :10], axis=1)).max(axis=2).ravel() for x in chunks])
            assert int((seams > .08).sum()) == sum(e['at_chunk_boundary'] for e in events)
            assert int((within > .08).sum()) == sum(not e['at_chunk_boundary'] for e in events)
        results.append({
            'report': str(path.resolve()), 'checkpoint': d['checkpoint'],
            'trajectories': len(rows), 'trajectories_with_abrupt_step': sum(bool(r['events']) for r in rows),
            'events': len(events), 'active_arm_events': int(active), 'inactive_arm_events': int(inactive),
            'boundary_events': int((seams > .08).sum()), 'within_executed_chunk_events': int((within > .08).sum()),
            'boundary_step_mean_rad': float(seams.mean()), 'boundary_step_p95_rad': float(np.quantile(seams, .95)),
            'within_chunk_step_mean_rad': float(within.mean()), 'within_chunk_step_p95_rad': float(np.quantile(within, .95)),
            'event_joint11_histogram': dict(sorted(Counter(e['joint11_index'] for e in events).items())),
            'event_frame_histogram': dict(sorted(Counter(e['frame'] for e in events).items())),
            'mean_action_rmse_rad': float(np.mean([r['action_rmse_rad'] for r in rows])),
        })
    a.out.write_text(json.dumps({'results': results, 'matched_demonstration_seed_pairs': len(reference),
        'limitations': 'Teacher-observation replay on selected two geometry groups only; not physical success. Each model uses its original saved prediction length. Noise draws differ for different tensor shapes. No gate changes or action filtering.',
        'goal_complete': False}, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
