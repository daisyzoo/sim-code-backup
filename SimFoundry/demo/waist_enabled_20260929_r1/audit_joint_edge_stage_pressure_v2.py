"""Independent candidate pressure-file audit, with unchanged observer coverage.
Actual phase/reset/action validity remains covered by the original native audits.
This audit recomputes contact loads with scalar loops, not the candidate reader.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import numpy as np
from audit_peak_load_update_math import verify_event
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def independent_loads(arrays, metadata, task, frames):
    side,actor=('right','parcel_box') if task=='push_box_to_bin' else ('left','mailer')
    labels=metadata['shape_labels'];stride=24+metadata['expected_manager_steps'];out={}
    assert len(arrays['action_step'])==frames*stride
    offsets=arrays['contact_offsets']
    for t in range(frames):
        base=t*stride;ticks=arrays['substep_tick'][base:base+stride];values=[]
        assert np.all(arrays['action_step'][base:base+stride]==t)
        for tick in range(1,25):
            matches=np.flatnonzero(ticks==tick);assert len(matches)>0
            j=base+int(matches[0]);load=0.
            for k in range(int(offsets[j]),int(offsets[j+1])):
                names=[labels[int(i)] for i in arrays['shape_ids'][k]]
                if any(side+'_wrist_roll' in n for n in names) and any('/'+actor+'/' in n for n in names):
                    value=float(arrays['force_torque_world'][k,2]);assert math.isfinite(value)
                    load+=abs(value)
            values.append(load)
        out[t]=values
    return out


def verify_stream(pressure, frontal, loads, *, frames, wait):
    def near(a,b):assert math.isfinite(a) and math.isfinite(b) and abs(a-b)<1e-12,(a,b)
    def unique(rows,key):
        d={r[key]:r for r in rows};assert len(d)==len(rows),'duplicate steps';return d
    assert pressure['training_ready'] is False and pressure['executed_action_count']==frames
    assert type(pressure['wait']) is bool and pressure['wait']==wait
    updates=unique(pressure['rows'],'action_step');finals=unique(pressure['final_control_states'],'step')
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
            if abs(load['stored_z_bias_m']-final['bias_m'])>1e-12:
                assert final['bias_m']==0. and f.get('region_approach_active') is True
                stale_return.append(t)
            update_count+=1;records.append(result)
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
                original_region_returned_bias_before_reset=stale_return,training_ready=False)


def audit(ep):
    from audit_joint_edge_stage_contacts import audit as audit_contacts
    ep=Path(ep).resolve();observer=audit_contacts(ep)
    with np.load(ep/'raw.npz') as z:
        task=str(z['task_id']);n=len(z['q'])
    assert task in ('push_box_to_bin','nudge_mailer_to_bin','wait_no_package')
    wait=task=='wait_no_package';assert n==(70 if wait else 1200),'short attempt cannot pass pressure audit'
    p=json.loads((ep/'peak_load_updates.json').read_text())
    fr=None if wait else json.loads((ep/'frontal_bypass.json').read_text())
    meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
    with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
    loads={} if wait else independent_loads(a,meta,task,n)
    out=verify_stream(p,fr,loads,frames=n,wait=wait)
    native=ep/('WAIT_STABILITY_AUDIT.json' if wait else 'JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json')
    native_report=json.loads(native.read_text());assert native_report['passed'] is True
    files=['peak_load_updates.json','raw.npz','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz',native.name]
    if not wait:files.append('frontal_bypass.json')
    out.update(scope=__doc__,independent_substep_audit=observer,original_native_phase_audit_sha256=sha(native),
               source_sha256={n:sha(ep/n) for n in files},auditor_sha256=sha(__file__),
               math_auditor_sha256=sha(Path(__file__).with_name('audit_peak_load_update_math.py')))
    return out


if __name__=='__main__':
    ep=Path(sys.argv[1]);out=audit(ep);p=ep/'JOINT_EDGE_STAGE_PRESSURE_V2_AUDIT.json';assert not p.exists()
    p.write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k not in ['records','independent_substep_audit','source_sha256','scope']}))
