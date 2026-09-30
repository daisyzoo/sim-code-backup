"""Check completed NPZ/Unitree pairs without importing the simulator.

Checks export integrity, recorded quality metadata and adjacent RGB continuity.
These checks do not establish visual collision freedom or policy improvement.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

import numpy as np


def check_pair(path: Path, unitree: Path) -> dict:
    index = int(re.search(r'_ep(\d+)\.npz$', path.name)[1])
    folder = unitree / f'episode_{index:04d}'
    with np.load(path, allow_pickle=False) as data:
        task = str(data['task_id'].item())
        meta = json.loads(str(data['collect_meta'].item()))
        rgb, q, action = data['rgb'], data['q'], data['action']
        names = list(map(str, data['joint_names']))
        prompt = str(data['instruction'].item())
    errors = []
    length = len(rgb)
    if rgb.shape[1:] != (3, 480, 640) or rgb.dtype != np.uint8:
        errors.append('unexpected RGB shape/dtype')
    if q.shape != (length, 23) or action.shape != (length, 23):
        errors.append('state/action shape mismatch')
    if not np.isfinite(q).all() or not np.isfinite(action).all():
        errors.append('nonfinite state/action')
    payload = json.loads((folder / 'data.json').read_text())
    frames, info = payload['data'], payload['info']
    if len(frames) != length or len(list((folder / 'colors').glob('*.jpg'))) != length:
        errors.append('frame count mismatch')
    if info['simfoundry']['task_id'] != task or payload['text']['goal'] != prompt:
        errors.append('task/prompt mismatch')
    if info['simfoundry'].get('collect') != meta:
        errors.append('collection metadata mismatch')
    if info['image']['fps'] != 15:
        errors.append('unexpected fps')
    for kind, array in (('states', q), ('actions', action)):
        for group, group_names in info['joint_names'].items():
            if not group_names:
                continue
            indices = [names.index(name) for name in group_names]
            exported = np.asarray([f[kind][group]['qpos'] for f in frames])
            if exported.shape != array[:, indices].shape or not np.allclose(exported, array[:, indices], atol=1e-6, rtol=0):
                errors.append(f'{kind}/{group} values mismatch')
    for i, frame in enumerate(frames):
        if frame['idx'] != i or not (folder / frame['colors']['color_0']).is_file():
            errors.append(f'missing/misindexed frame {i}')
            break
    if not meta.get('quality_gate') or meta.get('push_assist') or meta.get('assist_frames', -1) != 0:
        errors.append('missing gate or assisted data')
    if meta.get('table_pen_frames', -1) != 0:
        errors.append('recorded table penetration')
    if meta.get('wrong_way_excursion_y', 1) > .035:
        errors.append('recorded wrong-way threshold exceeded')
    if task != 'wait_no_package' and (meta.get('push_delta_y', 0) < .15 or meta.get('stable_zone_frames', 0) < 10):
        errors.append('recorded lateral success threshold not met')
    max_mad = max((float(np.abs(rgb[i].astype(np.int16) - rgb[i-1]).mean()) for i in range(1, length)), default=0)
    max_q_jump = float(np.abs(np.diff(q, axis=0)).max()) if length > 1 else 0
    return dict(index=index, task=task, frames=length, errors=errors,
                max_adjacent_rgb_mad=max_mad, max_state_jump=max_q_jump,
                continuity_review=max_mad >= 6 or max_q_jump >= .25,
                collect_meta=meta)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--npz-dir', type=Path, required=True)
    parser.add_argument('--unitree-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expect-total', type=int, default=300)
    args = parser.parse_args()
    rows = []
    for path in sorted(args.npz_dir.glob('*_ep*.npz')):
        try:
            rows.append(check_pair(path, args.unitree_dir))
        except Exception as exc:
            rows.append(dict(file=path.name, errors=[str(exc)]))
    counts = dict(Counter(r.get('task', 'unreadable') for r in rows))
    indices = sorted(r['index'] for r in rows if 'index' in r)
    folders = sorted(p.name for p in args.unitree_dir.glob('episode_*') if p.is_dir())
    complete = len(rows) == args.expect_total and indices == list(range(args.expect_total)) and folders == [f'episode_{i:04d}' for i in range(args.expect_total)]
    if args.expect_total == 300:
        complete &= counts == dict(push_box_to_bin=120, nudge_mailer_to_bin=120, wait_no_package=60)
    result = dict(complete=bool(complete), counts=counts, total=len(rows),
                  integrity_pass=bool(complete and not any(r['errors'] for r in rows)),
                  continuity_review_indices=[r.get('index') for r in rows if r.get('continuity_review')],
                  note='Integrity and heuristic continuity checks only; visual contact and PI0.5 effectiveness require separate validation.',
                  episodes=rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'episodes'}, ensure_ascii=False))
    raise SystemExit(0 if result['integrity_pass'] else 1)


if __name__ == '__main__':
    main()
