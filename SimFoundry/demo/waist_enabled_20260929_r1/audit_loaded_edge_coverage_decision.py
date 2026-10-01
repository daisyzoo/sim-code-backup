"""Independent coverage/precedence checker for every declared loaded-edge call.
Candidate modules are not imported. Original parent proposal assembly, full
geometry outside overrides, episode provenance and task success remain separate.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from audit_loaded_edge_coverage_record import verify, near


def verify_decision(tr, *, row, previous_row, coordinate, current, previous_command,
                    parent_command, final_command, packet, object_xyz, object_quat,
                    core_size, side, selected, hand, elbows):
    t=row['step'];prev=previous_row or {};assert tr['step']==coordinate['step']==t
    if previous_row is not None:assert previous_row['step']==t-1
    near(tr['parent_upper_command'],parent_command,0)
    near(tr['final_upper_command'],final_command,0)
    reason=None
    if not selected:reason='not_selected_rear'
    elif row.get('route_stop_reason') or row.get('release_reason') or coordinate.get('terminal_joint_hold') or coordinate.get('region_joint_override') or coordinate.get('controller_kind')=='verified_unloaded_recontact_joint_path':reason='parent_precedence'
    elif row['mode']!='top_push':reason='original_mode_guard'
    elif prev.get('mode')!='top_push' or prev.get('recontacts',0)!=row.get('recontacts',0):reason='genuine_push_transition'
    if reason is None:
        near(coordinate['upper_q'],current,1e-7)
        assert packet['after_action_step']==t-1
        key,actor=('box','parcel_box') if side=='right' else ('mailer','mailer')
        R=Rotation.from_quat(object_quat).as_matrix();xyz=np.asarray(object_xyz,float)
        near(packet['post_action_pose'][key],xyz,1e-6)
        loads=[];points=[]
        for c in packet['parcel_contacts']:
            slots=[i for i,name in enumerate(c['shapes']) if '/'+actor+'/' in name]
            if len(slots)!=1 or not any(side+'_wrist' in name for name in c['shapes']):continue
            load=-float((np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1))@R[:,2]);assert np.isfinite(load)
            if load>.05:loads.append(load);points.append(c['position_world'])
        total=sum(loads);near(tr['context']['load_n'],total,2e-6)
        if total<.3:reason='no_current_loaded_contact'
        else:
            cop=R.T@(np.average(points,axis=0,weights=loads)-xyz);near(tr['context']['current_cop_local'],cop,2e-8)
            axes=[k for k in [0,1] if core_size[k]/2-abs(cop[k])<=.01]
            if not axes:reason='no_near_core_edge'
    if reason is not None:
        assert tr['reason']==reason and tr['eligible'] is False and tr['accepted'] is True and tr['override'] is False
        near(final_command,parent_command,0)
        return dict(step=t,passed=True,eligible=False,override=False,reason=reason)
    assert tr['eligible'] is True and tr['threatened_axes']==axes
    q=np.asarray(current,float);previous=np.asarray(previous_command,float);parent=np.asarray(parent_command,float);inp=coordinate['task_inputs']
    near(inp['current'],q,1e-6);near(inp['previous'],previous,0)
    low=np.maximum.reduce([np.array(inp['lower']),q-np.array(inp['step_limits']),previous-.055]);high=np.minimum.reduce([np.array(inp['upper']),q+np.array(inp['step_limits']),previous+.055])
    near(tr['bound_low'],low,1e-7);near(tr['bound_high'],high,1e-7)
    offset=np.asarray(row['control_offset_local'])
    def point(x):T=hand.fk(x,side);return T[:3,3]+T[:3,:3]@offset
    motion=point(parent)-point(q);values=[float(-np.sign(cop[k])*R[:,k]@motion) for k in axes]+[float((-1 if side=='right' else 1)*motion[1])]
    valid=bool(np.all(low<high) and min(values)>=-1e-7 and min(elbows.gap(parent))>=.005-2e-7 and min(parent-low)>=-2e-7 and min(high-parent)>=-2e-7)
    if valid:
        assert tr['reason']=='parent_already_valid' and tr['override'] is False and tr['accepted'] is True
        near(final_command,parent,0)
        return dict(step=t,passed=True,eligible=True,override=False,reason=tr['reason'])
    # A failure/rejection must never be reported as a passing executed command.
    assert tr['override'] is True and tr['accepted'] is True, 'no verified edge command'
    checked=verify(tr,row=row,previous_row=previous_row,coordinate=coordinate,current=current,previous_command=previous_command,parent_command=parent_command,final_command=final_command,packet=packet,object_xyz=object_xyz,object_quat=object_quat,core_size=core_size,side=side,selected=selected,hand=hand,elbows=elbows)
    return dict(**checked,eligible=True,override=True,reason=tr['reason'])
