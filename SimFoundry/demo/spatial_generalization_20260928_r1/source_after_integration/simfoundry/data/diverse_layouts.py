"""Explicit diagnostic layouts. Admission to training requires separate review."""
import json, math
from pathlib import Path
from simfoundry.calibration.sorting_station import TABLE_TOP_BOX_Z, TABLE_TOP_MAILER_Z, PARCEL_BOX_SIZE, MAILER_SIZE_XYH, TABLE_FRONT_X

def load_diagnostic_layout(path, layout_id):
    return validate_diagnostic_layout(json.loads(Path(path).read_text()), layout_id)

def validate_diagnostic_layout(d, layout_id):
    if d.get('layout_id') != layout_id or type(d.get('seed')) is not int:
        raise ValueError('Explicit layout id/seed mismatch')
    for key,z in [('box_xyz',TABLE_TOP_BOX_Z),('mailer_xyz',TABLE_TOP_MAILER_Z)]:
        xyz=d.get(key)
        if not isinstance(xyz,list) or len(xyz)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in xyz):
            raise ValueError('Invalid parcel coordinates')
        if not .36<=xyz[0]<=.62 or not -.18<=xyz[1]<=.18 or abs(xyz[2]-z)>1e-6:
            raise ValueError('Parcel outside diagnostic bounds or wrong height')
    half_extents = []
    for key, size in [('box', PARCEL_BOX_SIZE), ('mailer', MAILER_SIZE_XYH)]:
        yaw = d.get(key + '_yaw', 0.)
        if not isinstance(yaw, (int, float)) or not math.isfinite(yaw) or abs(yaw) > math.pi:
            raise ValueError('Invalid parcel yaw')
        c, s = abs(math.cos(yaw)), abs(math.sin(yaw))
        hx, hy = (size[0]*c + size[1]*s)/2, (size[0]*s + size[1]*c)/2
        if d[key + '_xyz'][0] - hx < TABLE_FRONT_X:
            raise ValueError('Initial parcel footprint overhangs table')
        half_extents.append((hx, hy))
    a,b=d['box_xyz'],d['mailer_xyz']
    if abs(a[0]-b[0]) < sum(h[0] for h in half_extents)+.02 and abs(a[1]-b[1]) < sum(h[1] for h in half_extents)+.02:
        raise ValueError('Insufficient initial footprint clearance')
    if not isinstance(d.get('geometry_group'),str) or d.get('assignment') not in ('normal','swapped'):
        raise ValueError('Missing grouped split metadata')
    return d


def validate_geometry_split(records, validation_layouts):
    """Reject category-swap leakage or partial spatial strata before conversion."""
    groups = {}
    for record in records:
        group = record.get('geometry_group')
        if group is not None:
            if not isinstance(group, str) or not group:
                raise ValueError('Invalid geometry group')
            groups.setdefault(group, []).append(record)
    tasks = {'push_box_to_bin', 'nudge_mailer_to_bin'}
    for group, rows in groups.items():
        if len(rows) != 4 or {r.get('assignment') for r in rows} != {'normal','swapped'}:
            raise ValueError(f'{group}: need both category assignments and both task demonstrations')
        for assignment in ('normal','swapped'):
            subset = [r for r in rows if r['assignment'] == assignment]
            if len(subset) != 2 or {r['task_id'] for r in subset} != tasks or len({r['layout_id'] for r in subset}) != 1:
                raise ValueError(f'{group}: incomplete or inconsistent assignment')
        if len({r['layout_id'] for r in rows}) != 2:
            raise ValueError(f'{group}: assignments must have distinct layout IDs')
        if len({r['layout_id'] in validation_layouts for r in rows}) != 1:
            raise ValueError(f'{group}: category swaps leaked across train/validation')
    return sorted(groups)


def contact_offset_for_distance(parcel_x, near_offset, far_offset=0.):
    """Opt-in geometric expert: preserve near path, shorten far approach.

    The threshold .48m separates the tested .36/.51m front/back slots.
    Category and push direction do not enter this rule; it is not a claim
    of validated behavior for every intermediate or arbitrary placement.
    """
    return far_offset if far_offset and parcel_x >= .48 else near_offset
