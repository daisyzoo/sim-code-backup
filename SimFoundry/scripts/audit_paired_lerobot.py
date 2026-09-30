#!/usr/bin/env python3
"""Verify every exported state/action/task row and decode sampled video frames."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from simfoundry.data.schema import load_episode
from simfoundry.data.diverse_layouts import validate_geometry_split
INDICES = [*range(13, 23), 12]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--repo-id', required=True)
    args = parser.parse_args()
    root = args.dataset
    import pandas as pd
    import pyarrow.parquet as pq
    provenance = json.loads((root/'meta/paired_provenance.json').read_text())
    records = provenance['records']
    split = json.loads((root/'meta/train_validation_split.json').read_text())
    tasks = pd.read_parquet(root/'meta/tasks.parquet')
    task_names = {int(row['task_index']): str(name) for name, row in tasks.iterrows()}
    table = pd.concat([pq.read_table(p).to_pandas() for p in sorted((root/'data').glob('chunk-*/file-*.parquet'))], ignore_index=True)
    if set(table.episode_index) != set(range(len(records))):
        raise ValueError('export episode indices mismatch')
    train, val = set(split['train']), set(split['validation'])
    if train & val or train | val != set(range(len(records))):
        raise ValueError('invalid train/validation coverage')
    if {records[i]['layout_id'] for i in train} & {records[i]['layout_id'] for i in val}:
        raise ValueError('layout leakage')
    validate_geometry_split(records, {records[i]['layout_id'] for i in val})
    for i, record in enumerate(records):
        actual_split = 'train' if i in train else 'validation'
        if record.get('planned_split', actual_split) != actual_split:
            raise ValueError('Export changed a preassigned pilot split or included test data')
    repo = ROOT.parent / 'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth'
    sys.path.insert(0, str(repo/'unitree_lerobot/lerobot/src'))
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    ds = LeRobotDataset(args.repo_id, root=root, video_backend='pyav')
    image_checks, max_mae, train_frames = 0, 0., 0
    for i, record in enumerate(records):
        path = Path(record['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['hash']:
            raise ValueError(f'source changed after conversion: {path}')
        ep = load_episode(path)
        rows = table[table.episode_index == i].sort_values('frame_index')
        if len(rows) != len(ep.q) or rows.frame_index.tolist() != list(range(len(ep.q))):
            raise ValueError(f'episode {i}: dropped/duplicated frames')
        q = np.stack(rows['observation.state'].to_numpy())
        a = np.stack(rows['action'].to_numpy())
        np.testing.assert_allclose(q, ep.q[:,INDICES], rtol=0, atol=1e-6)
        np.testing.assert_allclose(a, ep.action[:,INDICES], rtol=0, atol=1e-6)
        if np.abs(q[0]).max() >= 1e-4 or np.abs(a[0]).max() >= 1e-4:
            raise ValueError(f'episode {i}: exported initial state/action is not zero')
        np.testing.assert_allclose(rows.timestamp, np.arange(len(rows))/15., atol=1e-5)
        if {task_names[int(t)] for t in rows.task_index} != {record['exported_prompt']}:
            raise ValueError(f'episode {i}: task text/index mismatch')
        for t in (0, len(rows)//2, len(rows)-1):
            item = ds[int(rows.iloc[t]['index'])]
            if item['task'] != record['exported_prompt']:
                raise ValueError('dataloader changed prompt')
            decoded = item['observation.images.color_0'].cpu().numpy()
            if decoded.shape[-1] == 3:
                decoded = decoded.transpose(2,0,1)
            if decoded.max() <= 1.5:
                decoded = decoded*255.
            mae = float(np.abs(decoded.astype(float)-ep.rgb[t]).mean())
            if mae > 8.:
                raise ValueError(f'episode {i} frame {t}: decoded image mismatch MAE={mae:.3f}')
            max_mae = max(max_mae, mae)
            image_checks += 1
        if i in train:
            train_frames += len(rows)
    report = {'training_ready': True, 'episodes': len(records), 'frames': len(table),
              'train_frames': train_frames, 'train_episodes': len(train), 'validation_episodes': len(val),
              'image_checks': image_checks, 'max_decoded_image_mae': max_mae,
              'task_names': list(task_names.values()), 'layout_leakage': False,
              'state_action_rows_verified': len(table)}
    (root/'meta/paired_export_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
