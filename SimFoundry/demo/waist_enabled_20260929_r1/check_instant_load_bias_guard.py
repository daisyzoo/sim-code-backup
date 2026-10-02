"""Uninstalled guard boundary checks and one-step replay at actual pressure states.
Each observed pre-state is independent. Do not accumulate modified states or
infer task success. All four completed candidate pushes remain in this screen.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from instant_load_bias_guard import guard_instantaneous_load
from audit_peak_guard_pressure import verify_stream
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=dict(desired_n=5.,previous_bias_m=-.001,proposed_bias_m=-.0015,previous_action_peak_n=6.,previous_action_final_n=5.,active=True,action_step=9,observed_after_action_step=8,observed_solver_substeps=24)
checks=[]
def check(name,patch,expected=None,reject=False):
    try:r=guard_instantaneous_load(**(base|patch))
    except ValueError:assert reject,name
    else:
        assert not reject,name
        assert r['guarded_bias_m']==expected,(name,r)
    checks.append(name)
check('target_equality_holds_downward',{},-.001)
check('below_target_keeps_downward',dict(previous_action_final_n=4.999999),-.0015)
check('above_target_holds_downward',dict(previous_action_final_n=5.5),-.001)
check('upward_relief_not_suppressed',dict(proposed_bias_m=.002),.002)
check('inactive_unchanged',dict(active=False),-.0015)
check('peak_guard_retained_when_final_zero',dict(previous_action_peak_n=17.,previous_action_final_n=0.),-.001)
check('no_load_keeps_contact_seeking',dict(previous_action_peak_n=0.,previous_action_final_n=0.),-.0015)
check('lower_saturation_unchanged',dict(previous_bias_m=-.006,proposed_bias_m=-.006),-.006)
check('upper_saturation_unchanged',dict(previous_bias_m=.025,proposed_bias_m=.025),.025)
for name,patch in [('nan_final',dict(previous_action_final_n=float('nan'))),('infinite_final',dict(previous_action_final_n=float('inf'))),('negative_final',dict(previous_action_final_n=-1.)),('impossible_final_over_peak',dict(previous_action_final_n=7.)),('stale_observation',dict(observed_after_action_step=7)),('future_observation',dict(observed_after_action_step=9)),('missing_substep',dict(observed_solver_substeps=23)),('altered_load_target',dict(desired_n=5.1)),('altered_downward_bound',dict(min_bias_m=-.01)),('oversized_step',dict(proposed_bias_m=-.002))]:check(name,patch,reject=True)
rows=[];bound=[]
for case,task in [(840001,'push_box_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
    ep=W/'peak_guard_groups_r1'/f'case_{case}'/f'layout_{case}_{task}'
    h=json.loads((ep/'PEAK_GUARD_LOAD_HISTORY.json').read_text());assert h['independent_audit']['passed']
    for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
    loads={x['action_step']:x['vertical_load_n'] for x in h['rows']};p=json.loads((ep/'peak_load_updates.json').read_text());fr=json.loads((ep/'frontal_bypass.json').read_text())
    verify_stream(p,fr,loads,frames=1200,wait=False)
    q=json.loads((ep/'quality.json').read_text());changes=[];upward=inactive=overlap=0
    for e in p['rows']:
        before=e['before'];values=loads[e['action_step']-1];filt=.25*e['observed_vertical_load_n']+.75*before['filtered_n'];prior=before['bias_m']
        proposal=max(-.006,min(.025,prior+max(-.0005,min(.003,.0008*(filt-5.))))) if e['active'] else prior
        r=guard_instantaneous_load(desired_n=5.,previous_bias_m=prior,proposed_bias_m=proposal,previous_action_peak_n=max(values),previous_action_final_n=values[-1],active=e['active'],action_step=e['action_step'],observed_after_action_step=e['action_step']-1,observed_solver_substeps=24)
        # Independent truth table; no call to either helper in the reference.
        peak_hold=e['active'] and max(values)>10. and proposal<prior
        final_hold=e['active'] and values[-1]>=5. and proposal<prior
        expected=prior if (peak_hold or final_hold) else proposal
        assert r['guarded_bias_m']==expected and r['held_by_final_sample']==final_hold and r['held_by_peak']==peak_hold
        if proposal>=prior:assert r['guarded_bias_m']==proposal;upward+=1
        if not e['active']:assert r['guarded_bias_m']==e['after']['bias_m'];inactive+=1
        overlap+=bool(final_hold and peak_hold)
        delta=r['guarded_bias_m']-e['after']['bias_m'];assert -1e-12<=delta<=.000500000001
        if delta>1e-12:changes.append(dict(step=e['action_step'],phase=e['phase_at_update'],final_load_n=values[-1],filtered_n=filt,peak_n=max(values),actual_bias_m=e['after']['bias_m'],one_step_candidate_bias_m=expected,local_difference_mm=1000*delta))
    rows.append(dict(episode=ep.name,quality_passed=q['passed'],events_checked=len(p['rows']),additional_holds=len(changes),overlap_peak_final=overlap,upward_or_equal_verified=upward,inactive_verified=inactive,changes=changes))
    bound.extend(ep/n for n in ['PEAK_GUARD_LOAD_HISTORY.json','peak_load_updates.json','frontal_bypass.json','quality.json'])
bound.extend([Path(__file__),W/'instant_load_bias_guard.py',W/'peak_load_bias_guard.py',W/'audit_peak_guard_pressure.py',W/'audit_peak_load_update_math.py'])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,boundary_checks=checks,rows=rows,controller_installed=False,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in bound},limitations=['Final-load condition also changes successful trajectories.','A held bias may prevent needed reacquisition or remain limited by waypoint slew.','Future full-group physical comparison and original native audits remain mandatory.'])
p=W/'INSTANT_LOAD_BIAS_GUARD_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,boundary_checks=len(checks),physical_validation=False,rows=[{k:v for k,v in r.items() if k!='changes'} for r in rows]),indent=2))
