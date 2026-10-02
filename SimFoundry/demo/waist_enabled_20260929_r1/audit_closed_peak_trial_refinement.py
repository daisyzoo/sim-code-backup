"""Independent fixed0.5mm nominal constraint and metadata verification.
No controller imports. Future actual COP/parcel movement is not certified.
"""
import copy
import numpy as np
from audit_inward_command_probe import verify_refinement as verify_offset
from audit_box_entry_pose_loaded_execution import verify_refinement as verify_original,near

FIELDS=('nominal_inward_requirement_m','physical_motion_prediction','parent_edge_constraint_residual_m','edge_constraint_residual_m')

def normalized_trace(trace,enabled):
    assert type(enabled) is bool and isinstance(trace,dict)
    if not enabled:
        assert not any(k in trace for k in FIELDS),'inward metadata on unselected side'
        return copy.deepcopy(trace)
    assert type(trace.get('nominal_inward_requirement_m')) is float and trace['nominal_inward_requirement_m']==.0005,'fixed inward requirement'
    assert trace.get('physical_motion_prediction') is False,'nominal requirement is not dynamics prediction'
    out=copy.deepcopy(trace)
    out.pop('nominal_inward_requirement_m');out.pop('physical_motion_prediction')
    for actual,residual in [('parent_nominal_edge_inward_m','parent_edge_constraint_residual_m'),('nominal_edge_inward_m','edge_constraint_residual_m')]:
        assert (actual in out)==(residual in out),'incomplete inward metadata'
        if actual in out:
            a=np.asarray(out[actual],dtype=float);b=np.asarray(out[residual],dtype=float)
            assert a.ndim==b.ndim==1 and a.shape==b.shape and 1<=len(a)<=2 and np.isfinite(a).all() and np.isfinite(b).all()
            near(a,b+.0005,2e-12)
            out[actual]=out.pop(residual)
    return out

def verify_refinement(trace,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active,*,inward_enabled):
    tr=normalized_trace(trace,inward_enabled)
    if inward_enabled:assert direction==-1 and active==[3,4,5],'right rear only'
    axes=[k for k in [0,1] if core[k]/2-abs(local[k])<=.01]
    if not axes:
        assert tr['override'] is False and tr['reason']=='no_threatened_core_edge'
        near(tr['parent_final_upper_command'],parent,0);near(tr['final_upper_command'],actual,0);near(tr['previous_upper_command'],previous,0);near(actual,parent,0)
        assert not any(k in tr for k in ['nominal_edge_inward_m','parent_nominal_edge_inward_m','threatened_axes','command'])
        return dict(refined=False,reason=tr['reason'])
    args=(tr,parent,actual,previous,q,J,error,damping,lower,upper,limits,point_and_jacobian,rotation,local,core,direction,active)
    result=verify_offset(*args,inward_step_m=.0005) if inward_enabled else verify_original(*args)
    if inward_enabled and 'nominal_min_edge_inward_m' in result:
        result['minimum_constraint_residual_m']=result['nominal_min_edge_inward_m']
        result['nominal_min_edge_inward_m']+=.0005
    return result

def verify_plan(args,plan,meta):
    assert args.get('rear_box_inward_correction') is True and meta.get('rear_box_inward_correction') is True
    selected=bool(plan.get('rear_joint_edge_command',{}).get('enabled')) and plan['direction']==-1
    expected=dict(enabled=True,side='right',nominal_inward_requirement_m=.0005,existing_joint_xy_eligibility=True,original_task_objective=True,original_bounds_and_guards=True,physical_motion_prediction=False,training_ready=False)
    if selected:
        actual=plan.get('rear_box_inward_correction');assert actual==expected
        assert all(type(actual[k]) is type(v) for k,v in expected.items())
    else:assert 'rear_box_inward_correction' not in plan
    return selected
