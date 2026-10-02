"""Original causal/geometry audit plus independent measured/command domain checks."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np


def verify_bound_record(record, current, command, lower, upper, measured_lower,
                        measured_upper, *, joint_override, handover):
    errors=[]
    for name,want in [('measured_lower',measured_lower),('measured_upper',measured_upper),
                      ('command_lower',lower),('command_upper',upper)]:
        try:
            got=np.asarray(record[name],float)
            assert got.shape==(11,) and np.isfinite(got).all() and np.max(abs(got-want))<1e-12
        except (KeyError,ValueError,TypeError,AssertionError):errors.append('declared_'+name)
    if record.get('handover_requires_command_bounds') is not True:errors.append('handover_domain_declaration')
    current=np.asarray(current,float)
    if current.shape!=(11,) or not np.isfinite(current).all():return errors+['invalid_actual_state']
    if np.any(current<measured_lower-1e-6) or np.any(current>measured_upper+1e-6):errors.append('measured_physical_bounds')
    outside=bool(np.any(current<lower-1e-6) or np.any(current>upper+1e-6))
    if handover and outside:errors.append('handover_outside_command_domain')
    if joint_override:
        command=np.asarray(command,float)
        if command.shape!=(11,) or not np.isfinite(command).all():errors.append('invalid_command')
        elif np.any(command<lower-1e-6) or np.any(command>upper+1e-6):errors.append('command_planning_bounds')
    return errors


def main():
    w=Path(__file__).resolve().parent;repo=w.parents[1];ep=Path(sys.argv[1]).resolve();sys.path.insert(0,str(repo))
    from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    subprocess.run([sys.executable,str(w/'audit_box_entry_region_continuity.py'),str(ep)],check=True,stdout=subprocess.DEVNULL)
    prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];assert args['region_separate_measured_bounds'] and args['waist_limit_rad']==1.
    lower=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();upper=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lower[0]=-.98;upper[0]=.98;ml=lower.copy();mu=upper.copy();ml[0]=-1.;mu[0]=1.
    with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
    plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];rp=ep/'region_approach.json';rows=json.loads(rp.read_text())['rows'] if rp.exists() else []
    assert bool(rows)==bool(plan.get('region_measured_state_bounds',{}).get('enabled'))
    if rows:
        cfg=plan['region_measured_state_bounds'];assert cfg['waist_measured_limit_rad']==1. and cfg['waist_command_limit_rad']==.98 and cfg['other_joints']=='original_URDF' and cfg['handover_requires_command_bounds'] and cfg['original_geometry_and_prediction_bounds']
    checks=[];errors=[]
    for row in rows:
        s=row['solver']
        if not s:continue
        t=row['step'];override=bool(s.get('joint_override'));handover=bool(s.get('handover'))
        bad=verify_bound_record(s.get('measured_state_bounds',{}),q[t],u[t],lower,upper,ml,mu,joint_override=override,handover=handover)
        errors.extend([[t,e] for e in bad]);outside=bool(np.any(q[t]<lower-1e-6) or np.any(q[t]>upper+1e-6))
        checks.append(dict(step=t,outside_command_domain=outside,joint_override=override,handover=handover,waist_state_rad=float(q[t,0]),waist_command_rad=float(u[t,0]),errors=bad))
    sources=['raw.npz','frontal_bypass.json','BOX_ENTRY_REGION_CONTINUITY_AUDIT.json']+(['region_approach.json'] if rows else [])
    report=dict(passed=not errors,errors=errors,region_selected=bool(rows),solver_records_checked=len(checks),inward_recovery_commands=sum(c['outside_command_domain'] and c['joint_override'] for c in checks),checks=checks,source_sha256={n:sha(ep/n) for n in sources},auditor_sha256=sha(Path(__file__)),training_ready=False,scope='Declared limits matched to original URDF and physicalwaist1.0 versus planning0.98. Actual solver states checked, domain-exterior handover forbidden, actual commands bounded. Parent raw-action/causal/geometry/load/continuity audit required. No full-dynamics safety or sorting/data admission claim.')
    (ep/'BOX_ENTRY_REGION_BOUNDS_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['checks','source_sha256']});sys.exit(0 if report['passed'] else 1)


if __name__=='__main__':main()
