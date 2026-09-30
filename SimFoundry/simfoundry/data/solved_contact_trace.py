"""Diagnostic observer: solved last-tick contacts, without refreshing physics."""

def read_solved_contact_forces(action_step, *, include_hand_contacts=False, include_arm_contacts=False):
    import numpy as np
    import warp as wp
    from mujoco_warp._src.support import contact_force
    from isaaclab_newton.physics.newton_manager import NewtonManager

    solver = NewtonManager._solver
    if solver.use_mujoco_cpu:
        raise RuntimeError('Force observer requires the installed Warp backend')
    data, model = solver.mjw_data, NewtonManager.get_model()
    count = int(data.nacon.numpy()[0])
    if not 0 <= count <= data.naconmax:
        raise RuntimeError('Solved contact buffer overflow')
    mapping = solver.mjc_geom_to_newton_shape.numpy()
    geom = data.contact.geom.numpy()[:count]
    world = data.contact.worldid.numpy()[:count]
    arm_tokens=('left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist')
    def has_arm(names):return any(token in name for name in names for token in arm_tokens)
    selected, labels = [], []
    for i in range(count):
        shapes = [int(mapping[int(world[i]), int(g)]) for g in geom[i]]
        names = [model.shape_label[s] if s >= 0 else 'unmapped' for s in shapes]
        if any('/parcel_box/' in n or '/mailer/' in n for n in names) or (include_hand_contacts and any('_wrist_roll_rubber_hand' in n for n in names)) or (include_arm_contacts and has_arm(names)):
            if min(shapes) < 0:
                raise RuntimeError('Unmapped parcel contact')
            selected.append(i)
            labels.append(names)
    rows = []
    if selected:
        ids = wp.array(selected, dtype=wp.int32, device=data.contact.pos.device)
        local = wp.zeros(len(selected), dtype=wp.spatial_vector, device=ids.device)
        # Only output arrays are written by the installed support kernel.
        before = data.efc.force.numpy().copy()
        contact_force(solver.mjw_model, data, ids, False, local)
        forces = local.numpy()
        after = data.efc.force.numpy()
        if not np.array_equal(before, after, equal_nan=True):
            raise RuntimeError('Observer changed solver force buffer')
        if not np.isfinite(forces).all():
            raise RuntimeError('Nonfinite solved contact force')
        frames = data.contact.frame.numpy()
        positions = data.contact.pos.numpy()
        distances = data.contact.dist.numpy()
        friction = data.contact.friction.numpy()
        addresses = data.contact.efc_address.numpy()
        for j, i in enumerate(selected):
            # Installed kernel uses force[:3] @ contact.frame for world force.
            rows.append(dict(contact_id=i, shapes=labels[j], world_id=int(world[i]),
                             position_world=positions[i].tolist(),
                             contact_frame=frames[i].tolist(), distance_m=float(distances[i]),
                             friction=friction[i].tolist(), efc_address=addresses[i].tolist(),
                             force_torque_contact=forces[j].tolist(),
                             force_world_N=(forces[j, :3] @ frames[i]).tolist()))
    return dict(after_action_step=action_step, solved_contact_count=count,
                parcel_contacts=[r for r in rows if any('/parcel_box/' in n or '/mailer/' in n for n in r['shapes'])],
                hand_contacts=[r for r in rows if include_hand_contacts and any('_wrist_roll_rubber_hand' in n for n in r['shapes'])],
                arm_contacts=[r for r in rows if include_arm_contacts and has_arm(r['shapes'])],
                solver_force_buffer_unchanged=True)
