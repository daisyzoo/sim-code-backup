#!/usr/bin/env python3
"""Summarize completed h10 runs without treating numeric gates as visual review."""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def summarize(roots):
    rows, pairs, seen = [], [], set()
    for root in roots:
        if json.loads((root/'STATUS.json').read_text())['status'] != 'evaluation_complete':
            raise ValueError(f'incomplete evaluation: {root}')
        args = json.loads((root/'provenance.json').read_text())['args']
        if args['horizon'] != 10 or not args['policy_port'] or not args['newton_contacts']:
            raise ValueError(f'incorrect evaluation protocol: {root}')
        for group in json.loads((root/'manifest.json').read_text()):
            if 'pair' in group:
                pairs.append({'seed': args['eval_seed'], 'layout_id': group['layout']['layout_id'], **group['pair']})
        paths = sorted(root.glob('layout_*/quality.json'))
        expected = args['layouts']*2 + args['wait_episodes']
        if len(paths) != expected:
            raise ValueError(f'missing rollout: {root}: {len(paths)}/{expected}')
        for path in paths:
            parts = path.parent.name.split('_', 2)
            layout_id, task = int(parts[1]), parts[2]
            key = (args['prompt_variant'], args['eval_seed'], layout_id, task)
            if key in seen:
                raise ValueError(f'duplicate result {key}')
            seen.add(key)
            report = json.loads(path.read_text())
            rows.append({'seed': args['eval_seed'], 'layout_id': layout_id, 'task': task,
                         'variant': args['prompt_variant'], 'path': str(path.parent), **report})
    groups = defaultdict(list)
    for row in rows:
        groups[(row['variant'],row['task'])].append(row)
    summary = []
    for (variant,task), group in sorted(groups.items()):
        summary.append({'variant': variant, 'task': task, 'numerical_pass': sum(r['passed'] for r in group),
                        'total': len(group), 'seeds': sorted(set(r['seed'] for r in group)),
                        'min_target_progress_m': min((r['metrics']['target_final_progress_m'] for r in group
                            if 'target_final_progress_m' in r['metrics']), default=None)})
    return {'summary': summary, 'rows': rows, 'pairs': pairs,
            'paired_reset_checks_passed': all(p['passed'] for p in pairs),
            'visual_review': 'pending',
            'note': 'Numeric quality gates only. Small constrained-layout pilot; not a generalization claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = summarize(args.roots)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({'summary':result['summary'], 'paired_reset_checks_passed':result['paired_reset_checks_passed']}, indent=2))

if __name__ == '__main__':
    main()
