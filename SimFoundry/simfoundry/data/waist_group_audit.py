"""Complete category/slot counterfactual checks; does not admit diagnostic data."""
from collections import defaultdict
import math


def validate_complete_swap_layouts(layouts):
    groups = defaultdict(list)
    ids = set()
    for layout in layouts:
        identifier = layout['layout_id']
        if identifier in ids:
            raise ValueError('Duplicate layout ID')
        ids.add(identifier)
        group = layout.get('geometry_group')
        if not isinstance(group, str) or not group:
            raise ValueError('Missing geometry group')
        if layout.get('planned_split') not in ('development', 'train', 'validation'):
            raise ValueError('Unregistered split or held-out test geometry')
        for key in ('box_xyz', 'mailer_xyz'):
            if len(layout[key]) != 3 or not all(math.isfinite(x) for x in layout[key]):
                raise ValueError('Invalid parcel position')
        for key in ('box_yaw', 'mailer_yaw'):
            if not math.isfinite(layout.get(key, 0.)):
                raise ValueError('Invalid parcel orientation')
        groups[group].append(layout)
    if not groups:
        raise ValueError('Empty layout set')
    for group, rows in groups.items():
        if len(rows) != 2 or {x.get('assignment') for x in rows} != {'normal', 'swapped'}:
            raise ValueError(f'{group}: incomplete category swap')
        a, b = rows
        if a['seed'] != b['seed'] or a['planned_split'] != b['planned_split']:
            raise ValueError('Swap seed/split mismatch')
        # Keep the two physical slot XY/yaws, exchange object categories. Z is
        # category-specific height; category-locked yaw is a different design.
        for first, second in (('box', 'mailer'), ('mailer', 'box')):
            if a[first+'_xyz'][:2] != b[second+'_xyz'][:2]:
                raise ValueError('Category swap changes slot XY')
            delta = a.get(first+'_yaw', 0.) - b.get(second+'_yaw', 0.)
            if abs(math.atan2(math.sin(delta), math.cos(delta))) > 1e-9:
                raise ValueError('Category swap changes slot yaw')
    return {key: sorted(x['layout_id'] for x in rows) for key, rows in groups.items()}
