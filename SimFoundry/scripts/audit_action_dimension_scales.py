#!/usr/bin/env python3
"""Read-only physical-unit error and normalization-scale audit for matched models."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--reports', type=Path, nargs='+', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    stat_path = a.dataset / 'meta/train_only_stats.json'
    stats = json.loads(stat_path.read_text())
    span = np.array(stats['action']['max']) - np.array(stats['action']['min'])
    assert span.shape == (11,) and np.all(span[:10] > 0) and span[10] == 0
    names = stats['joint_order']
    records = json.loads((a.dataset / 'meta/paired_provenance.json').read_text())['records']
    by_hash = {r['hash']: Path(r['path']) for r in records}
    labels = {}
    reference = None
    results = []
    for path in a.reports:
        report = json.loads(path.read_text())
        cp = Path(report['checkpoint'])
        config = json.loads((cp / 'train_config.json').read_text())
        assert Path(config['dataset']['root']).resolve() == a.dataset.resolve()
        assert config['policy']['normalization_mapping']['ACTION'] == 'MIN_MAX'
        keys = {(r['raw_sha256'], r['seed']) for r in report['rows']}
        assert len(keys) == len(report['rows'])
        if reference is None:
            reference = keys
        assert keys == reference
        errors = []
        events = Counter()
        with np.load(path.parent / 'predictions.npz') as preds:
            for r in report['rows']:
                digest = r['raw_sha256']
                if digest not in labels:
                    raw = by_hash[digest]
                    assert hashlib.sha256(raw.read_bytes()).hexdigest() == digest
                    with np.load(raw) as z:
                        labels[digest] = z['action'][:, 13:23].astype(np.float64)
                pred = preds[r['prediction_key']][:, :10, :10].reshape(160, 10)
                errors.append(pred - labels[digest])
                events.update(e['joint11_index'] for e in r['events'])
        error = np.concatenate(errors)
        raw_mse = np.mean(error**2, axis=0)
        normalized_mse = raw_mse * (2 / span[:10])**2
        rows = []
        for j in range(10):
            rows.append({'joint11_index': j, 'joint': names[j], 'action_range_rad': float(span[j]),
                'normalized_error_for_0p08rad': float(.16 / span[j]),
                'normalized_squared_error_per_rad_squared': float((2 / span[j])**2),
                'inference_raw_rmse_rad': float(np.sqrt(raw_mse[j])),
                'inference_normalized_rmse': float(np.sqrt(normalized_mse[j])),
                'share_of_raw_squared_error': float(raw_mse[j] / raw_mse.sum()),
                'share_of_normalized_squared_error': float(normalized_mse[j] / normalized_mse.sum()),
                'largest_joint_at_abrupt_events': events[j]})
        results.append({'report': str(path.resolve()), 'checkpoint': str(cp), 'rows': rows,
                        'total_abrupt_events': sum(events.values())})
    out = {'dataset': str(a.dataset.resolve()), 'train_stats_sha256': hashlib.sha256(stat_path.read_bytes()).hexdigest(),
        'results': results, 'matched_pairs': len(reference),
        'physical_error_penalty_ratio_right_wrist_vs_right_elbow': float((span[8] / span[9])**2),
        'limitations': 'Inference action errors on24 teacher-observation trajectories, NOT measured training flow-velocity losses. MIN_MAX implies the displayed error metric, but scale disparity is not by itself a bug or causal proof. State, visual grounding, noise, and closed-loop coverage remain possible contributors. Waist excluded because its target range is zero. No model, data, loss, or gate changed.',
        'goal_complete': False}
    a.out.write_text(json.dumps(out, indent=2))
    print('right wrist/elbow equal-physical-error normalized squared penalty ratio:', out['physical_error_penalty_ratio_right_wrist_vs_right_elbow'])
    for r in results:
        print(r['checkpoint'])
        for d in r['rows']:
            print(d['joint11_index'], 'rawRMSE', round(d['inference_raw_rmse_rad'],5), 'raw_share',round(d['share_of_raw_squared_error'],3),'normalized_share',round(d['share_of_normalized_squared_error'],3),'events',d['largest_joint_at_abrupt_events'])


if __name__ == '__main__':
    main()
