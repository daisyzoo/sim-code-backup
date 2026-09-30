#!/usr/bin/env python3
"""Offline point-IK map for current expert waypoints; not task-feasibility proof."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from probe_sorting_kinematics import ArmFK


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(exist_ok=False, parents=True)
    source = Path(__file__).resolve().parents[1] / 'demo/spatial_candidate_pool72_20260928_r1'
    models = {side: ArmFK(side) for side in ['left', 'right']}
    warm = {side: [np.zeros(5)] for side in models}
    errors = []
    for lid in [62014, 62015]:
        for raw in sorted((source / f'case_{lid}').glob('layout_*/raw.npz')):
            with np.load(raw) as data, np.load(raw.parent / 'trace.npz') as trace:
                for side, start in [('left', 13), ('right', 18)]:
                    for frame in [0, 20, 50, 90, 130, 159]:
                        q = data['q'][frame, start:start + 5]
                        palm = models[side].palm(q, data['q'][frame, 12])
                        errors.append(float(np.linalg.norm(palm - trace['palm_' + side][frame])))
                        warm[side].append(q.copy())
    assert max(errors) < 1e-4
    xs = [.36, .385, .41, .435, .46, .485, .51]
    ys = [-.16, -.12, -.08, -.04, 0., .04, .08, .12, .16]
    rng = np.random.default_rng(20260928)
    rows = []
    for x in xs:
        offset = -.11 if x >= .48 else -.13
        for y in ys:
            row = {'object_x': x, 'object_y': y, 'contact_offset': offset, 'arms': {}}
            for side, model in models.items():
                direction = 1 if side == 'left' else -1
                lo, hi = np.array(model.bounds).T
                arm = {}
                for phase, z in [('stage', .92), ('contact', .84 if side == 'left' else .845)]:
                    target = np.array([x, y + direction * offset, z])
                    nearest = min(warm[side], key=lambda q: np.linalg.norm(model.palm(q) - target))
                    starts = [np.zeros(5), np.clip(nearest, lo + 1e-8, hi - 1e-8), np.clip(nearest + rng.normal(0, .25, 5), lo + 1e-8, hi - 1e-8)]
                    best = None
                    for initial in starts:
                        fit = least_squares(lambda q: model.palm(q) - target, initial, bounds=(lo, hi), max_nfev=160, ftol=1e-9, xtol=1e-9, gtol=1e-9)
                        error = float(np.linalg.norm(fit.fun))
                        if best is None or error < best['residual_m']:
                            best = {'residual_m': error, 'q': fit.x.tolist(), 'target': target.tolist(), 'palm': model.palm(fit.x).tolist()}
                    arm[phase] = best
                row['arms'][side] = arm
            row['max_four_waypoint_residual_m'] = max(value['residual_m'] for arm in row['arms'].values() for value in arm.values())
            rows.append(row)
        print('WAYPOINT_COLUMN', x, 'done', flush=True)
    report = {
        'rows': rows, 'fk_max_error_m': max(errors), 'fk_validation_samples': len(errors),
        'method': 'Three-start constrained point IK per arm/stage/contact; waist fixed0, configured current distance-based lateral offsets. Same task hand must reach each category-swappable object slot.',
        'limitations': 'Only current waypoint design, not all possible pushing strategies. Best residual from local IK is not a global impossibility certificate. Ignores hand orientation, collisions, non-target obstacles, force, effort and trajectory dynamics. Zero residual does not imply task success. No collection or training admission.',
        'training_ready': False,
    }
    (args.out / 'REPORT.json').write_text(json.dumps(report, indent=2))
    print('rows', len(rows), 'slots with all4 waypoint residuals under15mm', sum(row['max_four_waypoint_residual_m'] < .015 for row in rows), flush=True)


if __name__ == '__main__':
    main()
