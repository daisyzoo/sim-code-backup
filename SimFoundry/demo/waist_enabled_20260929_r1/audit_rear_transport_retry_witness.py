"""Independent witness and exact one-retry metadata/feasible-seed verification.
No candidate solver import; original final scene/path verification remains.
"""
import numpy as np
from audit_rear_transport_witness import verify_witness
from audit_unloaded_wrist_prior_live import near

def verify_retry_witness(audit,record,*,endpoint,scene,retry_enabled=False):
    assert type(retry_enabled) is bool
    result=verify_witness(audit,record,endpoint=endpoint,scene=scene)
    meta=record.get('feasible_endpoint_retry')
    if not retry_enabled:
        assert meta is None
        return result
    assert isinstance(meta,dict) and meta['enabled'] is True and type(meta['attempted']) is bool
    assert type(meta['maximum_extra_retries']) is int and meta['maximum_extra_retries']==1
    assert meta['original_ftol']==1e-12 and meta['original_maxiter']==220 and meta['original_problem_unchanged'] is True
    prior=meta['original_attempt']
    if not meta['attempted']:
        assert prior is None
        return dict(result,retry_attempted=False)
    assert prior['solver_status']==9 and prior['solver_success'] is False and prior['iterations']==220 and prior['accepted'] is False
    q=np.asarray(endpoint,float);x=np.asarray(prior['candidate'],float);assert x.shape==(11,) and np.isfinite(x).all();near(x,x.astype(np.float32),0)
    assert np.all(x>=audit.lo-2e-7) and np.all(x<=audit.hi+2e-7) and np.all(abs(x-q)<=audit.limits+2e-7) and max(abs(x-q))<=.0550002
    initial,zero=audit.geometry(q,scene);g,d=audit.geometry(x,scene);assert initial['accepted'] and g['accepted']
    offset=np.asarray(record['reference_offset_local']);near(offset,zero['vertex'],0);T0=zero['pose'];T=d['pose'];delta=T[:3,3]+T[:3,:3]@offset-(T0[:3,3]+T0[:3,:3]@offset)
    local=d['rotation'].T@(T[:3,3]+T[:3,:3]@offset-np.asarray(scene['target_xyz']));half=d['core'][:2]/2-.01;inactive='left' if scene['side']=='right' else 'right';gaps=audit.elbows.gap(x)
    iv=np.r_[delta[0]-.001,.002-delta[0],half-local[:2],half+local[:2],g['active_above_top_m']-.004,audit.hand.minz(x,inactive)-.84,gaps-.005]
    near(prior['inequality_residual_m'],iv,2e-9);near(prior['equality_residual_m'],delta[1:],2e-9);assert min(iv)>=-1e-7 and max(abs(delta[1:]))<=1e-7
    return dict(result,retry_attempted=True,original_failed_seed_geometry_passed=True,original_failure_status=9,extra_initializations=1)
