#!/usr/bin/env python3
"""Independent post-launch gate: the simulator launcher may swallow exit codes."""
import argparse,json
from pathlib import Path

def check(root, expected_episodes):
    root=Path(root)
    status=json.loads((root/'STATUS.json').read_text())
    if status.get('status')!='numeric_pass_visual_review_pending':
        raise ValueError(f'{root}: collector did not pass: {status}')
    manifest=json.loads((root/'manifest.json').read_text())
    paths=sorted(root.glob('layout_*/quality.json'))
    if len(paths)!=expected_episodes or sum(len(g['episodes']) for g in manifest)!=expected_episodes:
        raise ValueError('Missing/extra episodes after collector returned')
    for group in manifest:
        if not all(row.get('passed') is True for row in group['episodes']):
            raise ValueError('Manifest contains failed quality gate')
        if 'pair' in group and group['pair'].get('passed') is not True:
            raise ValueError('Paired initial scene check failed')
    for p in paths:
        if json.loads(p.read_text()).get('passed') is not True or not (p.parent/'raw.npz').is_file():
            raise ValueError(f'Failed/incomplete episode: {p.parent}')
    return {'numeric_pass':True,'episodes':expected_episodes,'visual_review':'still required','training_ready':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--episodes',type=int,required=True);a=p.parse_args();print(json.dumps(check(a.root,a.episodes)))
