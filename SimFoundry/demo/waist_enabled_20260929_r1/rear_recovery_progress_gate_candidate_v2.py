"""Default-off recovery progress gate, isolated from the actual collector.
If tracking compensation is valid, require its own requested72% X correction
without increasing nominal Z above the already verified parent command.
If no such loaded command is verified, explicitly request original unload.
No physical progress or force is synthesized; actual recontact remains required.
"""
import copy
import numpy as np
from rear_recovery_tracking_solver_v2 import solve as parent_solve
from rear_recovery_progress_gate_solver import solve as constrained_solve


def solve(*, progress_gate=False, **inputs):
    if type(progress_gate) is not bool:
        raise ValueError('Explicit progress gate option required')
    command,parent=parent_solve(**inputs)
    if not progress_gate:
        return command,parent
    tracking=parent.get('tracking_feedback',{})
    if command is None or not parent.get('applied') or tracking.get('accepted') is not True:
        return command,parent
    parent_command=np.asarray(command,float)
    delta=np.asarray(parent['reference_delta_xyz_m'],float)
    bias=np.asarray(tracking['correction_xyz_m'],float)
    required=.72*parent['requested_x_m']
    gate=dict(enabled=True,minimum_predicted_x_m=required,
              parent_predicted_x_m=float(delta[0]+bias[0]),
              nominal_z_ceiling_m=float(delta[2]),
              parent_command=parent_command.tolist(),parent_result=copy.deepcopy(parent),
              preserve_original_requested_gain=True,
              physical_progress_proven=False)
    if delta[0]+bias[0]>=required-1e-7:
        gate.update(selection='original_sufficient_predicted_progress',new_loaded_solve=False)
        return command,dict(parent,progress_gate=gate)
    candidate,result=constrained_solve(**inputs,diagnostic_z_ceiling_m=float(delta[2]))
    gate.update(selection='new_loaded_command' if candidate is not None else 'request_original_guarded_unload',new_loaded_solve=True)
    if candidate is not None:
        assert result['applied'] and result['tracking_feedback']['accepted']
        movement=np.asarray(result['reference_delta_xyz_m'])
        assert movement[0]+bias[0]>=required-1e-7 and movement[2]<=delta[2]+1e-7
    else:
        assert result['requires_recontact'] and result['reason']=='no_verified_loaded_recovery'
    return candidate,dict(result,progress_gate=gate)
