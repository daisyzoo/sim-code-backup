"""Original normal task math with explicitly verified unloaded handovers.
A caller must independently verify every event before supplying verified_events.
Original normal target stays fixed except initial capture and measured handover;
joint-path frames explicitly execute no normal task. Finite-difference URDF J.
"""
import numpy as np
from audit_unloaded_wrist_prior_live import near

def verify_normal_rows(q,coords,experts,topsteps,verified_events,model,side,*,enabled=True):
    assert enabled is True
    assert [c['step'] for c in coords]==list(range(1,len(q)))
    assert set(verified_events)<=set(topsteps)
    anchor=None;records=[];jacobians=[];captures=[]
    def normal(state):return model.fk(np.asarray(state,float),side)[2,:3]
    for row in coords:
        t=row['step'];mode=experts[t]['mode'];current=normal(q[t]);event=verified_events.get(t)
        if event is not None:
            assert event['kind'] in ('command','handover') and row['controller_kind']=='verified_unloaded_recontact_joint_path'
            assert row['contact_normal_tracking'] is None and row['task_inputs'] is None
            assert row['recontact_pose_override']==event
            if event['kind']=='handover':
                anchor=np.array(event['captured_normal_local_up']);near(anchor,current,2e-6);captures.append(t);assert mode=='top_press'
            else:assert mode=='top_cross'
            records.append(dict(step=t,kind='declared_joint_path',normal_task=False));continue
        assert row.get('controller_kind')!='verified_unloaded_recontact_joint_path'
        if t in topsteps and anchor is None and mode in ('top_press','top_push'):anchor=current.copy()
        expected=t in topsteps and anchor is not None and mode in ('top_lift','top_cross','top_descend','top_press','top_push')
        actual=row.get('contact_normal_tracking');assert (actual is not None)==bool(expected),(t,'normal_activation')
        if actual is None:continue
        near(actual['current_local_up'],current,2e-6);near(actual['target_local_up'],anchor,2e-6)
        correction=.15*np.clip(.72*(anchor-current),-.1,.1);near(actual['error'],correction,2e-6)
        raw_angle=float(np.arccos(np.clip(np.array(actual['current_local_up'])@np.array(actual['target_local_up']),-1,1)))
        near(actual['angle_error_rad'],raw_angle,1e-9);assert actual['weight_m']==.15
        assert np.asarray(actual['jacobian']).shape==(3,11) and np.isfinite(actual['jacobian']).all()
        records.append(dict(step=t,kind='original_normal_task',normal_task=True))
        if t%20==0:
            fd=np.empty((3,11));h=1e-6
            for j in range(11):
                delta=np.zeros(11);delta[j]=h;fd[:,j]=.15*(normal(q[t]+delta)-normal(q[t]-delta))/(2*h)
            near(actual['jacobian'],fd,2e-6);jacobians.append(t)
    return dict(passed=True,frames=len(coords),normal_frames=sum(r['normal_task'] for r in records),joint_path_frames=sum(not r['normal_task'] for r in records),jacobian_samples=len(jacobians),measured_recapture_steps=captures,records=records)
