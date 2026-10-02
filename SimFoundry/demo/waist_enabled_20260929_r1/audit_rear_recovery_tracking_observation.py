"""Independent causal residual witness checks; never imports candidate observation.
The native caller must supply the actual preceding executed record and raw arrays.
"""
import numpy as np

def verify_observation(verifier, *, record, previous_record, current, previous):
    row=record['parent_row'];coord=record['parent_coordinate'];t=record['step']
    witness=record['recovery'].get('tracking_feedback')
    assert isinstance(witness,dict),'Missing explicit tracking decision'
    if not previous_record or previous_record.get('kind')!='loaded_recovery' or previous_record.get('step')!=t-1:
        assert witness==dict(accepted=False,reason='no_previous_executed_recovery')
        return np.zeros(3)
    p=previous_record;c=p['commit'];phase=p['phase_committed']
    assert c['kind']=='committed_recovery_reference' and c['step']==t-1 and c['final_guard']['accepted'] is True
    assert phase['active'] is True and phase['last_step']==t-1
    assert np.array_equal(previous,p['emitted_command']) and np.array_equal(previous,c['final_guard']['command'])
    guarded=(row['mode']!='top_push' or row.get('route_stop_reason') or row.get('release_reason') or not row.get('rear_cop_centering',{}).get('override') or coord.get('region_joint_override') or coord.get('terminal_joint_hold') or row['recontacts']!=p['parent_row']['recontacts'])
    if guarded:
        assert witness==dict(accepted=False,reason='original_mode_contact_or_bout_guard')
        return np.zeros(3)
    side=coord['active_side'];assert side==p['parent_coordinate']['active_side'];offset=np.asarray(row['control_offset_local'],float)
    def point(q):
        T=verifier.hand.fk(q,side);return T[:3,3]+T[:3,:3]@offset
    measured=point(current);nominal=point(previous);bias=measured-nominal
    assert np.max(abs(measured-np.asarray(row['observed_support_xyz'])))<=2e-6
    for key,value in [('current_q',current),('previous_emitted_command',previous),('control_offset_local',offset)]:assert np.array_equal(witness[key],value),key
    for key,value in [('measured_reference_xyz',measured),('previous_nominal_reference_xyz',nominal),('observed_residual_xyz_m',bias)]:assert np.max(abs(np.asarray(witness[key])-value))<2e-10,key
    assert witness['step']==t and witness['previous_step']==t-1 and witness['side']==side
    assert witness['maximum_bias_xy_m']==[.0015,.0005]
    # Validate the logged double-precision threshold and independently rebuilt
    # residual separately; no widening of the declared model domain.
    logged=np.asarray(witness['observed_residual_xyz_m']);accepted=bool(abs(logged[0])<=.0015 and abs(logged[1])<=.0005)
    assert witness['accepted'] is accepted
    assert witness['reason']==('previous_actual_tracking_residual' if accepted else 'outside_tracking_domain')
    correction=[float(logged[0]),float(logged[1]),0.] if accepted else [0.,0.,0.]
    assert witness['correction_xyz_m']==correction
    if not accepted:return np.zeros(3)
    bias[2]=0.
    return bias
