"""Independent post-waypoint pressure transition check, no controller imports.
This covers only the declared final recovery boundary. Full original substep,
pressure mathematics, source, action, phase and physical quality audits remain.
"""
import math
import numpy as np

def verify(final, row, record, *, current, executed_command, side):
    def finite(value):
        if isinstance(value,dict):
            for v in value.values():finite(v)
        elif isinstance(value,(list,tuple)):
            for v in value:finite(v)
        elif isinstance(value,(float,np.floating)):assert math.isfinite(value),'nonfinite trace'
    finite(final);finite(record)
    base={'step','mode','top_mode','bias_m','filtered_n','pressure_update_count'}
    assert set(final)==base|{'before_final_recovery','final_recovery_transition'}
    before=final['before_final_recovery'];assert set(before)==base
    step=record['step'];assert type(step) is int and step==row['step']==before['step']==final['step']
    assert side in ('left','right')
    for key in ['enabled','selected','applied','requires_recovery','recovery_committed']:assert record[key] is True,key
    assert record['requires_stop'] is False and record['training_ready'] is False
    assert record['reason']=='verified_hold_then_original_recontact'
    assert record['proposal']['requires_recovery'] is True
    assert row['mode']=='top_push' and row['route_stage']=='lateral_y'
    assert not row.get('route_stop_reason') and not row.get('release_reason')
    q=np.asarray(current,float);action=np.asarray(executed_command,float)
    assert q.shape==action.shape==(11,) and np.isfinite(q).all() and np.isfinite(action).all()
    assert np.array_equal(action,q.astype(np.float32).astype(float))
    assert np.array_equal(record['output_command'],action)
    request=record['recovery_request'];assert request['source_step']==step and request['side']==side
    assert request['reason']=='front_nonreversing_contact_recovery'
    point=np.asarray(request['observed_support_xyz'],float)
    assert point.shape==(3,) and np.isfinite(point).all() and np.array_equal(point,row['observed_support_xyz'])
    event=record['recovery_transition'];assert event==final['final_recovery_transition']
    assert set(event)=={'step','before','after','reason','observed_support_xyz'}
    assert event['step']==step and event['reason']==request['reason'] and np.array_equal(event['observed_support_xyz'],point)
    a,b=event['before'],event['after'];assert set(a)==set(b)=={'top_mode','recontacts','lost_contact_steps'}
    for state in [a,b]:
        for k in ['recontacts','lost_contact_steps']:assert type(state[k]) is int and state[k]>=0
    assert a['top_mode']=='top_push' and a['recontacts']==row['recontacts']
    assert b==dict(top_mode='top_lift',recontacts=a['recontacts']+1,lost_contact_steps=0)
    assert before['mode']==before['top_mode']==row['mode']
    assert type(before['pressure_update_count']) is int and before['pressure_update_count']>0
    assert -.006<=before['bias_m']<=.025 and before['filtered_n']>=0
    expected=dict(before,top_mode='top_lift',bias_m=0.)
    assert {k:final[k] for k in base}==expected,'post-commit pressure state mismatch'
    return dict(passed=True,step=step,pressure_filter_retained=True,bias_reset_to_zero=True,recontact_increment=1,training_ready=False)
