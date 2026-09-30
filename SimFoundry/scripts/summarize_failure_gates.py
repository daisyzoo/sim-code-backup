#!/usr/bin/env python3
"""Explain existing unchanged gates; auxiliary counts never redefine success."""
import argparse
import json
from pathlib import Path
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summaries', type=Path, nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    results = []
    for path in args.summaries:
        report = json.loads(path.read_text())
        buckets = defaultdict(list)
        for row in report['rows']:
            assert row['passed'] == (not row['reasons'])
            buckets[row['task']].append(row)
        for task, rows in sorted(buckets.items()):
            def count(predicate):
                return sum(any(predicate(reason) for reason in row['reasons']) for row in rows)
            only_abrupt = [row for row in rows if row['reasons'] and all(reason.startswith('abrupt action step ') for reason in row['reasons'])]
            results.append({
                'source': str(path.resolve()), 'task': task, 'total': len(rows),
                'passed_original_gate': sum(row['passed'] for row in rows),
                'only_action_discontinuity_failure': len(only_abrupt),
                'any_action_discontinuity': count(lambda reason: reason.startswith('abrupt action step ')),
                'any_target_zone_or_progress_failure': count(lambda reason: reason.startswith('target did not finish stably')),
                'any_non_target_movement': count(lambda reason: reason.startswith('non-target/idle')),
                'any_target_still_moving': count(lambda reason: reason == 'target still moving at end'),
                'any_wrong_way': count(lambda reason: reason.startswith('target wrong-way')),
                'any_palm_table_overlap': count(lambda reason: 'palm/table overlap' in reason),
                'any_idle_palm_drift': count(lambda reason: reason.startswith('idle ') and 'palm drift' in reason),
                'only_discontinuity_cases': [{'seed': row['seed'], 'layout_id': row['layout_id']} for row in only_abrupt],
            })
    args.out.write_text(json.dumps({
        'summary': results,
        'note': 'Failure categories overlap. Only-discontinuity cases still FAIL; not an alternative success rate. All original gates and source results remain unchanged.',
        'goal_complete': False,
    }, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
