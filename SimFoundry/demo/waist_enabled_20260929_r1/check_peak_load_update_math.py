"""Independent audit checked against prospective events from real old states.
These events are offline fixtures, not actual new-controller physical execution.
"""
from pathlib import Path
from types import SimpleNamespace
import copy
import datetime
import hashlib
import json
import sys
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W.parents[1]))
from peak_load_update_trace import TracedPeakLoadControl
from audit_peak_load_update_math import verify_event

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];bindings={};fault_fixture=None
for arg in sys.argv[1:]:
    ep=Path(arg).resolve()
    screen=json.loads((ep/'PEAK_LOAD_ADAPTER_ACTIVE_PHASE_SCREEN.json').read_text())
    assert not screen['parent_reproduction_failures']
    for path,h in screen['source_sha256'].items():assert sha(path)==h,path
    fr={r['step']:r for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']}
    hist={r['action_step']:r for r in json.loads((ep/'SUBSTEP_LOAD_HISTORY.json').read_text())['rows']}
    changed=0
    for row in screen['rows']:
        t=row['step'];old=fr[t-1]['contact_load'];now=fr[t]['contact_load'];loads=hist[t-1]['vertical_load_n']
        c=TracedPeakLoadControl(5.,bias_m=old['stored_z_bias_m'],filtered_n=old['filtered_vertical_load_n'],min_bias_m=-.006)
        owner=SimpleNamespace(load=c,top_mode=row['previous_mode']);c.bind_owner(owner)
        c.observe(action_step=t,after_action_step=t-1,vertical_load_n=loads)
        c.update(now['observed_vertical_load_n'],True)
        event=c.updates[0];audit=verify_event(event,action_step=t,previous_action_loads=loads)
        assert audit['held_negative_increment']==row['held']
        assert abs(audit['guarded_bias_m']-row['adapter_bias_m'])<1e-12
        changed+=int(audit['held_negative_increment'])
        if row['held'] and fault_fixture is None:fault_fixture=(copy.deepcopy(event),t,loads)
    records.append(dict(episode=ep.name,offline_events=len(screen['rows']),held_events=changed))
    for name in ['PEAK_LOAD_ADAPTER_ACTIVE_PHASE_SCREEN.json','frontal_bypass.json','SUBSTEP_LOAD_HISTORY.json']:
        bindings[str(ep/name)]=sha(ep/name)

checks=[]
def reject(name, fn):
    try:fn()
    except (AssertionError,ValueError):checks.append(name)
    else:raise AssertionError(name)
event,t,loads=fault_fixture
for name,mutate in [
    ('stale_action',lambda x:x.update(action_step=t-1)),
    ('wrong_observation_action',lambda x:x['preceding_observation'].update(observed_after_action_step=t)),
    ('forged_peak',lambda x:x['preceding_observation'].update(previous_action_peak_n=99.)),
    ('forged_mode_activation',lambda x:x.update(phase_at_update='top_lift')),
    ('changed_pressure_target',lambda x:x['before'].update(desired_n=6.)),
    ('modified_filter',lambda x:x['after'].update(filtered_n=99.)),
    ('unheld_bias',lambda x:x['after'].update(bias_m=x['before']['bias_m']-.0005)),
    ('returned_bias_disagrees_with_state',lambda x:x['returned'].update(stored_z_bias_m=.01)),
    ('claimed_no_hold',lambda x:x['returned']['peak_bias_guard'].update(held_negative_increment=False)),
    ('applied_bias_disagrees',lambda x:x['returned'].update(applied_z_bias_m=.025))]:
    bad=copy.deepcopy(event);mutate(bad)
    reject(name,lambda:verify_event(bad,action_step=t,previous_action_loads=loads))
for phase,final in [('top_lift',0.),('top_push',17.)]:
    c=TracedPeakLoadControl(5.,bias_m=-.001,filtered_n=5.,min_bias_m=-.006)
    owner=SimpleNamespace(load=c,top_mode=phase);c.bind_owner(owner)
    c.observe(action_step=1,after_action_step=0,vertical_load_n=[17.]+[final]*23)
    c.update(final,phase=='top_push')
    verify_event(c.updates[0],action_step=1,previous_action_loads=[17.]+[final]*23)
    checks.append('independent_'+phase+'_check')
c=TracedPeakLoadControl(5.,min_bias_m=-.006)
reject('unbound_owner_rejected',lambda:c.update(0.,False))
owner=SimpleNamespace(load=c,top_mode='top_lift');c.bind_owner(owner)
c.observe(action_step=1,after_action_step=0,vertical_load_n=[0.]*24)
reject('incorrect_owner_phase_rejected',lambda:c.update(0.,True))
assert not c.updates and c.bias_m==c.filtered_n==0.
for name in ['check_peak_load_update_math.py','peak_load_update_trace.py','audit_peak_load_update_math.py','peak_load_control_adapter.py','peak_load_bias_guard.py']:
    bindings[str(W/name)]=sha(W/name)
dest=W/'PEAK_LOAD_UPDATE_MATH_CHECK.json';assert not dest.exists()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
            scope=__doc__,episodes=records,checks=checks,source_sha256=bindings,
            controller_installed=False,physical_validation=False,training_ready=False)
dest.write_text(json.dumps(report,indent=2))
print(json.dumps(dict(passed=True,offline_events=sum(r['offline_events'] for r in records),
                      held_events=sum(r['held_events'] for r in records),fault_and_boundary_checks=len(checks))))
