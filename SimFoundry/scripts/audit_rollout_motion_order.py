#!/usr/bin/env python3
"""Read-only temporal motion audit; displacement/proximity never imply contact force."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def first(a):
    ids = np.flatnonzero(a)
    return int(ids[0]) if len(ids) else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    source = json.loads(a.comparison.read_text())
    assert len(source['rows']) == 60
    rows = []
    for trial in source['rows']:
        task = trial['task']
        if task == 'wait_no_package':
            continue
        folder = Path(trial['candidate']['path'])
        target, other, side = ('box', 'mailer', 'right') if task == 'push_box_to_bin' else ('mailer', 'box', 'left')
        with np.load(folder/'trace.npz', allow_pickle=False) as tr:
            xyz = {k: tr[k].copy() for k in [target, other, 'palm_'+side]}
        n = len(xyz[target])
        assert n == 160 and all(v.shape == (n,3) and np.isfinite(v).all() for v in xyz.values())
        motion = {k: np.linalg.norm(xyz[k][:,:2]-xyz[k][0,:2], axis=1) for k in [target, other]}
        onsets = {}
        for mm in (2,5,15):
            ti, oi = first(motion[target] > mm/1000), first(motion[other] > mm/1000)
            onsets[str(mm)] = {'target_frame':ti, 'non_target_frame':oi,
                'non_target_before_target':oi is not None and (ti is None or oi < ti)}
        snapshots = []
        for t in sorted({0,40,80,120,159} | {x for v in onsets.values() for x in (v['target_frame'],v['non_target_frame']) if x is not None}):
            palm=xyz['palm_'+side][t]
            snapshots.append({'frame':t,'target_xy_displacement_m':float(motion[target][t]),
                'non_target_xy_displacement_m':float(motion[other][t]),
                'active_palm_target_center_distance_m':float(np.linalg.norm(palm-xyz[target][t])),
                'active_palm_non_target_center_distance_m':float(np.linalg.norm(palm-xyz[other][t]))})
        q = json.loads((folder/'quality.json').read_text())
        assert q['passed'] == trial['candidate']['passed'] and q['reasons'] == trial['candidate']['reasons']
        rows.append({'distribution':trial['distribution'],'seed':trial['seed'],'layout_id':trial['layout_id'],
            'task':task,'distance':trial['distance'],'path':str(folder),'passed':q['passed'],
            'reasons':q['reasons'],'motion_onsets_mm':onsets,'snapshots':snapshots,
            'raw_sha256':hashlib.sha256((folder/'raw.npz').read_bytes()).hexdigest(),
            'trace_sha256':hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest()})
    assert len(rows) == 54
    violations=[r for r in rows if any(x.startswith('non-target') for x in r['reasons'])]
    summary={'push_episodes':54,'non_target_violations':len(violations),
        'violations_with_non_target_moving_first_by_threshold_mm':{str(mm):sum(r['motion_onsets_mm'][str(mm)]['non_target_before_target'] for r in violations) for mm in (2,5,15)}}
    a.out.write_text(json.dumps({'summary':summary,'rows':rows,'method':'All54 completed push traces, prespecified XY displacement onsets at2/5/15mm from initial object center; report all thresholds. Active palm center distances only at fixed/onset frames. No model inference, action modification or training-data admission.',
        'limitations':'Onset ordering is descriptive, not causal. Palm center distance is not surface distance or contact force. Traces lack dynamic object quaternions. Reused development trials cannot establish independent generalization.','goal_complete':False},indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
