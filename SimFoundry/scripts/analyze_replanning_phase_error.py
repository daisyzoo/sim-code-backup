#!/usr/bin/env python3
"""Diagnose saved prediction error within executed h10 windows against exact raw labels."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--reports', nargs='+', type=Path, required=True)
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    records = json.loads((a.dataset / 'meta/paired_provenance.json').read_text())['records']
    raw_by_hash = {r['hash']: Path(r['path']) for r in records}
    ground_truth = {}
    reference = None
    results = []
    for path in a.reports:
        report = json.loads(path.read_text())
        keys = {(r['raw_sha256'], r['seed']) for r in report['rows']}
        assert len(keys) == len(report['rows'])
        if reference is None:
            reference = keys
        assert keys == reference
        errors = []
        seam_error_changes = []
        seam_gt_steps = []
        seam_pred_steps = []
        with np.load(path.parent / 'predictions.npz') as pred:
            for row in report['rows']:
                digest = row['raw_sha256']
                if digest not in ground_truth:
                    raw = raw_by_hash[digest]
                    assert hashlib.sha256(raw.read_bytes()).hexdigest() == digest
                    with np.load(raw) as z:
                        ground_truth[digest] = z['action'][:, 13:23].astype(np.float64)
                gt = ground_truth[digest]
                chunks = pred[row['prediction_key']][:, :10, :10].astype(np.float64)
                assert chunks.shape == (16, 10, 10) and gt.shape == (160, 10)
                error = chunks - gt.reshape(16, 10, 10)
                errors.append(error)
                seam_error_changes.append(error[1:, 0] - error[:-1, 9])
                seam_gt_steps.append(gt[10::10] - gt[9:-1:10])
                seam_pred_steps.append(chunks[1:, 0] - chunks[:-1, 9])
        e = np.stack(errors)
        de = np.concatenate(seam_error_changes)
        dg = np.concatenate(seam_gt_steps)
        dp = np.concatenate(seam_pred_steps)
        assert np.max(np.abs(dp - dg - de)) < 1e-12
        results.append({
            'report': str(path.resolve()), 'trajectories': len(errors),
            'executed_chunk_offset_rmse_rad': np.sqrt(np.mean(e**2, axis=(0,1,3))).tolist(),
            'executed_chunk_offset_signed_mean_error_rad': np.mean(e, axis=(0,1,3)).tolist(),
            'seam_gt_step_max_rad': float(np.max(np.abs(dg))),
            'seam_pred_step_max_rad': float(np.max(np.abs(dp))),
            'seam_prediction_error_change_max_rad': float(np.max(np.abs(de))),
            'seam_prediction_error_change_rms_rad': float(np.sqrt(np.mean(de**2))),
            'note': 'Exact identity: predicted seam step = expert seam step + change in prediction error. Descriptive decomposition, not a causal noise/phase diagnosis.',
        })
    a.out.write_text(json.dumps({'results': results, 'matched_pairs': len(reference),
        'limitations': 'Selected expert observations, not physical rollout; per-offset errors are correlated. Predictions use saved original noise and chunk lengths. No smoothing, gates or trained model changed.',
        'goal_complete': False}, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
