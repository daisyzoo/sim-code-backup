"""UNWIRED projection onto original slew/hand-lead and moving material bounds.
Retains3mm per-axis command slew,30mm hand-reference lead,10mm material cap,
original enable/capture/phase/load gating. Removes only the added per-axis
parent-direction segment, which caused measured0.4micrometer early stops.
The output is the nearest feasible command to the parent's current command;
no simulator state, Z target, pressure, prior guard or joint limit is changed.
A truly empty remaining intersection still requires an explicit failed stop.
Geometric feasibility is not proof of contact, motion, force or task success.
"""
import numpy as np
CAP_M=.010
STEP_M=.003
HAND_LEAD_M=.030
MIN_LOAD_N=.3
STRATEGY='nearest_parent_in_slew_hand_material_intersection'

def cap_loaded_reference(*,enabled,capture_complete,mode,parent_xy,previous_xy=None,
                         reference_xy=None,surface_xy=None,normal_load_n=0.):
    if type(enabled) is not bool or type(capture_complete) is not bool:
        raise ValueError('Explicit enable and actual-capture flags required')
    parent=np.asarray(parent_xy,dtype=float)
    if parent.shape!=(2,) or not np.isfinite(parent).all():raise ValueError('Invalid parent command')
    if not np.isfinite(normal_load_n) or normal_load_n<0:raise ValueError('Invalid measured normal load')
    def unchanged(reason):return dict(applied=False,changed=False,requires_recontact=False,reason=reason,command_xy=parent.tolist())
    if not enabled:return unchanged('disabled')
    if not capture_complete:return unchanged('no_actual_initial_capture')
    if mode!='top_push':return unchanged('original_non_push_mode')
    if normal_load_n<MIN_LOAD_N:return unchanged('original_unloaded_parent')
    previous,reference,surface=[np.asarray(x,dtype=float) for x in (previous_xy,reference_xy,surface_xy)]
    if any(x.shape!=(2,) or not np.isfinite(x).all() for x in (previous,reference,surface)):
        raise ValueError('Finite current material/hand reference and previous emitted command required')
    if np.max(abs(parent-previous))>STEP_M+1e-10:raise ValueError('Parent violated original Cartesian command slew')
    lower=np.maximum.reduce([previous-STEP_M,reference-HAND_LEAD_M,surface-CAP_M])
    upper=np.minimum.reduce([previous+STEP_M,reference+HAND_LEAD_M,surface+CAP_M])
    segment_lower=np.minimum(previous,parent);segment_upper=np.maximum(previous,parent)
    old_feasible=bool(np.all(np.maximum(lower,segment_lower)<=np.minimum(upper,segment_upper)))
    evidence=dict(parent_xy=parent.tolist(),previous_command_xy=previous.tolist(),reference_xy=reference.tolist(),material_surface_xy=surface.tolist(),normal_load_n=float(normal_load_n),cap_xy_m=CAP_M,original_step_m=STEP_M,original_hand_lead_m=HAND_LEAD_M,lower=lower.tolist(),upper=upper.tolist(),projection_strategy=STRATEGY,previous_added_segment_was_feasible=old_feasible)
    if np.any(lower>upper):
        return dict(applied=False,changed=False,requires_recontact=True,reason='empty_original_slew_lead_material_intersection',command_xy=None,**evidence)
    emitted=np.clip(parent,lower,upper)
    return dict(applied=True,changed=bool(np.max(abs(emitted-parent))>1e-12),requires_recontact=False,reason='bounded_material_reference',command_xy=emitted.tolist(),command_material_offset_xy=(emitted-surface).tolist(),command_reference_lead_xy=(emitted-reference).tolist(),command_delta_xy=(emitted-previous).tolist(),boundary_following_repair=not old_feasible,**evidence)
