"""Captured failure-bound test with explicit idealized geometry, not real physics."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_measured_bounds_probe'
spec=importlib.util.spec_from_file_location('measured_bounds_probe',stage/'contact_patch_approach.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
failure=w/'rear_cop_centering_groups_r1/RUNTIME_FAILURE.json';d=json.loads(failure.read_text())['context'];q=np.array(d['upper11_q']);lower=np.array(d['lower']);upper=np.array(d['upper']);sl=lower.copy();su=upper.copy();sl[0]=-1.;su[0]=1.
calls=[]
def geometry(v):
    calls.append(np.asarray(v).copy())
    return dict(hand_xyz=np.array([.5,0,.7995]),hand_rotation=np.eye(3),vertices=np.array([[-.01,-.01,0],[.01,-.01,0],[-.01,.01,0],[.01,.01,0]]),target_xyz=np.array([.5,0,.7725]),target_rotation=np.eye(3),origin_linear_jacobian=np.zeros((3,11)),angular_jacobian=np.zeros((3,11)),inactive_palm=np.zeros(3),inactive_jacobian=np.zeros((3,11)),hand_other_gap_m=.1)
kw=dict(lower=lower,upper=upper,step_limits=np.r_[.015,np.full(10,.04)],damping=np.r_[.12,np.full(10,.045)],target_size=np.array([.14,.09,.045]),inactive_anchor=np.zeros(3),tracking_residual=np.array(d['tracking_residual']),response_gain=np.array(d['response_gain']),response_offset=np.array(d['response_offset']),preferred_core_scale=np.array([.96,.96,1.]),command_change_damping=True,response_centered_xy_objective=True)
try:module.contact_patch_step(q,geometry,**kw)
except ValueError as e:assert str(e).startswith('Measured joints outside working bounds') and not calls
else:raise AssertionError('Default no longer rejects captured measured bound violation')
out=module.contact_patch_step(q,geometry,**kw,measured_lower=sl,measured_upper=su)
assert out['accepted'] and not out['reached']
nq=np.array(out['next_q']);pred=np.array(d['response_gain'])*nq+np.array(d['response_offset'])
for vector in [nq,pred]:assert np.all(vector>=lower-1e-6) and np.all(vector<=upper+1e-6)
assert np.max(abs(nq-(q-np.array(d['tracking_residual']))))<=.055+1e-8
assert abs(nq[0]-q[0])<=.015+1e-8
# Once within the command domain, measured hold may satisfy original handover.
inside=module.contact_patch_step(nq,geometry,**kw,measured_lower=sl,measured_upper=su)
assert inside['reached'] and np.array_equal(inside['next_q'],nq)
negative=[]
for kind in ['physical_upper','physical_lower','missing_lower','shape','nonfinite','narrow_state_domain']:
    v=q.copy();extra=dict(measured_lower=sl.copy(),measured_upper=su.copy())
    if kind=='physical_upper':v[0]=1.0001
    elif kind=='physical_lower':v[0]=-1.0001
    elif kind=='missing_lower':extra['measured_lower']=None
    elif kind=='shape':extra['measured_lower']=np.zeros(10)
    elif kind=='nonfinite':extra['measured_upper'][0]=np.nan
    else:extra['measured_upper'][0]=.97
    before=len(calls)
    try:module.contact_patch_step(v,geometry,**kw,**extra)
    except ValueError:assert len(calls)==before;negative.append(kind)
    else:raise AssertionError('Invalid measured bounds accepted')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(passed=True,captured_failure_default_rejected=True,geometry_scope='Explicit synthetic constant hand/target geometry; only tests bounds/guard paths, NOT actual robot reachability or physical recovery.',inward_recovery_command=nq.tolist(),predicted_response=pred.tolist(),no_outside_planning_handover=True,negative_cases=negative,failure_sha256=sha(failure),candidate_sha256=sha(stage/'contact_patch_approach.py'),checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False)
(stage/'CHECK.json').write_text(json.dumps(report,indent=2));print(dict(passed=True,waist_command=nq[0],waist_prediction=pred[0],negative_cases=len(negative),geometry='synthetic_only'))
