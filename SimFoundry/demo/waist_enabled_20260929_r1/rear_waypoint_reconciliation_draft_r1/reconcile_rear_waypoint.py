"""Unwired default-off post-commit Cartesian cursor reconciliation.
Only the future rear-box Y cursor may change, after an accepted actual edge
refinement. Current emitted action, X/Z, pressure and original guards stay with
the caller. FK point is nominal committed reference, not predicted physical COP.
A live adapter must bind the final action/FK/current offset and trace this state
transition explicitly; this helper alone is not a source or safety certificate.
"""
import numpy as np
VERSION='rear_box_post_commit_y_reconciliation_draft_v1'
def reconcile(*,enabled=False,side,mode,rear_selected,edge_selected,edge_override,
              command_accepted,requested_xyz,committed_reference_xyz,normal_load_n):
 for name,value in [('enabled',enabled),('rear_selected',rear_selected),('edge_selected',edge_selected),('edge_override',edge_override),('command_accepted',command_accepted)]:
  if type(value) is not bool:raise ValueError(name+' must be bool')
 no=lambda why:dict(override=False,reason=why,version=VERSION)
 if not enabled:return no('disabled')
 if side not in ['left','right']:raise ValueError('Invalid side')
 if side!='right' or not rear_selected:return no('not_rear_box')
 if mode!='top_push':return no('original_mode_guard')
 if not edge_selected or not edge_override:return no('no_applied_edge_refinement')
 if not command_accepted:return no('command_not_accepted')
 if not np.isfinite(normal_load_n) or normal_load_n<0:raise ValueError('Invalid measured load')
 if normal_load_n<.3:return no('no_valid_loaded_contact')
 requested,committed=(np.asarray(x,dtype=float) for x in [requested_xyz,committed_reference_xyz])
 if requested.shape!=(3,) or committed.shape!=(3,) or not np.isfinite(requested).all() or not np.isfinite(committed).all():raise ValueError('Invalid finite reference3D')
 # Right box has task direction -Y. Remove only forward unexecuted nominal
 # cursor advance; never add forward advance or a fixed lead/material cap.
 unrealized=float(committed[1]-requested[1])
 if unrealized<=0:return no('no_unrealized_forward_cursor')
 after=requested.copy();after[1]=committed[1]
 return dict(override=True,reason='reconcile_future_cursor_to_nominal_committed_reference',version=VERSION,requested_before_xyz=requested.tolist(),nominal_committed_reference_xyz=committed.tolist(),next_state_command_xyz=after.tolist(),next_state_last_waypoint_xy=after[:2].tolist(),removed_unrealized_forward_y_m=unrealized,current_action_changed=False,physical_motion_prediction=False)
