"""Uninstalled one-step guard: do not integrate down against a met final load.
Builds on the existing peak guard without changing its threshold, original
filter, upward increments, phases, resets, slew, IK, or physical state. This
pure function is a hypothesis only; no actual future contact is predicted.
"""
import math
from peak_load_bias_guard import guard_bias_step

def guard_instantaneous_load(*,previous_action_final_n,**kwargs):
    if not math.isfinite(previous_action_final_n) or previous_action_final_n<0:
        raise ValueError('Finite nonnegative preceding final load required')
    peak=kwargs['previous_action_peak_n']
    if not math.isfinite(peak) or previous_action_final_n>peak+1e-12:
        raise ValueError('Final load cannot exceed the same observation peak')
    parent=guard_bias_step(**kwargs)
    prior=kwargs['previous_bias_m'];proposed=kwargs['proposed_bias_m']
    met=previous_action_final_n>=kwargs['desired_n']
    final_hold=bool(kwargs['active'] and met and proposed<prior)
    result=prior if final_hold else parent['guarded_bias_m']
    return dict(guarded_bias_m=result,held_negative_increment=bool(final_hold or parent['held_negative_increment']),
                held_by_final_sample=final_hold,held_by_peak=parent['held_negative_increment'],
                final_sample_meets_target=met,previous_action_final_n=previous_action_final_n,
                original_peak_guard=parent,original_filter_and_upward_response_unchanged=True,
                training_ready=False)
