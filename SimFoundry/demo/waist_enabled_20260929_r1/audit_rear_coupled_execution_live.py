"""Replay recorded loaded IK goals through archived solver to actual raw actions.

New enabled rear episodes require every top_push frame. Historical sampled mode
is explicit and cannot claim full execution coverage or validate new physics.
"""
from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def replay_record(c,row,expert,current,prior_action,actual_action,side,solver):
    assert c['bounded_solver'] is True and c['active_side']==side
    assert not c.get('region_joint_override') and not c.get('terminal_joint_hold')
    assert c['contact_bout_yaw_tracking'] is None and c['waist_preference_rad'] is None
    current=np.asarray(current,dtype=np.float32);previous=np.asarray(prior_action,dtype=np.float32)
    assert np.array_equal(current,np.asarray(c['upper_q'],dtype=np.float32))
    assert np.array_equal(np.asarray(row['target_xyz']),np.asarray(expert['target_xyz']))
    assert expert['mode']==row['mode']=='top_push'
    assert np.max(abs(np.asarray(c['control_point_positions'][side])-row['observed_support_xyz']))<2e-6
    position=np.asarray(c['control_jacobian_world'],dtype=np.float32);assert position.shape==(6,11) and np.isfinite(position).all()
    errors=[]
    for hand in ['left','right']:
        target=row['target_xyz'] if hand==side else c['inactive_anchor']
        point=np.asarray(c['control_point_positions'][hand],dtype=np.float32)
        errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-point),np.float32(-.035),np.float32(.035)).tolist())
    normal=c['contact_normal_tracking'];assert normal is not None
    jac=np.vstack([position,np.asarray(normal['jacobian'],dtype=np.float32)])
    error=np.r_[np.asarray(errors,dtype=np.float32),np.asarray(normal['error'],dtype=np.float32)]
    assert jac.shape==(9,11) and error.shape==(9,) and np.isfinite(jac).all() and np.isfinite(error).all()
    lower=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98
    limits=np.full(11,.04);limits[0]=.015;penalty=np.full(11,np.float32(.045**2),dtype=np.float32);penalty[0]=np.float32(.12**2)
    prior=np.zeros(11,dtype=np.float32);prior[0]=c['preferred_waist_step_rad'];assert prior[0]==0
    dq=solver(jac,error,current,lower,upper,limits,np.sqrt(penalty),preferred_step=prior)
    target=current+dq;target[0]=np.clip(target[0],-.98,.98)
    assigned=target.astype(np.float32);slewed=np.clip(assigned,previous-np.float32(.055),previous+np.float32(.055))
    command=np.clip(slewed,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
    delta=float(np.max(abs(command-np.asarray(actual_action,dtype=np.float32))))
    assert delta<=1.2e-7,('executed_command_mismatch',delta)
    return dict(step=c['step'],max_action_error_rad=delta,command_xyz=row['target_xyz'],reconstructed_upper_action=command.tolist())

def inspect(ep,historical_sampled=False):
    ep=Path(ep).resolve();prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];fr=json.loads((ep/'frontal_bypass.json').read_text());selected=bool(fr['plan'].get('rear_coupled_progress',{}).get('enabled'))
    if not historical_sampled:assert args.get('rear_coupled_progress') is True
    assert args['waist_limit_rad']==1. and args['bounded_coupled_ik'] and args['expert_top_contact_normal_hold'] and not args['expert_top_contact_bout_yaw_hold']
    if not selected and not historical_sampled:
        assert not fr['plan'].get('rear_cop_centering',{}).get('enabled')
        return dict(passed=True,selected=False,records=[],expected_push_frames=0,checked_push_frames=0,historical_sampled=False,complete_push_coverage=True)
    source=ep.parent/'source_snapshot';names=['simfoundry/data/bounded_ik.py','simfoundry/data/waist_coordination.py','simfoundry/robots/g1_assets.py']
    for n in names:assert sha(source/n)==prov['source_sha256'][n]
    # Constants and original limits are independently reconstructed above;
    # bind their implementation to the archived originals examined for this audit.
    assert sha(repo/'simfoundry/robots/g1_assets.py')==sha(source/'simfoundry/robots/g1_assets.py')
    spec=importlib.util.spec_from_file_location('recorded_bounded_ik',source/names[0]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(np.float32);u=z['action'][:,12:23].astype(np.float32)
    coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};expert={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};push=[r for r in fr['rows'] if r['mode']=='top_push'];records=[];errors=[];side='right' if 'push_box' in ep.name else 'left'
    for row in push:
        t=row['step'];c=coords[t]
        if 'control_jacobian_world' not in c:
            if not historical_sampled:errors.append([t,'missing_full_push_jacobian'])
            continue
        try:records.append(replay_record(c,row,expert[t],q[t],u[t-1],u[t],side,module.bounded_damped_step))
        except (AssertionError,KeyError,ValueError) as exc:errors.append([t,repr(exc)])
    if not records:errors.append(['no_push_replay_records'])
    return dict(passed=not errors,errors=errors,selected=selected,records=records,expected_push_frames=len(push),checked_push_frames=len(records),historical_sampled=historical_sampled,complete_push_coverage=len(records)==len(push),maximum_action_error_rad=max((r['max_action_error_rad'] for r in records),default=None),source_sha256={n:sha(ep/n) for n in ['raw.npz','frontal_bypass.json','expert_control.json','coordination.json']},archived_controller_sha256={n:sha(source/n) for n in names})

def main():
    ep=Path(sys.argv[1]).resolve();assert len(sys.argv) in (2,3)
    sampled=len(sys.argv)==3
    if sampled:assert sys.argv[2]=='--historical-sampled'
    out=inspect(ep,sampled);out.update(auditor_sha256=sha(Path(__file__)),training_ready=False,scope='Reconstruct recorded float32 point errors/normal rows and archived bounded IK plus final slew/limits, compare raw executed upper actions. Every top_push Jacobian required for new rear candidate; explicit historical mode checks only recorded samples. Does not certify physical contact, task success, independently measured Jacobian or data admission.')
    name='REAR_COUPLED_EXECUTION_SAMPLED_AUDIT.json' if sampled else 'REAR_COUPLED_EXECUTION_LIVE_AUDIT.json'
    (ep/name).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','source_sha256','archived_controller_sha256']});sys.exit(0 if out['passed'] else 1)
if __name__=='__main__':main()
