#!/usr/bin/env python3
"""Counterfactual waist input on teacher observations, paired CUDA noise. No deployment."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from pi05_policy_server import Pi05Server


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-report', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(exist_ok=False, parents=True)
    baseline = json.loads(a.baseline_report.read_text())
    cp = Path(baseline['checkpoint'])
    cfg = json.loads((cp / 'train_config.json').read_text())
    dataset = Path(cfg['dataset']['root'])
    records = json.loads((dataset / 'meta/paired_provenance.json').read_text())['records']
    by_hash = {r['hash']: r for r in records}
    server = Pi05Server(argparse.Namespace(policy_path=cp, dataset_root=dataset,
        repo_id=cfg['dataset']['repo_id'], tokenizer_path=Path('/home/user/Documents/zoo/sim/lerobot/models/paligemma-3b-pt-224'),
        device='cuda:0', seed=0, num_inference_steps=10))
    server.warmup()
    rows = []
    saved = {}
    max_replay_error = 0.
    with np.load(a.baseline_report.parent / 'predictions.npz') as reference:
        for row in baseline['rows']:
            src = by_hash[row['raw_sha256']]
            raw = Path(src['path'])
            assert hashlib.sha256(raw.read_bytes()).hexdigest() == row['raw_sha256']
            ix = [*range(13,23),12]
            with np.load(raw) as z:
                rgb = z['rgb'].copy(); q = z['q'][:,ix].copy(); gt = z['action'][:,ix].copy()
            torch.manual_seed(row['seed']); np.random.seed(row['seed'])
            chunks = {'original': [], 'waist_zero': []}
            for t in range(0,160,10):
                before = torch.cuda.get_rng_state()
                pred = server.infer(rgb[t].transpose(1,2,0), q[t], src['exported_prompt'])
                after = torch.cuda.get_rng_state()
                modified = q[t].copy(); modified[-1] = 0
                torch.cuda.set_rng_state(before)
                changed = server.infer(rgb[t].transpose(1,2,0), modified, src['exported_prompt'])
                torch.cuda.set_rng_state(after)
                chunks['original'].append(pred); chunks['waist_zero'].append(changed)
            err = float(np.max(np.abs(np.stack(chunks['original']) - reference[row['prediction_key']])))
            max_replay_error = max(max_replay_error, err)
            assert err < 1e-6, f'Baseline replay mismatch: {err}'
            for variant, values in chunks.items():
                stitched = np.concatenate([v[:10] for v in values])
                delta = np.abs(np.diff(stitched[:,:10], axis=0))
                steps = delta.max(axis=1)
                frames = (np.flatnonzero(steps > .08) + 1).tolist()
                key = row['prediction_key'] + '_' + variant
                saved[key] = np.stack(values)
                rows.append({k:row[k] for k in ['raw_sha256','seed','task','partition','layout_id']} | {
                    'variant': variant,'prediction_key':key,'abrupt_frames':frames,
                    'boundary_events':sum(t%10==0 for t in frames),
                    'max_action_step_rad':float(steps.max()),
                    'arm_action_rmse_rad':float(np.sqrt(np.mean((stitched[:,:10]-gt[:,:10])**2))),
                    'max_abs_waist_input_rad':float(np.max(np.abs(q[::10,-1])))})
            print('PAIRED_WAIST', row['prediction_key'], 'done', flush=True)
    summary = []
    for variant in ['original','waist_zero']:
        rs = [r for r in rows if r['variant']==variant]
        summary.append({'variant':variant,'trajectories':len(rs),'trajectories_with_abrupt_step':sum(bool(r['abrupt_frames']) for r in rs),
            'events':sum(len(r['abrupt_frames']) for r in rs),'boundary_events':sum(r['boundary_events'] for r in rs),
            'mean_arm_rmse_rad':float(np.mean([r['arm_action_rmse_rad'] for r in rs]))})
    np.savez_compressed(a.out/'predictions.npz', **saved)
    (a.out/'REPORT.json').write_text(json.dumps({'checkpoint':str(cp),'baseline_report':str(a.baseline_report.resolve()),
        'baseline_replay_max_abs_error':max_replay_error,'summary':summary,'rows':rows,
        'method':'Identical RGB/prompt and fresh original CUDA noise sequence; restore each query RNG for waist-zero counterfactual and restore original next RNG. Exact replay baseline verified.',
        'limitations':'Synthetic single-state-component intervention on selected expert observations; not physical recovery, task success, or proof of causal data defect. No inference server, training, raw data, action or quality gate changed. No mask adopted.',
        'goal_complete':False},indent=2))
    print(json.dumps(summary,indent=2),flush=True)


if __name__ == '__main__':
    main()
