"""Pure read-only extraction from one independently recorded substep interval.
No physics buffers, device operations, or controller state writes.
"""
import numpy as np


def extract(packed, metadata, *, after_action_step, side, target_name):
    if (side, target_name) not in [('left', 'mailer'), ('right', 'parcel_box')]:
        raise ValueError('Original hand/target pairing required')
    managers = metadata['expected_manager_steps']
    if metadata['expected_substeps'] != 24 or managers not in (1, 8):
        raise ValueError('Original 24-substep schedule required')
    if type(after_action_step) is not int or after_action_step < 0:
        raise ValueError('Explicit completed action identity required')
    size = 24 + managers
    steps = np.asarray(packed['action_step'])
    ticks = np.asarray(packed['substep_tick'])
    kinds = np.asarray(packed['kind'])
    offsets = np.asarray(packed['contact_offsets'])
    shapes = np.asarray(packed['shape_ids'])
    force = np.asarray(packed['force_torque_world'])
    expected_ticks = np.concatenate([np.arange(i*24//managers, (i+1)*24//managers+1)
                                     for i in range(managers)])
    expected_kinds = np.tile([0]*(24//managers)+[1], managers)
    if (steps.shape != (size,) or not np.all(steps == after_action_step)
            or not np.array_equal(ticks, expected_ticks)
            or not np.array_equal(kinds, expected_kinds)):
        raise ValueError('Incomplete, reordered or stale substep interval')
    if (offsets.shape != (size+1,) or not np.issubdtype(offsets.dtype, np.integer)
            or offsets[0] != 0 or np.any(np.diff(offsets) < 0)
            or force.shape != (offsets[-1], 6) or not np.isfinite(force).all()
            or shapes.shape != (len(force), 2)
            or not np.issubdtype(shapes.dtype, np.integer)):
        raise ValueError('Malformed packed contacts')
    labels = metadata['shape_labels']
    if np.any(shapes < 0) or np.any(shapes >= len(labels)):
        raise ValueError('Unknown shape identity')
    hand = np.asarray([f'{side}_wrist_roll' in name for name in labels])
    target = np.asarray([f'/{target_name}/' in name for name in labels])
    pair = np.any(hand[shapes], axis=1) & np.any(target[shapes], axis=1)
    summed = np.zeros(size, dtype=float)
    sample_ids = np.repeat(np.arange(size), np.diff(offsets))
    np.add.at(summed, sample_ids[pair], abs(force[pair, 2]).astype(float))
    selected = [int(np.flatnonzero(ticks == tick)[0]) for tick in range(1, 25)]
    # The final tick and each unique solved boundary use the same selection as
    # the independent file diagnosis, excluding tick0 and boundary duplicates.
    values = summed[selected].tolist()
    return dict(after_action_step=after_action_step, vertical_load_n=values,
                peak_vertical_load_n=max(values), final_vertical_load_n=values[-1],
                selected_sample_indices=selected, solver_substeps=24)
