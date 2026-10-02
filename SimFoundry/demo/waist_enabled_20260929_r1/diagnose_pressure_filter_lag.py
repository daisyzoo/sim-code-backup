"""Observed downward pressure updates despite final load meeting the 5N target.
Reference coverage is consecutive unchanged top_press/top_push rows only; native
candidate traces cover actual pressure updates directly. No counterfactual state
is accumulated, no controller changed, and no task benefit is predicted.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep, traced):
    history_name='PEAK_GUARD_LOAD_HISTORY.json' if traced else 'SUBSTEP_LOAD_HISTORY.json'
    history=json.loads((ep/history_name).read_text())
    for name,h in history['source_sha256'].items():assert sha(ep/name)==h,name
    assert history['independent_audit']['passed'] is True
    fr=json.loads((ep/'frontal_bypass.json').read_text())['rows'];by_step={x['step']:x for x in fr}
    loads={x['action_step']:x['vertical_load_n'] for x in history['rows']};events=[];checked=[];unmatched=[]
    if traced:
        from audit_peak_guard_pressure import verify_stream
        p=json.loads((ep/'peak_load_updates.json').read_text())
        proof=verify_stream(p,dict(rows=fr),loads,frames=1200,wait=False)
        records=[dict(step=e['action_step'],active=e['active'],before=e['before'],after=e['after'],load=e['observed_vertical_load_n'],held=e['returned']['peak_bias_guard']['held_negative_increment']) for e in p['rows']]
        coverage='all actual pressure update events (active and inactive)'
    else:
        records=[];proof=None;coverage='consecutive same top_press/top_push phase with recorded contact_load in both rows'
        for prev,cur in zip(fr,fr[1:]):
            if cur['step']!=prev['step']+1 or prev['mode']!=cur['mode'] or cur['mode'] not in ('top_press','top_push') or any('contact_load' not in x for x in (prev,cur)):continue
            before=prev['contact_load'];after=cur['contact_load']
            records.append(dict(step=cur['step'],active=True,before=dict(bias_m=before['stored_z_bias_m'],filtered_n=before['filtered_vertical_load_n']),after=dict(bias_m=after['stored_z_bias_m'],filtered_n=after['filtered_vertical_load_n']),load=after['observed_vertical_load_n'],held=False))
    for e in records:
        t=e['step'];before=e['before'];after=e['after'];sample=loads[t-1]
        assert abs(sample[-1]-e['load'])<1e-5
        filt=.25*e['load']+.75*before['filtered_n']
        assert abs(after['filtered_n']-filt)<1e-12,(ep,t,'filter')
        proposed=max(-.006,min(.025,before['bias_m']+max(-.0005,min(.003,.0008*(filt-5.))))) if e['active'] else before['bias_m']
        actual=after['bias_m'];expected=before['bias_m'] if e['held'] else proposed
        if abs(actual-expected)>1e-12:
            unmatched.append(dict(step=t,mode=by_step[t]['mode'],original_proposal_m=proposed,recorded_bias_m=actual,reason='outside stable pressure-only transition assumption'))
            continue
        checked.append(t)
        if e['active'] and actual<before['bias_m']-1e-12 and e['load']>=5.:
            events.append(dict(step=t,phase=by_step[t]['mode'],last_load_n=e['load'],filtered_n=filt,previous_peak_n=max(sample),previous_mean_n=float(np.mean(sample)),before_bias_m=before['bias_m'],after_bias_m=actual,downward_increment_mm=(before['bias_m']-actual)*1000,previous_action=t-1))
    files=[ep/history_name,ep/'frontal_bypass.json',ep/'quality.json']
    if traced:files.append(ep/'peak_load_updates.json')
    q=json.loads((ep/'quality.json').read_text())
    return dict(episode=ep.name,run=ep.parent.parent.name,quality_passed=q['passed'],coverage=coverage,pressure_rows_considered=len(records),reproduced_rows=len(checked),unmatched_rows=unmatched,downward_despite_final_at_target_count=len(events),sum_local_downward_increments_mm=sum(x['downward_increment_mm'] for x in events),events=events,source_sha256={str(p):sha(p) for p in files},training_ready=False)

if __name__=='__main__':
    cases=[(p.parent,False) for p in sorted((W/'substep_reference03_groups_r1').glob('case_*/layout_*/SUBSTEP_LOAD_HISTORY.json'))]
    assert len(cases)==8
    cases += [(p.parent,True) for p in sorted((W/'peak_guard_groups_r1').glob('case_*/layout_*/PEAK_GUARD_LOAD_HISTORY.json'))]
    assert len(cases)==10,'This diagnostic snapshot explicitly covers reference8 plus candidate first2'
    rows=[inspect(ep,traced) for ep,traced in cases]
    out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,script_sha256=sha(__file__),parent_pressure_source_sha256=sha(W.parents[1]/'simfoundry/data/contact_load_control.py'),training_ready=False,limitations=['Sums are local observed increments, not accumulated counterfactual bias or predicted progress.','Final contact magnitude meeting target is not proof of stable net force, torque, or full-interval support.','A new downward hold would change successful reference trajectories too; full physical groups remain necessary.'])
    p=W/'peak_guard_groups_r1/PRESSURE_FILTER_LAG_FIRST_TWO.json';assert not p.exists();p.write_text(json.dumps(out,indent=2))
    for row in rows:print(json.dumps({k:row[k] for k in ['run','episode','quality_passed','pressure_rows_considered','reproduced_rows','unmatched_rows','downward_despite_final_at_target_count','sum_local_downward_increments_mm']}))
