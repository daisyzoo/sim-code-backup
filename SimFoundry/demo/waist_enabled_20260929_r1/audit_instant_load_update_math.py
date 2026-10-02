"""Independent uninstalled final-load guard pressure mathematics.
No candidate/controller imports. The old peak guard remains an explicit inner
result; the actual final bias must also satisfy the new final-sample condition.
Source admission, complete file coverage, outer resets and actions are separate.
"""
import math

def verify_event(event,*,action_step,previous_action_loads):
    def near(a,b):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<1e-12,(a,b)
    def exact(actual,expected):
        if type(expected) is dict:
            assert type(actual) is dict and set(actual)==set(expected)
            for k,v in expected.items():exact(actual[k],v)
        elif type(expected) is float:near(actual,expected)
        else:assert type(actual) is type(expected) and actual==expected,(actual,expected)
    assert type(action_step) is int and action_step>=1 and event['action_step']==action_step
    values=tuple(float(x) for x in previous_action_loads);assert len(values)==24 and all(math.isfinite(x) and x>=0 for x in values)
    obs=event['preceding_observation'];before=event['before'];after=event['after'];r=event['returned'];active=event['active']
    assert type(active) is bool and active==(event['phase_at_update'] in ('top_press','top_push'))
    assert obs['action_step']==action_step and obs['observed_after_action_step']==action_step-1 and obs['observed_solver_substeps']==24
    assert before['desired_n']==5. and before['min_bias_m']==-.006 and -.006<=before['bias_m']<=.025 and math.isfinite(before['filtered_n'])
    near(obs['previous_action_peak_n'],max(values));near(obs['final_load_n'],values[-1])
    measured=event['observed_vertical_load_n'];assert math.isfinite(measured) and measured>=0 and abs(measured-values[-1])<1e-5
    filtered=.25*measured+.75*before['filtered_n'];original=before['bias_m']
    if active:original=max(-.006,min(.025,original+max(-.0005,min(.003,.0008*(filtered-5.)))))
    peak_held=bool(active and max(values)>10. and original<before['bias_m'])
    peak_bias=before['bias_m'] if peak_held else original
    final_held=bool(active and values[-1]>=5. and original<before['bias_m'])
    final_bias=before['bias_m'] if final_held else peak_bias
    peak=dict(proposed_bias_m=original,guarded_bias_m=peak_bias,held_negative_increment=peak_held,
              previous_action_peak_n=max(values),peak_threshold_n=10.,peak_exceeded=max(values)>10.,
              observed_after_action_step=action_step-1,observed_solver_substeps=24,action_step=action_step,
              original_bias_domain_preserved=True,training_ready=False)
    final=dict(guarded_bias_m=final_bias,held_negative_increment=bool(final_held or peak_held),
               held_by_final_sample=final_held,held_by_peak=peak_held,final_sample_meets_target=values[-1]>=5.,
               previous_action_final_n=values[-1],original_peak_guard=peak,
               original_filter_and_upward_response_unchanged=True,training_ready=False)
    exact(r['peak_bias_guard'],peak);exact(r['instantaneous_load_guard'],final)
    near(after['filtered_n'],filtered);near(after['bias_m'],final_bias)
    near(r['observed_vertical_load_n'],measured);near(r['filtered_vertical_load_n'],filtered)
    near(r['stored_z_bias_m'],final_bias);near(r['applied_z_bias_m'],final_bias if active else 0.)
    return dict(passed=True,action_step=action_step,held_by_peak=peak_held,held_by_final_sample=final_held,
                additional_final_hold=bool(final_held and not peak_held),original_bias_m=original,
                peak_guarded_bias_m=peak_bias,actual_final_bias_m=final_bias,training_ready=False)
