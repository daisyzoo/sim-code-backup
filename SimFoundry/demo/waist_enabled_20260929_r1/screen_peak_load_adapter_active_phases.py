"""One-step recorded-state adapter screen for top_press/top_push pairs.
Transitions that leave active contact remain excluded; the separate original
controller fixture checks their reset semantics, not a physical counterfactual.
"""
from pathlib import Path
import sys
import json
import hashlib
import datetime
import collections
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W.parents[1]))
from peak_load_control_adapter import PeakLoadControl

ep=Path(sys.argv[1]).resolve()
hist=json.loads((ep/'SUBSTEP_LOAD_HISTORY.json').read_text())
fr=json.loads((ep/'frontal_bypass.json').read_text())
assert fr['plan']['top_recontact']['desired_vertical_load_n']==5.
assert fr['plan']['top_recontact']['load_bias_min_m']==-.006
rows={r['step']:r for r in fr['rows']};history={r['action_step']:r for r in hist['rows']}
checked=[];excluded=[];unreproduced=[]
for t,now in rows.items():
    prev=rows.get(t-1)
    if prev is None or prev['mode'] not in ('top_press','top_push') or now['mode'] not in ('top_press','top_push'):
        excluded.append(t);continue
    old=prev['contact_load'];actual=now['contact_load'];observed=history[t-1]['vertical_load_n']
    assert abs(actual['observed_vertical_load_n']-observed[-1])<1e-5
    filtered=.25*actual['observed_vertical_load_n']+.75*old['filtered_vertical_load_n']
    bias=max(-.006,min(.025,old['stored_z_bias_m']+max(-.0005,min(.003,.0008*(filtered-5.)))))
    if abs(filtered-actual['filtered_vertical_load_n'])>1e-10 or abs(bias-actual['stored_z_bias_m'])>1e-12:
        unreproduced.append(dict(step=t,previous_mode=prev['mode'],mode=now['mode'],
                                 expected_filter_n=filtered,actual=actual,expected_bias_m=bias))
        continue
    controller=PeakLoadControl(5.,bias_m=old['stored_z_bias_m'],
                               filtered_n=old['filtered_vertical_load_n'],min_bias_m=-.006)
    controller.observe(action_step=t,after_action_step=t-1,vertical_load_n=observed)
    result=controller.update(actual['observed_vertical_load_n'],True)
    assert result['filtered_vertical_load_n']==filtered
    assert abs(result['peak_bias_guard']['proposed_bias_m']-bias)<1e-12
    assert 0<=controller.bias_m-bias<=.000500000001
    checked.append(dict(step=t,previous_mode=prev['mode'],mode=now['mode'],
                         parent_bias_m=bias,adapter_bias_m=controller.bias_m,
                         held=result['peak_bias_guard']['held_negative_increment'],
                         prior_action_peak_n=max(observed)))
held=[r for r in checked if r['held']]
paths=[ep/'SUBSTEP_LOAD_HISTORY.json',ep/'frontal_bypass.json',Path(__file__),
       W/'peak_load_control_adapter.py',W/'peak_load_bias_guard.py',
       W.parents[1]/'simfoundry/data/contact_load_control.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,
         episode=ep.name,checked_active_pairs=len(checked),
         phase_pair_counts=dict(collections.Counter(r['previous_mode']+'->'+r['mode'] for r in checked)),
         held_negative_increment_count=len(held),held_steps=[r['step'] for r in held],
         held_phase_pairs=dict(collections.Counter(r['previous_mode']+'->'+r['mode'] for r in held)),
         excluded_steps=excluded,parent_reproduction_failures=unreproduced,rows=checked,
         physical_validation=False,controller_installed=False,training_ready=False,
         source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
dest=ep/'PEAK_LOAD_ADAPTER_ACTIVE_PHASE_SCREEN.json';assert not dest.exists()
dest.write_text(json.dumps(out,indent=2))
print(json.dumps({k:out[k] for k in ['episode','checked_active_pairs','phase_pair_counts',
                 'held_negative_increment_count','held_steps','held_phase_pairs','parent_reproduction_failures']}))
