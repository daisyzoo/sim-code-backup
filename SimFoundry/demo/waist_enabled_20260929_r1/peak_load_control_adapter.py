"""Uninstalled diagnostic pressure adapter; original filter and relief retained.

An observation must cover the immediately previous action's 24 solved substeps.
Only the downward bias increment can be held. The enclosing controller keeps
ownership of phases, contact recovery, bias resets, waypoints and all guards.
"""
from dataclasses import dataclass, field
import math
from simfoundry.data.contact_load_control import ContactLoadControl
from peak_load_bias_guard import guard_bias_step


@dataclass
class PeakLoadControl(ContactLoadControl):
    _observation: dict | None = field(default=None, init=False, repr=False)
    _last_action_step: int = field(default=0, init=False, repr=False)

    def observe(self, *, action_step, after_action_step, vertical_load_n):
        values = tuple(float(x) for x in vertical_load_n)
        if len(values) != 24 or not all(math.isfinite(x) and x >= 0 for x in values):
            raise ValueError('Complete finite 24-substep loads required')
        if type(action_step) is not int or action_step <= self._last_action_step:
            raise ValueError('Observation must advance the control action')
        guard_bias_step(desired_n=self.desired_n, previous_bias_m=self.bias_m,
                        proposed_bias_m=self.bias_m, previous_action_peak_n=max(values),
                        active=False, action_step=action_step,
                        observed_after_action_step=after_action_step,
                        observed_solver_substeps=len(values), min_bias_m=self.min_bias_m)
        self._observation = dict(action_step=action_step,
                                 observed_after_action_step=after_action_step,
                                 observed_solver_substeps=24, previous_action_peak_n=max(values),
                                 final_load_n=values[-1])
        self._last_action_step = action_step

    def update(self, load_n, active):
        obs = self._observation
        if obs is None:
            raise ValueError('Fresh preceding-action observation required for each update')
        if not math.isfinite(load_n) or abs(load_n - obs['final_load_n']) > 1e-5:
            raise ValueError('Original last-tick feedback does not match observation')
        kwargs = {k: v for k, v in obs.items() if k != 'final_load_n'}
        old = self.bias_m
        # Validate domain before allowing the parent to change either state field.
        guard_bias_step(desired_n=self.desired_n, previous_bias_m=old,
                        proposed_bias_m=old, active=active, min_bias_m=self.min_bias_m,
                        **kwargs)
        result = super().update(load_n, active)
        guard = guard_bias_step(desired_n=self.desired_n, previous_bias_m=old,
                               proposed_bias_m=self.bias_m, active=active,
                               min_bias_m=self.min_bias_m, **kwargs)
        self.bias_m = guard['guarded_bias_m']
        self._observation = None
        return dict(result, applied_z_bias_m=self.bias_m if active else 0.,
                    stored_z_bias_m=self.bias_m, peak_bias_guard=guard)
