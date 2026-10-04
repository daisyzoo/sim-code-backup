"""Uninstalled causal evidence for a loss counter; never replace current force/COP.
Uses the original hand-target absolute vertical force observable. The original
0.2N loss threshold remains; a majority of24 completed solver ticks is additional
intermittent-contact evidence, not continuous contact or permission to push.
"""
import math
VERSION='previous24_majority_contact_evidence_v1'
LOSS_THRESHOLD_N=.2

def summarize(*,action_step,after_action_step,vertical_load_n,instantaneous_load_n):
    if type(action_step) is not int or action_step<=0 or type(after_action_step) is not int or after_action_step!=action_step-1:
        raise ValueError('Only immediately preceding completed action accepted')
    if type(instantaneous_load_n) not in (int,float) or not math.isfinite(instantaneous_load_n) or instantaneous_load_n<0:
        raise ValueError('Finite nonnegative original observation required')
    values=tuple(float(x) for x in vertical_load_n)
    if len(values)!=24 or any(not math.isfinite(x) or x<0 for x in values):
        raise ValueError('Complete24 finite nonnegative solver ticks required')
    if abs(values[-1]-instantaneous_load_n)>1e-5:
        raise ValueError('Original instantaneous observation must match final solved tick')
    count=sum(x>=LOSS_THRESHOLD_N for x in values)
    return dict(version=VERSION,action_step=action_step,after_action_step=after_action_step,solver_substeps=24,
                instantaneous_load_n=instantaneous_load_n,mean_abs_vertical_load_n=sum(values)/24,
                peak_abs_vertical_load_n=max(values),ticks_at_or_above_loss_threshold=count,
                majority_contact_evidence=count>=12,entire_interval_below_threshold=count==0,
                original_loss_threshold_n=LOSS_THRESHOLD_N,training_ready=False)

def loss_counter_observation(*,enabled=False,selected_front=False,mode,action_step,after_action_step,vertical_load_n,instantaneous_load_n):
    if type(enabled) is not bool or type(selected_front) is not bool:
        raise ValueError('Explicit boolean opt-in/selection required')
    observation=summarize(action_step=action_step,after_action_step=after_action_step,vertical_load_n=vertical_load_n,instantaneous_load_n=instantaneous_load_n)
    original=instantaneous_load_n>=LOSS_THRESHOLD_N
    applicable=enabled and selected_front and mode=='top_push'
    additional=bool(applicable and not original and observation['majority_contact_evidence'])
    return dict(observation=observation,original_contact_evidence=original,
                contact_evidence_for_loss_counter=bool(original or additional),
                additional_intermittent_evidence=additional,enabled=enabled,selected_front=selected_front,
                mode=mode,current_force_preserved=True,current_cop_available_from_window=False,
                phase_or_command_modified=False,training_ready=False)
