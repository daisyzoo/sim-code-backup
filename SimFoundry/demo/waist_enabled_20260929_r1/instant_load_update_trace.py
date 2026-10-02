"""Prospective pressure-boundary trace; uninstalled, no physics access.
Owner binding records the actual phase when the original pressure update runs.
This trace does not replace original phase/reset or executed-action audits.
"""
import copy
from instant_load_control_adapter import InstantLoadControl


class TracedInstantLoadControl(InstantLoadControl):
    def bind_owner(self, owner):
        if hasattr(self, '_owner') or owner.load is not self:
            raise ValueError('Bind once to the actual enclosing pressure owner')
        self._owner = owner
        self.updates = []

    def update(self, load_n, active):
        if not hasattr(self, '_owner') or self._owner.load is not self:
            raise ValueError('Actual pressure owner required')
        if active != (self._owner.top_mode in ('top_press', 'top_push')):
            raise ValueError('Pressure activation differs from current top phase')
        observation = copy.deepcopy(self._observation)
        before = dict(desired_n=self.desired_n, min_bias_m=self.min_bias_m,
                      bias_m=self.bias_m, filtered_n=self.filtered_n)
        result = super().update(load_n, active)
        self.updates.append(dict(action_step=observation['action_step'],
                                 phase_at_update=self._owner.top_mode, active=active,
                                 observed_vertical_load_n=load_n,
                                 preceding_observation=observation, before=before,
                                 after=dict(bias_m=self.bias_m, filtered_n=self.filtered_n),
                                 returned=copy.deepcopy(result)))
        return result
