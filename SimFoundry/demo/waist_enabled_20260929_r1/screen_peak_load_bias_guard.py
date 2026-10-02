"""One-step old-observation screen, NOT a new trajectory or controller replay.
Only consecutive actual top_push samples with an exactly reproduced parent
integrator are compared. External phase transitions/resets are excluded and counted.
"""
from pathlib import Path
import sys,json,hashlib,datetime
from peak_load_bias_guard import guard_bias_step
p=Path(sys.argv[1]).resolve();sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();hist=json.loads((p/'SUBSTEP_LOAD_HISTORY.json').read_text());fr=json.loads((p/'frontal_bypass.json').read_text());cfg=fr['plan']['top_recontact'];desired=cfg['desired_vertical_load_n'];assert desired==5 and cfg['load_bias_min_m']==-.006
rows={x['step']:x for x in fr['rows']};history={x['action_step']:x for x in hist['rows']};checks=[];excluded=[]
for t,f in rows.items():
 prev=rows.get(t-1)
 if prev is None or prev['mode']!='top_push' or f['mode']!='top_push':excluded.append(t);continue
 old=prev['contact_load'];now=f['contact_load'];observed=history[t-1];peak=max(observed['vertical_load_n'])
 assert abs(now['observed_vertical_load_n']-observed['vertical_load_n'][-1])<1e-5
 filtered=.25*now['observed_vertical_load_n']+.75*old['filtered_vertical_load_n'];assert abs(filtered-now['filtered_vertical_load_n'])<1e-10
 original=max(-.006,min(.025,old['stored_z_bias_m']+max(-.0005,min(.003,.0008*(filtered-desired)))))
 assert abs(original-now['stored_z_bias_m'])<1e-12,(t,original,now)
 out=guard_bias_step(desired_n=desired,previous_bias_m=old['stored_z_bias_m'],proposed_bias_m=original,previous_action_peak_n=peak,active=True,action_step=t,observed_after_action_step=t-1,observed_solver_substeps=len(observed['vertical_load_n']))
 assert out['guarded_bias_m']>=original and abs(out['guarded_bias_m']-original)<=.000500000001
 if original>=old['stored_z_bias_m']:assert out['guarded_bias_m']==original
 checks.append(dict(step=t,original_bias_m=original,previous_bias_m=old['stored_z_bias_m'],**out))
changed=[x for x in checks if x['held_negative_increment']]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=p.name,checked_consecutive_top_push=len(checks),excluded_phase_transition_or_other_mode_steps=excluded,held_negative_increment_count=len(changed),held_steps=[x['step'] for x in changed],maximum_one_step_proposal_difference_m=max((x['guarded_bias_m']-x['original_bias_m'] for x in checks),default=0),rows=checks,physical_validation=False,controller_installed=False,training_ready=False,limitations=['Every proposal starts from the recorded old state; effects cannot be accumulated into a predicted trajectory.','Previous-action peak has control-rate latency; this is not an intra-substep force limiter.','Top-press and phase-transition integration have not been screened here.'],source_sha256={str(f):sha(f) for f in [Path(__file__),Path(__file__).with_name('peak_load_bias_guard.py'),p/'SUBSTEP_LOAD_HISTORY.json',p/'frontal_bypass.json']})
dest=p/'PEAK_LOAD_BIAS_GUARD_SCREEN.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['episode','checked_consecutive_top_push','held_negative_increment_count','held_steps','maximum_one_step_proposal_difference_m']},indent=2))
