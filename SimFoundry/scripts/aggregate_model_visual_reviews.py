#!/usr/bin/env python3
"""Validate recorded actual reviews; cannot create or substitute visual review."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workflow', type=Path, required=True)
    p.add_argument('--prefix', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    root = (a.workflow / 'evaluation').resolve()
    episodes = {}
    sources = []
    for distribution, count in [('spatial', 13), ('original', 7)]:
        for seed in range(3):
            name = f'{a.prefix}_{distribution}_seed{seed}'
            material = root / 'visual_materials' / name
            review_path = material / 'review.json'
            review = json.loads(review_path.read_text())
            assert review['reviewed'] is True and len(review['episodes']) == count, name
            inventory = json.loads((material / 'inventory.json').read_text())
            assert len(inventory) == count, name
            expected = {}
            for row in inventory:
                raw = (Path(row['path']) / 'raw.npz').resolve()
                rel = str(raw.relative_to(root))
                assert rel.startswith(name + '/') and rel not in expected
                digest = hashlib.sha256(raw.read_bytes()).hexdigest()
                assert digest == row['raw_sha256'], rel
                expected[rel] = digest
                quality = json.loads((raw.parent / 'quality.json').read_text())
                assert quality['passed'] == row['passed'] and quality['reasons'] == row['reasons'], rel
            assert review['episodes'] == expected, name
            assert not set(episodes) & set(expected), name
            episodes.update(expected)
            sources.append({'path': str(review_path), 'sha256': hashlib.sha256(review_path.read_bytes()).hexdigest()})
    assert len(episodes) == 60
    actual = {str(p.resolve().relative_to(root)) for distribution in ['spatial', 'original'] for seed in range(3)
              for p in (root / f'{a.prefix}_{distribution}_seed{seed}').glob('**/raw.npz')}
    assert actual == set(episodes), 'Unreviewed or extra rollout'
    a.out.write_text(json.dumps({'reviewed': True,
        'method': 'Aggregate six recorded actual reviews, each five keyframes per episode, plus unchanged numeric inventory and freshly verified raw hashes. Not full-video review. This tool cannot itself inspect images.',
        'root': str(root), 'episodes': episodes, 'source_reviews': sources,
        'goal_complete': False}, indent=2))
    print('Verified60 episode hashes and6 recorded reviews. Workflow status unchanged.')


if __name__ == '__main__':
    main()
