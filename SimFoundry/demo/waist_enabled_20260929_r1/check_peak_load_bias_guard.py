"""Causal-observation and original-boundary checks of the uninstalled guard."""
from pathlib import Path
import datetime
import hashlib
import json
from peak_load_bias_guard import guard_bias_step

base = dict(desired_n=5., previous_bias_m=0., proposed_bias_m=-.0005,
            previous_action_peak_n=17., active=True, action_step=9,
            observed_after_action_step=8, observed_solver_substeps=24)
checks = []

def check(name, updates, expected=None, reject=False):
    try:
        result = guard_bias_step(**(base | updates))
    except ValueError:
        assert reject, name
    else:
        assert not reject, name
        assert result['guarded_bias_m'] == expected, (name, result)
    checks.append(name)

check('high_prior_peak_holds_negative_increment', {}, 0.)
check('upward_relief_preserved', {'proposed_bias_m': .003}, .003)
check('threshold_equality_does_not_trigger', {'previous_action_peak_n': 10.}, -.0005)
check('below_threshold_preserves_original', {'previous_action_peak_n': 9.8}, -.0005)
check('inactive_preserves_proposal', {'active': False}, -.0005)
check('lower_saturation_stays_at_original_bound', {'previous_bias_m': -.006, 'proposed_bias_m': -.006}, -.006)
check('upper_saturation_stays_at_original_bound', {'previous_bias_m': .025, 'proposed_bias_m': .025}, .025)
check('no_peak_preserves_original', {'previous_action_peak_n': 0.}, -.0005)
for name, update in [
    ('stale_observation_rejected', {'observed_after_action_step': 7}),
    ('current_action_future_information_rejected', {'observed_after_action_step': 9}),
    ('incomplete_substeps_rejected', {'observed_solver_substeps': 23}),
    ('nan_peak_rejected', {'previous_action_peak_n': float('nan')}),
    ('infinite_peak_rejected', {'previous_action_peak_n': float('inf')}),
    ('negative_peak_rejected', {'previous_action_peak_n': -1.}),
    ('increased_load_target_rejected', {'desired_n': 5.1}),
    ('changed_lower_bound_rejected', {'min_bias_m': -.01}),
    ('changed_upper_bound_rejected', {'max_bias_m': .03}),
    ('oversized_downward_step_rejected', {'proposed_bias_m': -.001}),
    ('oversized_upward_step_rejected', {'proposed_bias_m': .004}),
    ('out_of_bounds_state_rejected', {'previous_bias_m': -.007}),
    ('invalid_first_action_observation_rejected', {'action_step': 0, 'observed_after_action_step': -1}),
]:
    check(name, update, reject=True)

root = Path(__file__).resolve().parent
report = dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              passed=True, checks=checks, controller_installed=False,
              physical_validation=False, training_ready=False,
              source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [Path(__file__), root/'peak_load_bias_guard.py']})
dest = root/'PEAK_LOAD_BIAS_GUARD_BOUNDARY_CHECK.json'
assert not dest.exists()
dest.write_text(json.dumps(report, indent=2))
print(json.dumps(dict(passed=True, checks=len(checks), physical_validation=False)))
