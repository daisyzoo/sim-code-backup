"""Unwired default-off recovery-center tracking command; real positive recovery counter.
No state writes, fallback commands, normal-anchor resets, or loaded control.
Returns no command when disabled/ineligible or when verification rejects it.
Caller must retain original guard priority and handle any abort explicitly.
"""
import numpy as np

def propose(*,enabled,selected,mode,recontacts,observed_load_n,filtered_load_n,
            current,previous_q,previous_command,waypoint,decay,guard,scene_check):
    if type(enabled) is not bool or type(selected) is not bool:
        raise ValueError('Expected explicit boolean switches')
    if not enabled:return None,dict(applied=False,reason='disabled')
    if not selected or mode!='top_cross' or type(recontacts) is not int or recontacts<1:
        return None,dict(applied=False,reason='outside_selected_recovery_front_landing')
    if not np.isfinite(observed_load_n) or not np.isfinite(filtered_load_n):
        raise ValueError('Nonfinite contact load')
    if observed_load_n!=0. or not 0.<=filtered_load_n<=.05:
        return None,dict(applied=False,reason='not_measured_unloaded')
    q,qp,previous,target,a=[np.asarray(x,dtype=float) for x in
                           [current,previous_q,previous_command,waypoint,decay]]
    if any(x.shape!=(11,) or not np.isfinite(x).all() for x in [q,qp,previous,target,a]):
        raise ValueError('Expected finite upper11 arrays')
    if np.any(a<0.) or np.any(a>.95):raise ValueError('Invalid response decay')
    if np.any(target<guard.lower-2e-7) or np.any(target>guard.upper+2e-7):
        return None,dict(applied=False,reason='waypoint_outside_original_command_bounds')
    measured=scene_check(q)
    if measured.get('accepted') is not True:
        return None,dict(applied=False,reason='measured_scene_rejected',measured_scene=measured)
    bias=(q-previous)-a*(qp-previous)
    requested=(target-a*q-bias)/(1-a)
    low=np.maximum.reduce([guard.lower,q-guard.limits,previous-.055])
    high=np.minimum.reduce([guard.upper,q+guard.limits,previous+.055])
    if np.any(low>high):return None,dict(applied=False,reason='empty_original_bounds')
    command=np.clip(requested,low,high).astype(np.float32)
    predicted=(1-a)*command+a*q+bias
    checked=guard.command(command,q,previous)
    nominal=scene_check(command);predicted_scene=scene_check(predicted)
    # Require reserve in proposed nominal/predicted states. Measured physical
    # eligibility above still uses the unchanged original scene guard.
    reserve=bool(nominal['inactive_lowest_z_m'] >= .8405
                 and predicted_scene['inactive_lowest_z_m'] >= .8405)
    accepted=bool(checked['accepted'] and nominal.get('accepted') is True
                  and predicted_scene.get('accepted') is True and reserve)
    record=dict(applied=accepted,reason='verified_unloaded_command' if accepted else 'command_or_predicted_scene_rejected',current=q.tolist(),previous_q=qp.tolist(),previous_command=previous.tolist(),waypoint=target.tolist(),decay=a.tolist(),causal_bias=bias.tolist(),requested_command=requested.tolist(),candidate_command=command.tolist(),predicted_q=predicted.tolist(),command_check=checked,nominal_scene=nominal,predicted_scene=predicted_scene,scope='Causal local response hypothesis and sampled selected geometry only; not physical validation or training admission.')
    return (command if accepted else None),record
