"""Uninstalled adapter: final-sample downward hold over the existing peak guard.
The original pressure filter, upward response, observe-once contract, and outer
controller ownership of phases, resets, geometry and action guards are retained.
"""
from peak_load_control_adapter import PeakLoadControl
from instant_load_bias_guard import guard_instantaneous_load

class InstantLoadControl(PeakLoadControl):
    def update(self,load_n,active):
        obs=self._observation
        old=self.bias_m
        result=super().update(load_n,active)
        original=result['peak_bias_guard']
        guard=guard_instantaneous_load(desired_n=self.desired_n,previous_bias_m=old,
            proposed_bias_m=original['proposed_bias_m'],previous_action_peak_n=obs['previous_action_peak_n'],
            previous_action_final_n=obs['final_load_n'],active=active,action_step=obs['action_step'],
            observed_after_action_step=obs['observed_after_action_step'],
            observed_solver_substeps=obs['observed_solver_substeps'],min_bias_m=self.min_bias_m)
        self.bias_m=guard['guarded_bias_m']
        return dict(result,applied_z_bias_m=self.bias_m if active else 0.,stored_z_bias_m=self.bias_m,
                    instantaneous_load_guard=guard)
