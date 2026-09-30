#!/usr/bin/env python3
"""Summarize exported privileged search trajectories without claiming visual review."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
rows=[];counts=collections.Counter();groups=collections.defaultdict(list)
for folder in sorted(a.root.glob('env_*')):
    meta=json.loads((folder/'meta.json').read_text());path=folder/'trajectory.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==meta['trajectory_sha256']
    task=meta['task_id'];obj='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if obj=='box' else 'box';hand='right' if obj=='box' else 'left';start=18 if obj=='box' else 13
    report=meta['report'];metrics=report['metrics'];categories=[]
    with np.load(path) as z:
        assert z['action'].shape==z['q'].shape==(160,23)
        assert np.max(np.abs(z['q'][0,12:]))<1e-4 and np.max(np.abs(z['action'][0,12:]))<1e-4 and np.all(z['action'][:,12]==0)
        target=z[obj];palm=z['palm_'+hand];xy=np.linalg.norm(palm[:,:2]-target[:,:2],axis=1);height=np.abs(palm[:,2]-target[:,2])
        proximity=(xy<.13)&(height<.10);target_motion=float(np.linalg.norm(target[:,:2]-target[0,:2],axis=1).max())
        if target_motion<.002:categories.append('target_motion_below_2mm')
        if proximity.sum()<3:categories.append('no_sustained_target_proximity')
        if metrics['target_final_progress_m']<.15:categories.append('progress_below_150mm')
        if metrics['wrong_way_m']>.035:categories.append('wrong_direction_excursion')
        if metrics[other+'_max_xy_m']>.015:categories.append('non_target_interference')
        if any('palm/table' in x for x in report['reasons']):categories.append('table_overlap_proxy')
        if not meta['fitness']['upright']:categories.append('excessive_tilt')
        if not meta['fitness']['support']:categories.append('footprint_outside_table')
        row=dict(env_id=meta['env_id'],layout_id=meta['layout']['layout_id'],geometry_group=meta['layout'].get('geometry_group'),task=task,
            passed=report['passed'],search_success=meta['fitness']['search_success'],categories=categories,
            target_max_xy_m=target_motion,target_progress_m=metrics['target_final_progress_m'],non_target_max_xy_m=metrics[other+'_max_xy_m'],
            target_proximity_frames=int(proximity.sum()),palm_target_min_xyz_distance_m=float(np.linalg.norm(palm-target,axis=1).min()),
            active_command_range_rad=np.ptp(z['action'][:,start:start+5],axis=0).tolist(),
            command_minus_pre_action_q_rms_rad=float(np.sqrt(np.mean((z['action'][:,start:start+5]-z['q'][:,start:start+5])**2))),
            reasons=report['reasons'],trajectory_sha256=meta['trajectory_sha256'])
    rows.append(row);counts.update(categories);groups[(row['geometry_group'],meta['env_id']//8)].append(row)
group_rows=[]
for (name,repeat),members in groups.items():
    unique={(x['layout_id'],x['task']) for x in members}
    group_rows.append(dict(geometry_group=name,repeat=repeat,episodes=len(members),unique_cases=len(unique),
        complete_four_case_group=len(members)==4 and len(unique)==4,
        all_search_success=len(members)==4 and len(unique)==4 and all(x['search_success'] for x in members)))
a.out.write_text(json.dumps(dict(rows=rows,overlapping_failure_counts=dict(counts),groups=group_rows,
    scope='Numerical trajectory diagnosis on training layouts. Proximity and command/pre-action difference are geometric/tracking proxies, not contact-force or causal measurements. No RGB review or independent VLA evaluation.',training_ready=False,goal_complete=False),indent=2))
print(json.dumps(dict(episodes=len(rows),search_success=sum(x['search_success'] for x in rows),failures=dict(counts),whole_groups_pass=sum(x['all_search_success'] for x in group_rows))),flush=True)
