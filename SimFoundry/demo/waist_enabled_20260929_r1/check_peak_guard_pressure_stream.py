"""Independent pressure stream and fault checks; synthetic controller phases.
Contact inputs come from an actual reference episode; no new physics is run.
"""
from pathlib import Path
from types import SimpleNamespace
import copy
import datetime
import hashlib
import json
import sys
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parents[1]))
from peak_load_update_trace import TracedPeakLoadControl
from audit_peak_guard_pressure import independent_loads,verify_stream
ep=W/'substep_reference03_groups_r1/case_840001/layout_840001_push_box_to_bin'
with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
actual=independent_loads(a,meta,'push_box_to_bin',1200)
hist=json.loads((ep/'SUBSTEP_LOAD_HISTORY.json').read_text())
assert all(actual[r['action_step']]==r['vertical_load_n'] for r in hist['rows'])
n=31;loads={t:actual[300+t] for t in range(n)}
c=TracedPeakLoadControl(5.,min_bias_m=-.006)
owner=SimpleNamespace(load=c,top_mode='top_push');c.bind_owner(owner)
fr=[];finals=[]
for t in range(1,n):
    owner.top_mode='top_lift' if t==7 else 'top_push'
    if t==7:c.bias_m=0.
    c.observe(action_step=t,after_action_step=t-1,vertical_load_n=loads[t-1])
    result=c.update(loads[t-1][-1],owner.top_mode=='top_push')
    f=dict(step=t,mode=owner.top_mode,contact_load=copy.deepcopy(result))
    if t in (11,12):
        c.bias_m=0.;owner.top_mode='top_descend';f['mode']='top_descend'
        if t==11:f['contact_load'].update(applied_z_bias_m=0.,stored_z_bias_m=0.)
        else:f['region_approach_active']=True
    fr.append(f)
    finals.append(dict(step=t,mode=f['mode'],top_mode=owner.top_mode,bias_m=c.bias_m,
                       filtered_n=c.filtered_n,pressure_update_count=len(c.updates)))
pressure=dict(rows=c.updates,final_control_states=finals,executed_action_count=n,wait=False,training_ready=False)
frontal=dict(rows=fr)
out=verify_stream(pressure,frontal,loads,frames=n,wait=False)
assert out['held_negative_increments']>0 and 12 in out['original_region_returned_bias_before_reset']
checks=['real1200_interval_scalar_extraction_matches_independent_history','synthetic31_frame_pressure_and_zero_reset_stream']
def reject(name,fn):
    try:fn()
    except (AssertionError,ValueError,KeyError):checks.append(name)
    else:raise AssertionError(name)
for name,mutate in [
    ('missing_update',lambda p:p['rows'].pop()),
    ('duplicate_update',lambda p:p['rows'].append(copy.deepcopy(p['rows'][-1]))),
    ('stale_substep_identity',lambda p:p['rows'][0]['preceding_observation'].update(observed_after_action_step=1)),
    ('missing_final_control_frame',lambda p:p['final_control_states'].pop()),
    ('forged_final_counter',lambda p:p['final_control_states'][-1].update(pressure_update_count=0)),
    ('changed_filter_between_updates',lambda p:p['rows'][1]['before'].update(filtered_n=99.)),
    ('unexplained_nonzero_bias_reset',lambda p:p['final_control_states'][10].update(bias_m=.02)),
    ('forged_peak',lambda p:p['rows'][0]['preceding_observation'].update(previous_action_peak_n=99.)),
    ('changed_frame_count',lambda p:p.update(executed_action_count=30))]:
    bad=copy.deepcopy(pressure);mutate(bad)
    reject(name,lambda:verify_stream(bad,frontal,loads,frames=n,wait=False))
badfr=copy.deepcopy(frontal);badfr['rows'][11].pop('region_approach_active')
reject('unjustified_stale_return_field',lambda:verify_stream(pressure,badfr,loads,frames=n,wait=False))
badloads=copy.deepcopy(loads);badloads[0][0]=99.
reject('actual_substep_load_mismatch',lambda:verify_stream(pressure,frontal,badloads,frames=n,wait=False))
wait=dict(rows=[],final_control_states=[],executed_action_count=70,wait=True,training_ready=False)
assert verify_stream(wait,None,{},frames=70,wait=True)['passed'];checks.append('wait_has_no_pressure_activity')
badwait=copy.deepcopy(wait);badwait['rows']=[pressure['rows'][0]]
reject('wait_pressure_update_rejected',lambda:verify_stream(badwait,None,{},frames=70,wait=True))
files=[Path(__file__),W/'audit_peak_guard_pressure.py',W/'audit_peak_load_update_math.py',
       W/'peak_load_update_trace.py',W/'peak_load_control_adapter.py',W/'peak_load_bias_guard.py',
       ep/'substep_contacts.npz',ep/'SUBSTEP_CONTACT_RECORDING.json',ep/'SUBSTEP_LOAD_HISTORY.json']
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
            scope=__doc__,checks=checks,synthetic_stream_result=out,
            source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            physical_validation=False,training_ready=False)
dest=W/'PEAK_GUARD_PRESSURE_STREAM_CHECK.json';assert not dest.exists()
dest.write_text(json.dumps(report,indent=2));print('PASS',len(checks),'checks; synthetic phases, real contact inputs')
