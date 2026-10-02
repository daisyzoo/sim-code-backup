from pathlib import Path
import ast,json,hashlib,sys,subprocess
import numpy as np
from rear_latched_xy_reconstruction import reconstruct

def main():
    w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    subprocess.run([sys.executable,str(w/'audit_rear_latched_stage_region_bounds.py'),str(ep)],check=True,stdout=subprocess.DEVNULL)
    fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];prov=json.loads((ep.parent/'provenance.json').read_text());enabled=bool(plan.get('rear_cop_centering',{}).get('enabled'))
    if enabled:
        assert bool(plan['rear_cop_centering'].get('core_slice_feedback',False))==bool(prov['args'].get('rear_core_slice_feedback',False))
        assert prov['args']['rear_cop_centering'] and not plan.get('front_route_selected') and not plan.get('initial_top_selected')
        region=json.loads((ep/'region_approach.json').read_text())['rows'];handover=next((r['step'] for r in region if r['solver'] and r['solver'].get('handover')),None)
        key='box' if 'push_box' in ep.name else 'mailer'
        with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
        with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
        config=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(config)==prov['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
        node=next(n for n in ast.walk(ast.parse(config.read_text())) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='core_scale' for x in n.targets));assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'"
        scale=np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body));size=np.array(plan['top_recontact']['contact_size_xyz']);assert np.max(abs(size*scale-plan['rear_cop_centering']['actual_core_size_xyz']))<1e-7
        packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
        from rear_corridor_latched_inputs import verify_inputs
        recovery=verify_inputs(ep,w.parents[1],w/'staged_rear_corridor_latched')
        report=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover,recovery.overrides);recovery.assert_unchanged()
    else:
        assert not any('rear_cop_centering' in r for r in fr['rows'])
        report=dict(passed=True,errors=[],overrides_checked=0,records=[])
    declared=prov['args'].get('rear_coupled_progress',False)
    assert type(declared) is bool
    selected=plan.get('rear_coupled_progress',{}).get('enabled',False)
    assert type(selected) is bool and selected==(declared and enabled)
    if not enabled:assert not any('rear_coupled_progress' in r for r in fr['rows'])
    declared_xy=prov['args'].get('rear_joint_xy_progress',False)
    selected_xy=plan.get('rear_joint_xy_progress',{}).get('enabled',False)
    assert type(declared_xy) is bool and type(selected_xy) is bool
    assert selected_xy==(declared_xy and enabled)
    if declared_xy:assert declared is True
    if not enabled:assert not any('rear_joint_xy_progress' in r for r in fr['rows'])
    if selected_xy:
        for suffix in ['/rear_joint_xy_progress.py','/rear_cop_route.py']:
            matches=[n for n in prov['source_sha256'] if n.endswith(suffix)]
            assert len(matches)==1
            assert sha(ep.parent/'source_snapshot'/matches[0])==prov['source_sha256'][matches[0]]
    names=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','solved_contact_forces.json','REAR_LATCHED_STAGE_REGION_CONTINUITY_AUDIT.json','REAR_LATCHED_STAGE_REGION_BOUNDS_AUDIT.json']
    if (ep/'region_approach.json').exists():names.append('region_approach.json')
    report.update(enabled=enabled,source_sha256={n:sha(ep/n) for n in names},auditor_sha256=sha(Path(__file__)),training_ready=False,scope='Independent prior-packet COP and actual core, original world-X slice correction, original internal Y/Z and optional external reference-direction Y halfspace LP reconstruction. Actual emitted history maintained; original Z preserved; optional joint XY independently maximizes Y under original X slew/lead bounds with parent-Y fallback. Requires original raw-joint/region/transition audits; not a success or training admission decision.')
    (ep/'REAR_LATCHED_STAGE_REAR_XY_AUDIT.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['records','source_sha256']});sys.exit(0 if report['passed'] else 1)


if __name__=='__main__':main()
