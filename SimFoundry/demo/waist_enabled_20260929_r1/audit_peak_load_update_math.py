"""Independent pressure-event mathematics; no controller/candidate imports.
Caller must bind event provenance and supply loads from independently audited
substep files. Phase/reset and executed-action audits remain separately required.
"""
import math


def verify_event(event, *, action_step, previous_action_loads):
    def near(a, b):
        assert math.isfinite(a) and math.isfinite(b) and abs(a-b) < 1e-12, (a, b)
    assert type(action_step) is int and action_step >= 1
    assert event['action_step'] == action_step
    values = tuple(float(x) for x in previous_action_loads)
    assert len(values) == 24 and all(math.isfinite(x) and x >= 0 for x in values)
    obs = event['preceding_observation']; before = event['before']; after = event['after']
    result = event['returned']; guard = result['peak_bias_guard']
    active = event['active']
    assert type(active) is bool and active == (event['phase_at_update'] in ('top_press','top_push'))
    assert obs['action_step'] == action_step and obs['observed_after_action_step'] == action_step-1
    assert obs['observed_solver_substeps'] == 24
    assert before['desired_n'] == 5. and before['min_bias_m'] == -.006
    assert -.006 <= before['bias_m'] <= .025 and math.isfinite(before['filtered_n'])
    near(obs['previous_action_peak_n'], max(values));near(obs['final_load_n'], values[-1])
    actual_load = event['observed_vertical_load_n']
    assert math.isfinite(actual_load) and actual_load >= 0 and abs(actual_load-values[-1]) < 1e-5
    filtered = .25*actual_load + .75*before['filtered_n']
    original_bias = before['bias_m']
    if active:
        original_bias = max(-.006, min(.025, original_bias + max(-.0005, min(.003, .0008*(filtered-5.)))))
    held = bool(active and max(values) > 10. and original_bias < before['bias_m'])
    candidate = before['bias_m'] if held else original_bias
    near(after['bias_m'], candidate);near(after['filtered_n'], filtered)
    near(result['observed_vertical_load_n'], actual_load)
    near(result['filtered_vertical_load_n'], filtered)
    near(result['stored_z_bias_m'], candidate)
    near(result['applied_z_bias_m'], candidate if active else 0.)
    expected = dict(proposed_bias_m=original_bias, guarded_bias_m=candidate,
                    held_negative_increment=held, previous_action_peak_n=max(values),
                    peak_threshold_n=10., peak_exceeded=max(values)>10.,
                    observed_after_action_step=action_step-1, observed_solver_substeps=24,
                    action_step=action_step, original_bias_domain_preserved=True, training_ready=False)
    assert set(guard) == set(expected)
    for key,value in expected.items():
        if type(value) is float:near(guard[key], value)
        else:assert type(guard[key]) is type(value) and guard[key] == value, key
    return dict(passed=True, action_step=action_step, held_negative_increment=held,
                original_bias_m=original_bias, guarded_bias_m=candidate, training_ready=False)
