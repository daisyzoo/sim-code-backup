"""Diagnostic coupled palm-position IK; not a certified collision planner."""
import numpy as np
import torch
from isaaclab.utils.math import quat_apply
from simfoundry.data.sorting_quality import PALM_OFFSET
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES


def coordinated_step(robot, hands, action, *, state, anchor, default, waist_limit, bounded=False, active_point_offset=None, trace_jacobian=False, waist_preference=None, active_support_reference=None, active_normal_anchor_local=None, active_bout_yaw_anchor=None, clearance_geometry=None, previous_command=None, recontact_override=None, front_initial_override=None, front_recontact_override=None, precise_task_ik=False):
    """Track active path and keep inactive palm at its initial world position.

    Joint regularization limits gratuitous waist motion. Full-arm collision
    clearance is not guaranteed; all output is quarantined diagnostic data.
    """
    indices = list(range(12, 23))
    joint_ids = [robot.joint_names.index(G1_U1_23DOF_JOINT_NAMES[i]) for i in indices]
    cols = [j + robot.num_base_dofs for j in joint_ids]
    rows, errors, palms, points = [], [], {}, {}
    for side in ('left', 'right'):
        body = hands[side]
        pos = robot.data.body_pos_w.torch[0, body]
        quat = robot.data.body_quat_w.torch[0, body]
        palm_offset = quat_apply(quat[None], pos.new_tensor(PALM_OFFSET)[None])[0]
        palms[side] = (pos+palm_offset).detach().cpu().numpy().tolist()
        local_offset = active_point_offset if side == state.side and active_point_offset is not None else PALM_OFFSET
        offset = quat_apply(quat[None], pos.new_tensor(local_offset)[None])[0]
        palm = pos + offset
        points[side] = palm.detach().cpu().numpy().tolist()
        jac = robot.data.body_link_jacobian_w.torch[0, body-1 if robot.is_fixed_base else body, :, cols]
        x,y,z = offset
        zero = x.new_zeros(())
        skew = torch.stack([torch.stack([zero,-z,y]),torch.stack([z,zero,-x]),torch.stack([-y,x,zero])])
        target = state.last_target_xyz if side == state.side else anchor[side]
        if side == state.side and active_support_reference is not None:
            from simfoundry.data.projected_support_reference import projected_support_jacobian
            from simfoundry.data.top_contact_bypass import rotation_xyzw
            reference={k:np.asarray(v,dtype=float) for k,v in active_support_reference.items()}
            if active_point_offset is None or not np.allclose(reference['reference_local'],active_point_offset,atol=1e-8):
                raise ValueError('Projected support reference differs from controlled point')
            controlled_jacobian=projected_support_jacobian(jac[:3].detach().cpu().numpy(),jac[3:].detach().cpu().numpy(),rotation_xyzw(quat.detach().cpu().numpy()),reference)
            rows.append(jac.new_tensor(controlled_jacobian))
        else:
            rows.append(jac[:3] - skew @ jac[3:])
        errors.append(torch.clamp(.72*(pos.new_tensor(target)-palm),-.035,.035))
    if front_initial_override is not None and recontact_override is not None:
        raise ValueError('Competing initial front and rear recovery overrides')
    if sum(x is not None for x in (front_recontact_override,front_initial_override,recontact_override))>1:
        raise ValueError('Competing independently declared joint-path overrides')
    if front_recontact_override is not None:
        if front_recontact_override.get('kind') not in ('command','handover') or not front_recontact_override.get('proposal',{}).get('applied'):
            raise ValueError('Unverified unloaded front recovery override')
        target=np.asarray(front_recontact_override['command'],dtype=np.float32)
        current=robot.data.joint_pos.torch[0,joint_ids].detach().cpu().numpy()
        if not bounded or clearance_geometry is None or np.any(default[indices]!=0) or not np.allclose(current,front_recontact_override['context']['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,front_recontact_override['context']['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Front recovery command context differs from actual controller state')
        if target.shape!=(11,) or not np.isfinite(target).all():raise ValueError('Invalid front recovery command')
        proposal=front_recontact_override['proposal'];context=front_recontact_override['context']
        if not np.array_equal(target,np.asarray(proposal['candidate_command'],dtype=np.float32)) or not np.allclose(current,proposal['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,proposal['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Front recovery proposal differs from emitted command/context')
        if context['guard_stop'] or not context['selected'] or (type(context['recontacts']) is not int or context['recontacts']<1 or (context['scene']['side']!=state.side or not (state.side=='left' or (state.side=='right' and front_recontact_override.get('front_box_recenter_version') in ('front_box_recenter_v1','front_box_trailing_20mm_reserve_05mm_v1')))) or front_recontact_override.get('real_recontact_index')!=context['recontacts']) or context['observed_load_n']!=0. or not 0<=context['filtered_load_n']<=.05 or context['parent_mode'] not in ('top_cross','top_descend'):
            raise ValueError('Front recovery override not currently unloaded')
        if not (proposal['command_check']['accepted'] and proposal['nominal_scene']['accepted'] and proposal['predicted_scene']['accepted']):
            raise ValueError('Front recovery proposal did not pass geometry')
        action[indices]=target-default[indices]
        return dict(palm_positions=palms,control_point_positions=points,active_point_offset_local=active_point_offset,waist_target_rad=float(target[0]),inactive_anchor=anchor['right' if state.side=='left' else 'left'],bounded_solver=True,waist_preference_rad=None,preferred_waist_step_rad=0.,full_arm_clearance_verified=False,active_support_reference=active_support_reference,contact_normal_tracking=None,contact_bout_yaw_tracking=None,upper_q=current.tolist(),active_side=state.side,task_inputs=None,front_recontact_center_override=front_recontact_override,controller_kind='verified_unloaded_front_recontact_joint_path')
    if front_initial_override is not None:
        if front_initial_override.get('kind') not in ('command','handover') or not front_initial_override.get('proposal',{}).get('applied'):
            raise ValueError('Unverified unloaded initial front override')
        target=np.asarray(front_initial_override['command'],dtype=np.float32)
        current=robot.data.joint_pos.torch[0,joint_ids].detach().cpu().numpy()
        if not bounded or clearance_geometry is None or np.any(default[indices]!=0) or not np.allclose(current,front_initial_override['context']['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,front_initial_override['context']['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Initial front command context differs from actual controller state')
        if target.shape!=(11,) or not np.isfinite(target).all():raise ValueError('Invalid initial front command')
        proposal=front_initial_override['proposal'];context=front_initial_override['context']
        if not np.array_equal(target,np.asarray(proposal['candidate_command'],dtype=np.float32)) or not np.allclose(current,proposal['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,proposal['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Initial front proposal differs from emitted command/context')
        if context['guard_stop'] or not context['selected'] or context['recontacts']!=0 or context['observed_load_n']!=0. or not 0<=context['filtered_load_n']<=.05 or context['parent_mode'] not in ('top_cross','top_descend'):
            raise ValueError('Initial front override not currently unloaded')
        if not (proposal['command_check']['accepted'] and proposal['nominal_scene']['accepted'] and proposal['predicted_scene']['accepted']):
            raise ValueError('Initial front proposal did not pass geometry')
        action[indices]=target-default[indices]
        return dict(palm_positions=palms,control_point_positions=points,active_point_offset_local=active_point_offset,waist_target_rad=float(target[0]),inactive_anchor=anchor['right' if state.side=='left' else 'left'],bounded_solver=True,waist_preference_rad=None,preferred_waist_step_rad=0.,full_arm_clearance_verified=False,active_support_reference=active_support_reference,contact_normal_tracking=None,contact_bout_yaw_tracking=None,upper_q=current.tolist(),active_side=state.side,task_inputs=None,front_initial_center_override=front_initial_override,controller_kind='verified_unloaded_front_initial_joint_path')
    if recontact_override is not None:
        if recontact_override.get('kind') not in ('command','handover') or not recontact_override.get('proposal',{}).get('applied'):
            raise ValueError('Unverified unloaded recovery override')
        target=np.asarray(recontact_override['command'],dtype=np.float32)
        current=robot.data.joint_pos.torch[0,joint_ids].detach().cpu().numpy()
        if not bounded or clearance_geometry is None or np.any(default[indices]!=0) or not np.allclose(current,recontact_override['context']['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,recontact_override['context']['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Recovery command context differs from actual controller state')
        if target.shape!=(11,) or not np.isfinite(target).all():raise ValueError('Invalid recovery command')
        proposal=recontact_override['proposal'];context=recontact_override['context']
        if not np.array_equal(target,np.asarray(proposal['candidate_command'],dtype=np.float32)) or not np.allclose(current,proposal['current'],atol=1e-7,rtol=0) or not np.allclose(previous_command,proposal['previous_command'],atol=1e-7,rtol=0):
            raise ValueError('Recovery proposal differs from emitted command/context')
        if context['guard_stop'] or not context['selected'] or context['recontacts']<1 or context['observed_load_n']!=0. or not 0<=context['filtered_load_n']<=.05 or context['parent_mode'] not in ('top_cross','top_descend'):
            raise ValueError('Recovery override not currently unloaded')
        if not (proposal['command_check']['accepted'] and proposal['nominal_scene']['accepted'] and proposal['predicted_scene']['accepted']):
            raise ValueError('Recovery proposal did not pass geometry')
        action[indices]=target-default[indices]
        return dict(palm_positions=palms,control_point_positions=points,active_point_offset_local=active_point_offset,waist_target_rad=float(target[0]),inactive_anchor=anchor['right' if state.side=='left' else 'left'],bounded_solver=True,waist_preference_rad=None,preferred_waist_step_rad=0.,full_arm_clearance_verified=False,active_support_reference=active_support_reference,contact_normal_tracking=None,contact_bout_yaw_tracking=None,upper_q=current.tolist(),active_side=state.side,task_inputs=None,recontact_pose_override=recontact_override,controller_kind='verified_unloaded_recontact_joint_path')
    position_jac = torch.cat(rows)
    normal_record = None
    if active_normal_anchor_local is not None:
        from simfoundry.data.contact_normal_constraint import contact_normal_constraint
        from simfoundry.data.top_contact_bypass import rotation_xyzw
        body = hands[state.side]
        normal_rotation = rotation_xyzw(robot.data.body_quat_w.torch[0,body].detach().cpu().numpy())
        angular_jac = robot.data.body_link_jacobian_w.torch[0,body-1 if robot.is_fixed_base else body,3:,cols]
        constraint = contact_normal_constraint(normal_rotation,angular_jac.detach().cpu().numpy(),active_normal_anchor_local)
        rows.append(position_jac.new_tensor(constraint['jacobian']))
        errors.append(position_jac.new_tensor(constraint['error']))
        normal_record = {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in constraint.items()}
    yaw_record = None
    if active_bout_yaw_anchor is not None:
        if active_normal_anchor_local is None:
            raise ValueError('Contact-bout yaw requires original normal tracking')
        from simfoundry.data.contact_bout_yaw import contact_bout_yaw_constraint
        constraint = contact_bout_yaw_constraint(normal_rotation, angular_jac.detach().cpu().numpy(), active_bout_yaw_anchor)
        rows.append(position_jac.new_tensor(constraint['jacobian']))
        errors.append(position_jac.new_tensor(constraint['error']))
        yaw_record = {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in constraint.items()}
    jac = torch.cat(rows)
    error = torch.cat(errors)
    penalty = torch.full((11,), .045**2, device=jac.device, dtype=jac.dtype)
    penalty[0] = .12**2
    current = robot.data.joint_pos.torch[0,joint_ids]
    prior = torch.zeros_like(current)
    if waist_preference is not None:
        if not np.isfinite(waist_preference) or abs(waist_preference)>waist_limit:raise ValueError('Invalid waist preference')
        prior[0] = torch.clamp(.15*(float(waist_preference)-current[0]),-.015,.015)
    dq = torch.linalg.solve(jac.T@jac + torch.diag(penalty),jac.T@error + penalty*prior)
    dq = torch.clamp(dq,-.04,.04)
    dq[0] = torch.clamp(dq[0],-.015,.015)
    current = robot.data.joint_pos.torch[0,joint_ids]
    target = (current+dq).detach().cpu().numpy()
    clearance_record = None
    task_inputs = None
    if clearance_geometry is not None and not bounded:
        raise ValueError("Self-clearance task requires bounded IK")
    if bounded:
        from simfoundry.data.bounded_ik import bounded_damped_step
        from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI
        lo=np.asarray(U1_JOINT_LIMIT_LO)[indices].copy()
        hi=np.asarray(U1_JOINT_LIMIT_HI)[indices].copy()
        hi[0]=waist_limit-min(.02,.1*waist_limit);lo[0]=-hi[0]
        limits=np.full(11,.04);limits[0]=.015
        q=current.detach().cpu().numpy()
        step=bounded_damped_step(jac.detach().cpu().numpy(),error.detach().cpu().numpy(),q,lo,hi,limits,np.sqrt(penalty.detach().cpu().numpy()),preferred_step=prior.detach().cpu().numpy())
        target=q+step
        if clearance_geometry is not None:
            from task_ik import solve
            if precise_task_ik:
                from task_ik_precision import solve
            task_inputs=dict(jacobian=jac.detach().cpu().numpy().tolist(),error=error.detach().cpu().numpy().tolist(),current=q.tolist(),previous=np.asarray(previous_command).tolist(),lower=lo.tolist(),upper=hi.tolist(),step_limits=limits.tolist(),damping=np.sqrt(penalty.detach().cpu().numpy()).tolist(),preferred_step=prior.detach().cpu().numpy().tolist())
            target,clearance_record=solve(enabled=True,geometry=clearance_geometry,**task_inputs)
            if target is None:
                return dict(self_clearance_task=clearance_record,task_inputs=task_inputs,no_verified_command=True,upper_q=q.tolist(),active_side=state.side)
    # Reserve 10% (at most .02 rad) for physical tracking overshoot.
    command_limit = waist_limit - min(.02, .1 * waist_limit)
    target[0] = np.clip(target[0],-command_limit,command_limit)
    action[indices] = target - default[indices]
    result = {'palm_positions':palms, 'control_point_positions':points, 'active_point_offset_local':active_point_offset, 'waist_target_rad':float(target[0]),
            'inactive_anchor':anchor['right' if state.side=='left' else 'left'],
            'bounded_solver':bounded, 'waist_preference_rad':waist_preference, 'preferred_waist_step_rad':float(prior[0]), 'full_arm_clearance_verified':False, 'active_support_reference':active_support_reference, 'contact_normal_tracking':normal_record, 'contact_bout_yaw_tracking':yaw_record}
    if clearance_record is not None:
        result["self_clearance_task"] = clearance_record
        result["task_inputs"] = task_inputs
    if trace_jacobian:
        result['control_jacobian_world']=position_jac.detach().cpu().numpy().tolist()
        result['upper_q']=current.detach().cpu().numpy().tolist()
        result['active_side']=state.side
    return result


def hand_point_xyz(robot, hand_index, local_offset):
    pos=robot.data.body_pos_w.torch[0,hand_index]
    quat=robot.data.body_quat_w.torch[0,hand_index]
    offset=quat_apply(quat[None],pos.new_tensor(local_offset)[None])[0]
    return (pos+offset).detach().cpu().numpy().tolist()
