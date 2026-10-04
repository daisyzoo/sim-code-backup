"""Independently bind release confirmation to complete measured episode history.
No candidate observer import; no training admission or task-success inference.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from audit_confirmed_release_margin import verify_rows
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify_files(ep,*,enabled):
    """Arithmetic/measurement check only; historical fixtures are not new-source data."""
    ep=Path(ep)
    with np.load(ep/'raw.npz') as z:
        task=str(z['task_id']);frames=len(z['q'])
    assert task in ('push_box_to_bin','nudge_mailer_to_bin','wait_no_package')
    wait=task=='wait_no_package';assert frames==(70 if wait else 1200)
    if wait:
        assert not (ep/'frontal_bypass.json').exists() or not json.loads((ep/'frontal_bypass.json').read_text())['rows']
        return verify_rows([],initial_y=0.,direction=1,enabled=enabled,wait=True)
    f=json.loads((ep/'frontal_bypass.json').read_text());rows=f['rows'];plan=f['plan']
    direction=-1 if task=='push_box_to_bin' else 1;key='box' if direction==-1 else 'mailer'
    assert plan['direction']==direction
    assert [r['step'] for r in rows]==list(range(1,frames)), 'incomplete or unordered controller history'
    with np.load(ep/'trace.npz') as z:target=z[key].copy()
    assert target.shape==(frames,3) and np.isfinite(target).all()
    np.testing.assert_allclose(plan['initial_target_xyz'],target[0],rtol=0,atol=1e-7)
    for row in rows:
        if 'observed_target' in row:
            np.testing.assert_allclose(row['observed_target'],target[row['step']],rtol=0,atol=1e-7)
        elif 'terminal_position_confirmed' in row:raise AssertionError('missing measured target')
    result=verify_rows(rows,initial_y=plan['initial_target_xyz'][1],direction=direction,enabled=enabled)
    result.update(full_frames=frames,measured_target_binding=True)
    return result

def audit(ep):
    from front_normal_stage_source_binding_v3 import verify_observation_binding
    ep=Path(ep).resolve();source=verify_observation_binding(ep)
    result=verify_files(ep,enabled=True)
    native=ep/('WAIT_STABILITY_AUDIT.json' if result['wait'] else 'FRONT_NORMAL_POSE_LIVE_V1_AUDIT.json')
    assert json.loads(native.read_text())['passed'] is True
    files=[ep/'raw.npz',native,Path(__file__),W/'audit_confirmed_release_margin.py']
    if not result['wait']:files += [ep/'trace.npz',ep/'frontal_bypass.json']
    result.update(source_binding=source,source_sha256={str(p):sha(p) for p in files},scope=__doc__,training_ready=False)
    return result

if __name__=='__main__':
    ep=Path(sys.argv[1]);result=audit(ep)
    (ep/'FRONT_NORMAL_STAGE_R1_V1_STAGE_RELEASE_AUDIT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_binding','source_sha256')}))
