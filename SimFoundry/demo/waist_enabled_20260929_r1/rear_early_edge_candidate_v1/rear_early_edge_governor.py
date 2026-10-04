"""Isolated default-off joint X/Y reference governor; not connected to collector.

Caller must retain original mode/recontact/first-load guards. This function is
only eligible after valid parent rear-X feedback. It predicts no physical COP.
"""
import itertools
import numpy as np


def _govern(*, edge_margin_m, enabled, mode, previous_xyz, parent_xyz,
                        reference_xyz, object_rotation, core_size, cop_local,
                        normal_load_n, direction):
    if type(enabled) is not bool:
        raise ValueError('enabled must be bool')
    if not enabled:
        return dict(override=False, reason='disabled')
    if mode != 'top_push':
        return dict(override=False, reason='original_non_push_mode')
    if not np.isfinite(normal_load_n) or normal_load_n < 0:
        raise ValueError('Invalid normal load')
    if cop_local is None or normal_load_n < .3:
        return dict(override=False, reason='no_valid_loaded_contact')
    if isinstance(direction, bool) or direction not in (-1, 1):
        raise ValueError('Invalid direction')
    prev,parent,ref,rot,size,cop=[np.asarray(v,dtype=float) for v in
        [previous_xyz,parent_xyz,reference_xyz,object_rotation,core_size,cop_local]]
    if [v.shape for v in [prev,parent,ref,rot,size,cop]] != [(3,),(3,),(3,),(3,3),(3,),(3,)]:
        raise ValueError('Invalid geometry shapes')
    if not all(np.isfinite(v).all() for v in [prev,parent,ref,rot,size,cop]):
        raise ValueError('Nonfinite geometry')
    if not np.allclose(rot.T@rot,np.eye(3),atol=1e-6) or np.linalg.det(rot)<.99999:
        raise ValueError('Invalid rotation')
    if np.any(size[:2]<=.02) or size[2]<=0:
        raise ValueError('Empty10mm core inset')
    delta=parent-prev
    if direction*delta[1]<-1e-10:
        return dict(override=False,reason='parent_nonforward_preserved')
    near=np.flatnonzero(size[:2]/2-abs(cop[:2])<edge_margin_m)
    if not len(near):
        return dict(override=False,reason='no_near_core_edge')
    low=max(prev[0]-.002,ref[0]-.030);high=min(prev[0]+.002,ref[0]+.030)
    if low>high:
        return dict(override=False,reason='no_cartesian_slew_and_lead_interval')
    xmin,xmax=(low-prev[0])*1000,(high-prev[0])*1000
    A=[];b=[]
    for i in near:
        sign=1. if cop[i]>=0 else -1.
        A.append([sign*rot[0,i],sign*rot[1,i]*delta[1]*1000])
        b.append(-sign*rot[2,i]*delta[2]*1000)
    A.extend([[-1,0],[1,0],[0,-1],[0,1]]);b.extend([-xmin,xmax,0,1])
    A=np.asarray(A);b=np.asarray(b);vertices=[]
    for i,j in itertools.combinations(range(len(b)),2):
        M=A[[i,j]]
        if abs(np.linalg.det(M))<1e-12:
            continue
        point=np.linalg.solve(M,b[[i,j]])
        if np.max(A@point-b)<=1e-8:
            vertices.append(point)
    evidence=dict(near_axes=near.tolist(),feasible_x_interval_m=[low,high],
                  constraints_mm=A.tolist(),rhs_mm=b.tolist())
    if not vertices:
        return dict(override=False,reason='no_joint_XY_direction',**evidence)
    scale=float(np.clip(max(v[1] for v in vertices),0.,1.))
    for a,rhs in zip(A,b):
        rhs-=a[1]*scale
        if abs(a[0])<1e-12:
            if rhs<-1e-8:
                return dict(override=False,reason='numerical_infeasible',**evidence)
        elif a[0]>0:
            xmax=min(xmax,rhs/a[0])
        else:
            xmin=max(xmin,rhs/a[0])
    if xmin>xmax+1e-8:
        return dict(override=False,reason='numerical_infeasible',**evidence)
    dx=float(np.clip(delta[0]*1000,xmin,xmax));point=np.array([dx,scale])
    if np.max(A@point-b)>1e-8:
        return dict(override=False,reason='numerical_infeasible',**evidence)
    command=parent.copy();command[0]=prev[0]+dx/1000;command[1]=prev[1]+scale*delta[1]
    if np.max(abs(command-parent))<1e-10:
        return dict(override=False,reason='original_direction_feasible',scale=scale,**evidence)
    return dict(override=True,reason='joint_XY_nonoutward_reference',command_xyz=command.tolist(),
                scale=scale,parent_delta_xyz_m=delta.tolist(),
                reference_delta_xyz_m=(command-prev).tolist(),
                projected_local_xy_delta_m=(rot.T@(command-prev))[:2].tolist(),**evidence)


def govern_rear_joint_xy_early(*, early_enabled, side, **parent_arguments):
    """Unwired box-only early warning; preserve full parent on any fallback.

    Parent arguments and original10mm solver are unchanged. The20mm candidate
    can replace it only with a feasible override. Disabled and left-side calls
    return the exact parent dictionary without new metadata.
    """
    if type(early_enabled) is not bool:
        raise ValueError('early_enabled must be bool')
    if side not in ('left','right'):
        raise ValueError('Invalid active side')
    parent = _govern(edge_margin_m=.010, **parent_arguments)
    if not early_enabled or side != 'right':
        return parent
    candidate = _govern(edge_margin_m=.020, **parent_arguments)
    accepted = bool(candidate['override'])
    selected = candidate if accepted else parent
    result = dict(selected)
    result['early_edge'] = dict(
        version='rear_box_early20_preserve_parent10_v1',
        candidate_selected=accepted,
        parent_result=parent,
        candidate_result=candidate,
        fallback='complete_original_joint_XY_result' if not accepted else None,
        warning_inset_m=.020,
        original_inset_m=.010,
        physics_verified=False,
    )
    return result
