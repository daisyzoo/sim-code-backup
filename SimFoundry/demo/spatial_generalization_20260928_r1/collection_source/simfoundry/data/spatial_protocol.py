"""Exact admission for fresh spatial pilots; diagnostic files never become pilots."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def validate_spatial_contract(path, *, layout_id, steps, staging_z, contact_offset, far_contact_offset=0.):
    path = Path(path)
    payload = path.read_bytes()
    c = json.loads(payload)
    if c.get('version') != 1 or c.get('approved_for_pilot') is not True:
        raise ValueError('Spatial pilot has not passed feasibility review')
    expected = {'steps': steps, 'staging_z': staging_z, 'contact_offset': contact_offset}
    if far_contact_offset or 'far_contact_offset' in c.get('expert', {}):
        expected['far_contact_offset'] = far_contact_offset
    if c.get('expert') != expected:
        raise ValueError('Expert settings differ from reviewed spatial contract')
    layouts = c.get('layouts', [])
    matches = [d for d in layouts if d.get('layout_id') == layout_id]
    if len(matches) != 1 or len({d['layout_id'] for d in layouts}) != len(layouts):
        raise ValueError('Unregistered or duplicate spatial layout')
    # Validate complete near/far swaps before any collection is admitted.
    groups = {}
    for d in layouts:
        groups.setdefault(d.get('geometry_group'), []).append(d)
    for key, rows in groups.items():
        if not isinstance(key, str) or not key or len(rows) != 2 or {d.get('assignment') for d in rows} != {'normal', 'swapped'}:
            raise ValueError('Spatial contract requires complete category-swap groups')
        a, b = rows
        if (a['box_xyz'][:2] != b['mailer_xyz'][:2] or a['mailer_xyz'][:2] != b['box_xyz'][:2]
                or a['seed'] != b['seed']):
            raise ValueError('Category assignments do not exchange the same two slots/seed')
        for angle in ('box_yaw', 'mailer_yaw'):
            if a.get(angle, 0.) != b.get(angle, 0.):
                raise ValueError('Category swap changes parcel orientation')
    # Evidence must be real reviewed successful groups, not a self-asserted flag.
    if not c.get('feasibility'):
        raise ValueError('Missing spatial feasibility evidence')
    diagnostic_ids = set()
    for evidence in c['feasibility']:
        root = Path(evidence['root'])
        review_path = root / 'visual_review.json'
        if hashlib.sha256(review_path.read_bytes()).hexdigest() != evidence['visual_review_sha256']:
            raise ValueError('Feasibility visual review changed')
        review = json.loads(review_path.read_text())
        if review.get('reviewed') is not True:
            raise ValueError('Feasibility images not reviewed')
        rows = json.loads((root / 'visual_evidence/inventory.json').read_text())
        approved_hashes = set(review.get('raw_sha256', []))
        if len(rows) < 4 or len(rows) % 4 or len(approved_hashes) != len(rows):
            raise ValueError('Incomplete feasibility group review')
        for row in rows:
            raw = Path(row['path']) / 'raw.npz'
            if not raw.is_absolute():
                raw = Path(__file__).resolve().parents[3] / raw
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()
            if not row['passed'] or digest != row['raw_sha256'] or digest not in approved_hashes:
                raise ValueError('Failed or changed feasibility trajectory')
        for f in root.glob('layout_*.json'):
            diagnostic_ids.add(json.loads(f.read_text())['layout_id'])
    if any(d['layout_id'] in diagnostic_ids for d in layouts):
        raise ValueError('Fresh pilot must use new layouts, not diagnostic IDs')
    return matches[0], hashlib.sha256(payload).hexdigest()
