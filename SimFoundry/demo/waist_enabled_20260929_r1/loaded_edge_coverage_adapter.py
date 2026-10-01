"""Unwired measured-record adapter for stateless current-contact edge repair.
Called after legacy command proposal, before original final clearance/actuation.
Returns (None, trace) on an eligible failure: collector must stop and retain it.
Only actual packet(t-1), current q/object pose and prior row/command are read.
"""
import numpy as np
from loaded_edge_coverage_current_contact import propose
from articulated_hand_geometry import skew

def refine_record(*,enabled=False,selected=False,row,previous_row,coordinate,
                  current,previous,parent_command,packet,object_xyz,
                  object_rotation,core_size,model,geometry,side):
    if type(enabled) is not bool or type(selected) is not bool:raise ValueError('Flags must be bool')
    parent=np.asarray(parent_command,dtype=np.float32)
    if parent.shape!=(11,) or not np.isfinite(parent).all():raise ValueError('Invalid parent command')
    parent=parent.copy()
    if not enabled:return parent,None
    if side not in ['left','right']:raise ValueError('Invalid active hand')
    t=row['step'];prev=previous_row or {};mode=row['mode']
    if type(t) is not int or t<1 or coordinate['step']!=t:raise ValueError('Missing current record')
    if previous_row is not None and previous_row['step']!=t-1:raise ValueError('Stale previous record')
    gates=dict(enabled=True,selected=selected,mode=mode,previous_mode=prev.get('mode'),recontacts=row.get('recontacts',0),previous_recontacts=prev.get('recontacts',0),parent_guard=bool(row.get('route_stop_reason') or row.get('release_reason')),terminal_hold=bool(coordinate.get('terminal_joint_hold')),region_override=bool(coordinate.get('region_joint_override')),unloaded_override=coordinate.get('controller_kind')=='verified_unloaded_recontact_joint_path')
    preliminary=propose(**gates)
    # propose reaches no-current-load only after phase/route/precedence checks.
    if preliminary['reason']!='no_current_loaded_contact':return parent,dict(step=t,**preliminary,context=gates,parent_upper_command=parent.tolist(),final_upper_command=parent.tolist())
    if packet is None or packet['after_action_step']!=t-1:raise ValueError('Missing causal solved force packet')
    obj=np.asarray(object_xyz,dtype=float);R=np.asarray(object_rotation,dtype=float)
    if obj.shape!=(3,) or not np.isfinite(obj).all() or R.shape!=(3,3) or not np.isfinite(R).all() or not np.allclose(R.T@R,np.eye(3),atol=1e-6) or np.linalg.det(R)<.99999:raise ValueError('Invalid measured object pose')
    key='box' if side=='right' else 'mailer';actor='parcel_box' if side=='right' else 'mailer'
    if np.max(abs(np.asarray(packet['post_action_pose'][key])-obj))>1e-6:raise ValueError('Packet/current object mismatch')
    points=[];weights=[]
    for c in packet['parcel_contacts']:
        slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
        if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
        force=np.asarray(c['force_world_N'],dtype=float)*(1 if slots[0]==1 else -1);load=-float(force@R[:,2])
        if not np.isfinite(load):raise ValueError('Nonfinite contact force')
        if load>.05:points.append(c['position_world']);weights.append(load)
    load=sum(weights);cop=R.T@(np.average(points,axis=0,weights=weights)-obj) if load>=.3 else None
    gates.update(load_n=load,previous_load_n=prev.get('contact_load',{}).get('observed_vertical_load_n',0.))
    context=dict(**gates,packet_after_action_step=t-1,current_cop_local=None if cop is None else cop.tolist(),object_xyz=obj.tolist(),object_rotation=R.tolist(),core_size=list(core_size),previous_load_measurement='previous row world-vertical load, diagnostic only; no admission gate')
    if cop is None:
        tr=propose(**gates);return parent,dict(step=t,**tr,context=context,parent_upper_command=parent.tolist(),final_upper_command=parent.tolist())
    q=np.asarray(current,dtype=np.float32);previous=np.asarray(previous,dtype=np.float32);inp=coordinate['task_inputs'];offset=np.asarray(row['control_offset_local'],dtype=float)
    if q.shape!=(11,) or previous.shape!=(11,) or offset.shape!=(3,) or not np.isfinite(q).all() or not np.isfinite(previous).all():raise ValueError('Invalid measured state')
    if not np.array_equal(q,np.asarray(coordinate['upper_q'],dtype=np.float32)) or np.max(abs(q-np.asarray(inp['current'])))>1e-6 or not np.array_equal(previous,np.asarray(inp['previous'],dtype=np.float32)):raise ValueError('State/command context mismatch')
    if coordinate['active_side']!=side or coordinate['bounded_solver'] is not True or coordinate['contact_normal_tracking'] is None or coordinate['contact_bout_yaw_tracking'] is not None or coordinate['waist_preference_rad'] is not None or coordinate['preferred_waist_step_rad']!=0:raise ValueError('Unsupported loaded task')
    def point(x):T,_,_=model.fk(side,x);return T[:3,3]+T[:3,:3]@offset
    def jac(x):T,jl,jw=model.fk(side,x);return jl-skew(T[:3,:3]@offset)@jw
    if np.max(abs(point(q)-np.asarray(row['observed_support_xyz'])))>2e-6 or np.max(abs(point(q)-np.asarray(coordinate['control_point_positions'][side])))>2e-6:raise ValueError('Measured reference mismatch')
    tr=propose(**gates,current=q,previous_command=previous,parent_command=parent,jacobian=inp['jacobian'],error=inp['error'],damping=inp['damping'],lower=inp['lower'],upper=inp['upper'],step_limits=inp['step_limits'],object_rotation=R,cop_local=cop,core_size=core_size,direction=-1 if side=='right' else 1,point_fn=point,point_jacobian_fn=jac,geometry=geometry)
    command=(np.asarray(tr['command'],dtype=np.float32) if tr['override'] else parent) if tr['accepted'] else None
    return command,dict(step=t,**tr,context=context,parent_upper_command=parent.tolist(),final_upper_command=None if command is None else command.tolist())
