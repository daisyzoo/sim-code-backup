"""Additional actual-input one-step screen of an uninstalled pressure candidate.
Real state is restarted before each event; no counterfactual state is carried
forward. Waits require an empty actual pressure trace. Not training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from instant_load_control_adapter import InstantLoadControl
from audit_peak_guard_pressure import verify_stream
from peak_guard_source_binding import verify_observation_binding
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(ep):
    binding=verify_observation_binding(ep);p=json.loads((ep/'peak_load_updates.json').read_text())
    with np.load(ep/'raw.npz') as z:task=str(z['task_id']);n=len(z['q'])
    wait=task=='wait_no_package';assert n==(70 if wait else 1200)
    files=[ep/'raw.npz',ep/'peak_load_updates.json',ep/'quality.json']
    if wait:fr=None;loads={}
    else:
        hp=ep/'PEAK_GUARD_LOAD_HISTORY.json';h=json.loads(hp.read_text());assert h['independent_audit']['passed']
        for name,digest in h['source_sha256'].items():assert sha(ep/name)==digest
        fr=json.loads((ep/'frontal_bypass.json').read_text());loads={x['action_step']:x['vertical_load_n'] for x in h['rows']};files.extend([hp,ep/'frontal_bypass.json'])
    actual=verify_stream(p,fr,loads,frames=n,wait=wait);changes=[];counts=dict(upward_or_equal=0,inactive=0,active=0)
    for e in p['rows']:
        t=e['action_step'];b=e['before'];values=loads[t-1];c=InstantLoadControl(5.,bias_m=b['bias_m'],filtered_n=b['filtered_n'],min_bias_m=-.006);c.observe(action_step=t,after_action_step=t-1,vertical_load_n=values);result=c.update(e['observed_vertical_load_n'],e['active'])
        filtered=.25*e['observed_vertical_load_n']+.75*b['filtered_n'];assert c.filtered_n==filtered==e['after']['filtered_n']
        proposed=max(-.006,min(.025,b['bias_m']+max(-.0005,min(.003,.0008*(filtered-5.))))) if e['active'] else b['bias_m']
        expect=b['bias_m'] if (e['active'] and proposed<b['bias_m'] and (max(values)>10. or values[-1]>=5.)) else proposed
        assert abs(c.bias_m-expect)<1e-12
        if proposed>=b['bias_m']:assert c.bias_m==proposed;counts['upward_or_equal']+=1
        if not e['active']:assert c.bias_m==e['after']['bias_m'];counts['inactive']+=1
        else:counts['active']+=1
        delta=c.bias_m-e['after']['bias_m'];assert -1e-12<=delta<=.000500000001
        if delta>1e-12:changes.append(dict(step=t,phase=e['phase_at_update'],previous_final_n=values[-1],filtered_n=filtered,previous_peak_n=max(values),actual_bias_m=e['after']['bias_m'],one_step_candidate_bias_m=c.bias_m,local_difference_mm=delta*1000))
    for name in ['instant_load_control_adapter.py','instant_load_bias_guard.py','peak_load_control_adapter.py','peak_load_bias_guard.py','audit_peak_guard_pressure.py','INSTANT_LOAD_BIAS_GUARD_CHECK.json','INSTANT_LOAD_CONTROL_ADAPTER_CHECK.json']:files.append(W/name)
    return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episode=ep.name,wait=wait,actual_input_events=len(p['rows']),additional_holds=len(changes),counts=counts,changes=changes,actual_pressure_stream_passed=actual['passed'],source_binding=binding,source_sha256={str(p):sha(p) for p in files},script_sha256=sha(__file__),controller_installed=False,physical_validation=False,training_ready=False)

if __name__=='__main__':
    ep=Path(sys.argv[1]).resolve();dest=ep/'INSTANT_LOAD_ONE_STEP_SCREEN.json';assert not dest.exists();out=inspect(ep);dest.write_text(json.dumps(out,indent=2));print(json.dumps({k:out[k] for k in ['episode','passed','wait','actual_input_events','additional_holds','counts','physical_validation']}))
