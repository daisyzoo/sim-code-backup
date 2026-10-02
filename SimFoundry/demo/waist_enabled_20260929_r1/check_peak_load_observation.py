"""Compare prospective extraction with independently audited actual intervals.
Fault injections use copies only; no physical run or control change.
"""
from pathlib import Path
import sys
import json
import hashlib
import datetime
import copy
import numpy as np
from peak_load_observation import extract

W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];bindings={};fixture=None
for arg in sys.argv[1:]:
    ep=Path(arg).resolve()
    hist=json.loads((ep/'SUBSTEP_LOAD_HISTORY.json').read_text())
    assert hist['independent_audit']['passed']
    for name,digest in hist['source_sha256'].items():assert sha(ep/name)==digest,name
    meta=json.loads((ep/'SUBSTEP_CONTACT_RECORDING.json').read_text())['metadata']
    with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
    side,target=('right','parcel_box') if 'push_box' in ep.name else ('left','mailer')
    stride=24+meta['expected_manager_steps'];maximum=0.
    for step,row in enumerate(hist['rows']):
        assert row['action_step']==step
        b=step*stride;e=b+stride;lo=int(a['contact_offsets'][b]);hi=int(a['contact_offsets'][e])
        part={k:a[k][b:e] for k in ['action_step','substep_tick','kind']}
        part.update(contact_offsets=a['contact_offsets'][b:e+1]-lo,
                    shape_ids=a['shape_ids'][lo:hi],force_torque_world=a['force_torque_world'][lo:hi])
        out=extract(part,meta,after_action_step=step,side=side,target_name=target)
        err=float(np.max(abs(np.asarray(out['vertical_load_n'])-row['vertical_load_n'])))
        assert err<1e-10,(ep.name,step,err)
        maximum=max(maximum,err)
        if fixture is None and out['peak_vertical_load_n']>10.:
            fixture=(copy.deepcopy(part),meta,step,side,target)
    records.append(dict(episode=ep.name,intervals=len(hist['rows']),max_load_error_n=maximum))
    for name in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','SUBSTEP_LOAD_HISTORY.json']:
        bindings[str(ep/name)]=sha(ep/name)
assert fixture is not None
p,m,step,side,target=fixture;checks=[]
before={k:v.tobytes() for k,v in p.items()}
extract(p,m,after_action_step=step,side=side,target_name=target)
assert before=={k:v.tobytes() for k,v in p.items()};checks.append('input_arrays_unchanged')
def reject(name,fn):
    try:fn()
    except ValueError:checks.append(name)
    else:raise AssertionError(name)
for name,mutate in [('stale_step',lambda x:x['action_step'].__setitem__(0,step-1)),
                    ('missing_tick',lambda x:x['substep_tick'].__setitem__(1,0)),
                    ('wrong_callback_kind',lambda x:x['kind'].__setitem__(-1,0)),
                    ('nonfinite_force',lambda x:x['force_torque_world'].__setitem__((0,2),np.nan)),
                    ('negative_shape',lambda x:x['shape_ids'].__setitem__((0,0),-1)),
                    ('offsets_out_of_bounds',lambda x:x['contact_offsets'].__setitem__(-1,999999))]:
    bad=copy.deepcopy(p);mutate(bad)
    reject(name,lambda:extract(bad,m,after_action_step=step,side=side,target_name=target))
reject('wrong_hand_target_pair',lambda:extract(p,m,after_action_step=step,side='left',target_name='parcel_box'))
for path in [Path(__file__),W/'peak_load_observation.py']:bindings[str(path)]=sha(path)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
            scope=__doc__,actual_episodes=records,total_actual_intervals=sum(x['intervals'] for x in records),
            fault_and_immutability_checks=checks,source_sha256=bindings,
            controller_installed=False,physical_validation=False,training_ready=False)
dest=W/'PEAK_LOAD_OBSERVATION_CHECK.json';assert not dest.exists()
dest.write_text(json.dumps(report,indent=2))
print(json.dumps(dict(passed=True,episodes=len(records),actual_intervals=report['total_actual_intervals'],
                      fault_and_immutability_checks=len(checks))))
