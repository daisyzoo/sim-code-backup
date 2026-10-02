"""Uninstalled one-step pressure-bias guard; no state/control/physics imports.
Proposes holding a negative integrator increment after a prior-action peak above
2x desired load. Upward increments and all original mode guards remain external.
"""
import math

def guard_bias_step(*,desired_n,previous_bias_m,proposed_bias_m,previous_action_peak_n,active,action_step,observed_after_action_step,observed_solver_substeps,min_bias_m=-.006,max_bias_m=.025):
 if type(active) is not bool or type(action_step) is not int or action_step<1 or type(observed_after_action_step) is not int or observed_after_action_step!=action_step-1 or type(observed_solver_substeps) is not int or observed_solver_substeps!=24:
  raise ValueError('Previous complete24-substep observation required')
 numbers=[desired_n,previous_bias_m,proposed_bias_m,previous_action_peak_n,min_bias_m,max_bias_m]
 if not all(math.isfinite(x) for x in numbers) or not .5<=desired_n<=5 or previous_action_peak_n<0 or min_bias_m!=-.006 or max_bias_m!=.025:
  raise ValueError('Invalid original top-pressure domain')
 if not min_bias_m<=previous_bias_m<=max_bias_m or not min_bias_m<=proposed_bias_m<=max_bias_m:
  raise ValueError('Original bias bounds required')
 delta=proposed_bias_m-previous_bias_m
 if active and not -.000500000001<=delta<=.003000000001:
  raise ValueError('Parent integrator step outside original bounds')
 high=previous_action_peak_n>2*desired_n
 held=bool(active and high and delta<0)
 result=previous_bias_m if held else proposed_bias_m
 return dict(proposed_bias_m=proposed_bias_m,guarded_bias_m=result,held_negative_increment=held,previous_action_peak_n=previous_action_peak_n,peak_threshold_n=2*desired_n,peak_exceeded=high,observed_after_action_step=observed_after_action_step,observed_solver_substeps=24,action_step=action_step,original_bias_domain_preserved=True,training_ready=False)
