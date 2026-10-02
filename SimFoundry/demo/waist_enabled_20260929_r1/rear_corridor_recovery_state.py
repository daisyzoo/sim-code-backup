"""Explicit bookkeeping commits after a verified joint command is selected.
No robot/parcel state writes and no measured-arrival assertion. These functions
must be called only for the command actually emitted after the final guard.
The original recontact lifecycle still owns measured unloading/path/handover.
"""
import numpy as np


def checked_reference(*,state,guard,row,coordinate,current,previous,command,result,reason):
    if state.top_mode!='top_push' or row['mode']!='top_push' or row.get('route_stop_reason') or row.get('release_reason') or coordinate.get('terminal_joint_hold') or coordinate.get('region_joint_override'):raise ValueError('Original guard priority')
    t=row['step']
    if type(t) is not int or t<1 or coordinate['step']!=t or t<=getattr(state,'rear_corridor_last_commit_step',-1):raise ValueError('Invalid/repeated state commit')
    if not result.get('applied') or result.get('reason')!=reason:raise ValueError('Verified command result required')
    q,prev,cmd=[np.asarray(v,float) for v in [current,previous,command]]
    if any(v.shape!=(11,) or not np.isfinite(v).all() for v in [q,prev,cmd]):raise ValueError('Invalid command context')
    if not np.array_equal(q,np.asarray(coordinate['upper_q'])) or not np.array_equal(prev,np.asarray(coordinate['task_inputs']['previous'])):raise ValueError('Causal context mismatch')
    accepted=[a for a in result['attempts'] if a['accepted']]
    if len(accepted)!=1 or not np.array_equal(cmd,np.asarray(accepted[0]['command'])):raise ValueError('Command differs from verified output')
    check=guard.command(cmd,q,prev)
    if not check['accepted']:raise ValueError('Final guard rejected state commit')
    side=coordinate['active_side'];offset=np.asarray(row['control_offset_local'],float)
    if offset.shape!=(3,) or not np.isfinite(offset).all():raise ValueError('Invalid control offset')
    T,_,_=guard.model.fk(side,cmd);T0,_,_=guard.model.fk(side,q);p=T[:3,3]+T[:3,:3]@offset;observed=T0[:3,3]+T0[:3,:3]@offset
    if max(abs(observed-np.asarray(row['observed_support_xyz'])))>2e-6:raise ValueError('Observed reference mismatch')
    return t,p,observed,check


def commit_loaded(**kwargs):
    t,p,observed,check=checked_reference(**kwargs,reason='nominal_rear_corridor_recovery');state=kwargs['state']
    old=dict(command=state.command,last_waypoint_xy=state.last_waypoint_xy,push_x_anchor=state.push_x_anchor)
    state.command=tuple(p);state.last_waypoint_xy=tuple(p[:2])
    if state.hold_established_x or state.hold_push_x:state.push_x_anchor=float(p[0])
    state.rear_corridor_last_commit_step=t
    return dict(kind='committed_recovery_reference',step=t,old=old,new=dict(command=state.command,last_waypoint_xy=state.last_waypoint_xy,push_x_anchor=state.push_x_anchor),measured_reference=observed.tolist(),scope='Verified command FK reference only; not measured arrival',final_guard=check)


def begin_lift(**kwargs):
    t,p,observed,check=checked_reference(**kwargs,reason='nominal_vertical_unload');state=kwargs['state']
    if getattr(state,'rear_corridor_recontact_pending',False):raise ValueError('Recontact already pending')
    before=dict(recontacts=state.recontacts,bias_m=state.load.bias_m,filtered_n=state.load.filtered_n)
    state._start_recontact(tuple(observed),'rear_corridor_no_verified_loaded_step')
    state.mode=state.top_mode;state.last_waypoint_xy=tuple(p[:2]);state.rear_cop.reset()
    state.rear_corridor_last_commit_step=t;state.rear_corridor_recontact_pending=True
    return dict(kind='started_original_recontact_lift',step=t,before=before,recontacts=state.recontacts,bias_m=state.load.bias_m,filtered_n=state.load.filtered_n,verified_first_lift_reference=p.tolist(),measured_reference=observed.tolist(),requires_measured_unloaded=True,requires_direction_checked_endpoint=True,final_guard=check)
