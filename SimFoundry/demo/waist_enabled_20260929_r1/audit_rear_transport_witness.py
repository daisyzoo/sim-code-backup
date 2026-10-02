"""Independent unloaded +X endpoint and every sampled path-point verification.
Uses existing independent URDF/convex-hand/elbow geometry, no candidate solver.
A nominal unloaded direction witness is not loaded traction or physical contact.
"""
import numpy as np
from audit_recontact_pose_events import EventAudit
from audit_unloaded_wrist_prior_live import near


def verify_witness(audit, record, *, endpoint, scene):
    q=np.asarray(endpoint,float);x=np.asarray(record['candidate'],float);side=scene['side'];inactive='left' if side=='right' else 'right'
    assert q.shape==x.shape==(11,) and np.isfinite(q).all() and np.isfinite(x).all()
    assert record['accepted'] is True and record['reason']=='nominal_unloaded_transport_witness'
    assert record['not_loaded_contact_proof'] is True and record['solver_success'] is True and record['solver_status']==0
    assert record['minimum_x_step_m']==.001 and record['maximum_x_step_m']==.002
    near(record['endpoint'],q,0);near(x,x.astype(np.float32),0)
    initial,details=audit.geometry(q,scene);assert initial['accepted']
    offset=np.asarray(record['reference_offset_local']);near(offset,details['vertex'],0)
    T0=details['pose'];origin=T0[:3,3]+T0[:3,:3]@offset
    g,d=audit.geometry(x,scene);assert g['accepted'];T=d['pose'];point=T[:3,3]+T[:3,:3]@offset;delta=point-origin
    near(record['reference_delta_xyz_m'],delta,2e-9);assert .001-1e-7<=delta[0]<=.002+1e-7 and max(abs(delta[1:]))<=1e-7
    local=d['rotation'].T@(point-np.asarray(scene['target_xyz']));half=d['core'][:2]/2-.01;inactive_z=audit.hand.minz(x,inactive);gaps=audit.elbows.gap(x)
    inequalities=np.r_[delta[0]-.001,.002-delta[0],half-local[:2],half+local[:2],g['active_above_top_m']-.004,inactive_z-.84,gaps-.005]
    near(record['inequality_residual_m'],inequalities,2e-9);near(record['equality_residual_m'],delta[1:],2e-9);assert min(inequalities)>=-1e-7
    def guard(stored,command):
        gap=audit.elbows.gap(command)
        assert np.all(command>=audit.lo-2e-7) and np.all(command<=audit.hi+2e-7) and np.all(abs(command-q)<=audit.limits+2e-7) and max(abs(command-q))<=.0550002 and min(gap)>=.005-2e-7
        assert stored['accepted'] is True and stored['first'] is False
        assert stored['checks']==dict(joint_bounds=True,measured_step=True,previous_slew=True,nominal_margin=True,first_zero=True)
        near(stored['command'],command,0);near(stored['current'],q,0);near(stored['previous'],q,0);near(stored['gaps_m'],gap,2e-9)
    guard(record['final_guard'],x)
    count=max(1,int(np.ceil(max(abs(x-q)/(audit.limits*.25)))))
    assert len(record['path'])==count
    for i,item in enumerate(record['path'],1):
        command=q+(x-q)*i/count;near(item['command'],command,1e-12)
        actual,_=audit.geometry(command,scene);assert actual['accepted'];audit.compare_geometry(item['scene_check'],actual);guard(item['final_guard'],command)
    return dict(passed=True,independent_reference_delta_xyz_m=delta.tolist(),sampled_path_points=count,minimum_hand_parcel_gap_m=min(g['hand_parcel_gaps_m'].values()),elbow_gaps_m=gaps.tolist(),not_loaded_contact_proof=True)
