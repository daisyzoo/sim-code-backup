"""Real front-bag recovery bookkeeping and measured-reference capture only.
Caller still applies command admission and explicitly replaces normal/inactive
anchors. Only a handover from the measured lifecycle can capture a new point.
"""
import numpy as np


def apply(row, state, reference, event, *, object_xyz, object_rotation):
    if event['kind'] == 'unchanged':
        return row, reference
    if event['kind'] not in ('command', 'handover'):
        raise ValueError('Cannot apply rejected initial landing')
    counter = event['context']['recontacts']
    if type(counter) is not int or counter < 1 or type(state.recontacts) is not int or state.recontacts != counter:
        raise ValueError('Recovery capture must match the real parent counter')
    if row.get('route_stop_reason') or row.get('release_reason'):
        raise ValueError('Parent guard has precedence over initial landing')
    if event['kind'] == 'handover':
        if event['measured_ready_count'] < 3:
            raise ValueError('Handover lacks three consecutive measured ready frames')
        new_reference = {k: np.array(v, dtype=float) for k, v in event['reference'].items()}
        tip = np.asarray(event['observed_support_xyz'], dtype=float)
        xy = np.asarray(event['selected_surface_local_xy'], dtype=float)
        if tip.shape != (3,) or xy.shape != (2,) or not np.isfinite(np.r_[tip,xy]).all():
            raise ValueError('Invalid measured contact reference')
        if max(abs(xy)) > .0020002 or np.min(np.asarray(state.size[:2])/2-abs(xy)) < .01:
            raise ValueError('Initial contact is not centered inside original inset')
        surface = np.asarray(object_xyz)+np.asarray(object_rotation)@np.r_[xy,state.size[2]/2]
    # Validate the full transition before modifying parent state.
    state.command = None
    state.settled = state.lost_contact_steps = 0
    state.load.bias_m = 0.
    state.approach_xy_bias = [0., 0.]
    state.push_x_anchor = None
    state.relative_contact_anchor = None
    state.cross_axis_control.reset()
    if hasattr(state, 'cop_slip'):
        state.cop_slip.reset()
        state.last_emitted_xy = None
    load = dict(row['contact_load'], applied_z_bias_m=0., stored_z_bias_m=0.)
    if event['kind'] == 'command':
        state.top_mode = state.mode = 'top_cross'
        state.mode_step = 0
        state.descent_z = None
        return dict(row, mode='top_cross', contact_load=load, front_recontact_center_phase='tracking'), reference
    state.selected_surface_local_xy = tuple(xy)
    state.top_mode = state.mode = 'top_press'
    state.mode_step = 1
    state.start = tuple(tip)
    state.descent_z = float(tip[2])
    # Start COP command history at the measured landing, not the last virtual cross goal.
    if hasattr(state, 'last_emitted_xy'):
        state.last_emitted_xy = tuple(tip[:2])
    return dict(row, mode='top_press', target_xyz=tip.tolist(), observed_support_xyz=tip.tolist(),
                control_offset_local=new_reference['reference_local'].tolist(), parcel_top_xyz=surface.tolist(),
                push_x_anchor_m=None, approach_xy_bias_m=[0.,0.], contact_load=load,
                front_recontact_center_phase='measured_handover'), new_reference
