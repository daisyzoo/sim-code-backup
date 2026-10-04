"""Original full pressure math plus explicit post-waypoint recovery boundaries.
No optimization/controller imports. Caller supplies independently extracted24
loads and source-bound raw q/actions/final guards. This is not source/phase or
geometric command certification, nor data/physical admission on its own.
"""
import math
import numpy as np
from audit_peak_load_update_math import verify_event
from audit_front_normal_pressure_finalization_v1 import verify as verify_final
from audit_front_effective_height_r1_v1_stage_pressure import independent_loads

def verify_stream(pressure, frontal, loads, *, frames, wait, enabled=False, normal_records=None, current=None, actions=None, side=None, final_guards=None):
    def near(a,b):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<1e-12,(a,b)
    def unique(rows,key):
        d={r[key]:r for r in rows};assert len(d)==len(rows),'duplicate steps';return d
    assert pressure['training_ready'] is False and pressure['executed_action_count']==frames
    assert type(pressure['wait']) is bool and pressure['wait']==wait
    updates=unique(pressure['rows'],'action_step');finals=unique(pressure['final_control_states'],'step')
    assert type(enabled) is bool
    transitions=[]
    if enabled:
        assert type(normal_records) is list and side in ('left','right')
        nr=unique(normal_records,'step');assert list(nr)==list(range(frames))
        q=np.asarray(current,float);u=np.asarray(actions,float)
        assert q.shape==u.shape==(frames,11) and np.isfinite(q).all() and np.isfinite(u).all()
        fg=unique(final_guards,'step');assert list(fg)==list(range(frames))
        for t,r in nr.items():
            assert type(t) is int and r['enabled'] is True
            assert r['requires_stop'] is False and r['training_ready'] is False
            for k in ['applied','selected','requires_recovery']:assert type(r[k]) is bool
            out=np.asarray(r['output_command'],float);assert out.shape==(11,) and np.isfinite(out).all() and np.array_equal(out,u[t])
            g=fg[t];assert g['accepted'] is True and np.array_equal(g['command'],u[t]) and np.array_equal(g['current'],q[t])
            assert np.array_equal(g['previous'],u[t-1] if t else np.zeros(11))
            if r['requires_recovery']:
                assert not wait and t>0 and t in finals
            else:
                assert 'recovery_transition' not in r and 'recovery_committed' not in r
                if t in finals:assert 'before_final_recovery' not in finals[t] and 'final_recovery_transition' not in finals[t]
    else:
        assert normal_records is None and final_guards is None
        assert all('before_final_recovery' not in f and 'final_recovery_transition' not in f for f in finals.values())

    if wait:
        assert not updates and not finals and frontal is None
        return dict(passed=True,wait=True,pressure_updates=0,control_frames=0,training_ready=False)
    fr=unique(frontal['rows'],'step')
    assert list(finals)==list(fr)==list(range(1,frames)),'full ordered control frame coverage required'
    assert list(updates)==sorted(updates) and set(updates)=={t for t,f in fr.items() if 'contact_load' in f}
    assert set(loads)==set(range(frames))
    previous_bias=0.;previous_filter=0.;update_count=0;records=[];reset_before=[];reset_after=[];stale_return=[]
    for t,final in finals.items():
        f=fr[t];assert final['mode']==f['mode']
        decision_final=final
        if enabled and nr[t]['requires_recovery']:
            transition=verify_final(final,f,nr[t],current=q[t],executed_command=u[t],side=side)
            transitions.append(transition);decision_final=final['before_final_recovery']
            # The next pressure update consumes the post-commit top_lift.
            # A latched route guard may return before any pressure update.
            if t+1<frames:
                nf=fr[t+1]
                if t+1 in updates:
                    assert updates[t+1]['phase_at_update']=='top_lift' and updates[t+1]['active'] is False
                    assert updates[t+1]['before']['bias_m']==0.
                    assert nf['recontacts']==nr[t]['recovery_transition']['after']['recontacts']
                else:assert nf.get('route_stop_reason') and nf['mode']=='front_guard_lift'

        assert math.isfinite(final['bias_m']) and -.006<=final['bias_m']<=.025
        current_bias=previous_bias;current_filter=previous_filter
        if t in updates:
            event=updates[t];near(event['before']['filtered_n'],previous_filter)
            if abs(event['before']['bias_m']-previous_bias)>1e-12:
                assert event['before']['bias_m']==0.,'original external resets must clear bias'
                reset_before.append(t)
            result=verify_event(event,action_step=t,previous_action_loads=loads[t-1])
            current_bias=event['after']['bias_m'];current_filter=event['after']['filtered_n']
            load=f['contact_load'];near(load['observed_vertical_load_n'],event['observed_vertical_load_n'])
            near(load['filtered_vertical_load_n'],current_filter)
            assert load['peak_bias_guard']==event['returned']['peak_bias_guard']
            # Original outer phase controllers can zero these fields or retain
            # the local update result while separately clearing stored state.
            assert load['stored_z_bias_m'] in (current_bias,0.)
            assert load['applied_z_bias_m'] in (event['returned']['applied_z_bias_m'],0.)
            if abs(load['stored_z_bias_m']-decision_final['bias_m'])>1e-12:
                assert decision_final['bias_m']==0. and f.get('region_approach_active') is True
                stale_return.append(t)
            update_count+=1;records.append(result)
        near(decision_final['filtered_n'],current_filter)
        assert math.isfinite(decision_final['bias_m']) and -.006<=decision_final['bias_m']<=.025
        assert decision_final['pressure_update_count']==final['pressure_update_count']
        near(final['filtered_n'],current_filter)
        if abs(final['bias_m']-current_bias)>1e-12:
            assert final['bias_m']==0.,'original external resets must clear bias'
            reset_after.append(t)
        assert type(final['pressure_update_count']) is int and final['pressure_update_count']==update_count
        previous_bias=final['bias_m'];previous_filter=final['filtered_n']
    return dict(passed=True,wait=False,pressure_updates=len(updates),control_frames=len(finals),
                held_negative_increments=sum(r['held_negative_increment'] for r in records),
                records=records,original_zero_resets_before_update=reset_before,
                original_zero_resets_after_update=reset_after,
                original_region_returned_bias_before_reset=stale_return,training_ready=False,**(dict(final_recovery_transitions=transitions,normal_record_frames=len(nr)) if enabled else {}))

