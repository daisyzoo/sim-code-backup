#!/usr/bin/env python3
"""Validate local evaluation membership and actual frame counts, not success."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def audit(summary, protocol, allow_partial=False):
    layouts=[]
    for item in protocol['layout_files']:
        p=Path(item['path'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed layout')
        layouts.append(json.loads(p.read_text())['layout_id'])
    expected={(seed,lid,task) for seed in protocol['eval_seeds'] for lid in layouts for task in ['push_box_to_bin','nudge_mailer_to_bin']}
    expected|={(seed,protocol['wait_layout_id'],'wait_no_package') for seed in protocol['eval_seeds']}
    seen=set();rows=[]
    for row in summary['rows']:
        key=(row['seed'],row['layout_id'],row['task'])
        if key in seen or key not in expected:raise ValueError(f'Unexpected or repeated episode: {key}')
        seen.add(key);folder=Path(row['path'])
        quality=json.loads((folder/'quality.json').read_text())
        with np.load(folder/'raw.npz') as raw:
            frames=len(raw['q'])
            if len(raw['action'])!=frames or len(raw['rgb'])!=frames:raise ValueError('Unequal trajectory lengths')
        expected_frames=protocol['wait_steps'] if row['task']=='wait_no_package' else protocol['push_steps']
        if frames!=expected_frames or quality['frames']!=expected_frames:
            raise ValueError(f'{key}: actual {frames} frames, protocol requires {expected_frames}')
        args=json.loads((folder.parent/'provenance.json').read_text())['args']
        if args['horizon']!=protocol['horizon'] or args['policy_max_action_step']!=protocol['policy_action_step_cap'] or args['eval_seed']!=row['seed'] or not args['policy_port']:
            raise ValueError('Policy execution protocol differs')
        rows.append(dict(key=key,frames=frames,raw_sha256=hashlib.sha256((folder/'raw.npz').read_bytes()).hexdigest()))
    if not allow_partial and seen!=expected:raise ValueError(f'Incomplete coverage: {len(seen)}/{len(expected)}')
    return dict(passed=True,complete=seen==expected,episodes=len(rows),expected_episodes=len(expected),rows=rows,scope='Membership, actual q/action/RGB lengths, recorded h10/cap/seed. Does not establish physical success, solver implementation, or visual review.',goal_complete=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--summary',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    result=audit(json.loads(a.summary.read_text()),json.loads(a.protocol.read_text()))
    result['protocol_sha256']=hashlib.sha256(a.protocol.read_bytes()).hexdigest()
    a.out.write_text(json.dumps(result,indent=2));print('Budget audit passed:',result['episodes'])

if __name__=='__main__':main()
