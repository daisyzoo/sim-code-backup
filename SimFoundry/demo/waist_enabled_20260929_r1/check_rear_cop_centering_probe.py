"""Independent algebra replay on rear histories, never a simulated intervention."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import sys
import numpy as np
from scipy.spatial.transform import Rotation

w = Path(__file__).resolve().parent
repo = w.parents[1]
sys.path.insert(0, str(repo))
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin

stage = w/'staged_rear_cop_centering_probe'
spec = importlib.util.spec_from_file_location('rear_cop_probe', stage/'rear_cop_centering.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reports = []
for run in ['region_continuity_groups_r1', 'region_causal_response_groups_r1',
            'region_causal_xy_groups_r2']:
    for cid, task in [(840001,'push_box_to_bin'), (840004,'nudge_mailer_to_bin')]:
        ep = w/run/f'case_{cid}/layout_{cid}_{task}'
        fr = json.loads((ep/'frontal_bypass.json').read_text())
        key = 'box' if task=='push_box_to_bin' else 'mailer'
        side = 'right' if key=='box' else 'left'
        actor = 'parcel_box' if key=='box' else 'mailer'
        direction = -1 if key=='box' else 1
        size = np.array(fr['plan']['top_recontact']['contact_size_xyz'])
        config = ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py'
        provenance = json.loads((ep.parent/'provenance.json').read_text())
        assert sha(config) == provenance['source_sha256']['simfoundry/scene_bridge/isaac_cfg.py']
        node = next(n for n in ast.walk(ast.parse(config.read_text())) if isinstance(n,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets))
        assert ast.unparse(node.value.test) == "obj.semantic == 'mailer'"
        scale = np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
        with np.load(ep/'trace.npz') as z: xyz=z[key].astype(float)
        with np.load(ep/'parcel_orientation.npz') as z:
            quat=z[key].astype(float); rot=Rotation.from_quat(quat).as_matrix()
        packets = {r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
        probe = mod.RearCopCentering()
        independent_anchor = None
        independent_world = None
        previous = None
        rows = []
        for row in fr['rows']:
            t=row['step']; parent=np.array(row['target_xyz']); reference=np.array(row['observed_support_xyz'])
            packet=packets.get(t-1)
            if packet:
                assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t])) < 1e-6
            contact=loaded_forward_margin(packet,side,actor,xyz[t],quat[t],size,direction)
            cop=np.array(contact['weighted_contact_local']) if contact['valid'] else None
            normal=contact['normal_load_n']
            prev=previous if previous is not None else reference
            kwargs=dict(mode=row['mode'],parent_xyz=parent,previous_xyz=prev,
                reference_xyz=reference,object_xyz=xyz[t],object_rotation=rot[t],
                core_size=size*scale,cop_local=cop,normal_load_n=normal)
            out=probe.update(**kwargs)
            expected=None
            if row['mode']!='top_push' or cop is None or normal < .3:
                independent_anchor=None;independent_world=None
                assert not out['override']
            elif independent_anchor is None:
                h=size[:2]*scale[:2]/2-.01
                independent_anchor=np.array([max(-h[i],min(h[i],cop[i])) for i in range(2)]+[cop[2]])
                independent_world=xyz[t]+rot[t]@independent_anchor
                assert out['reason']=='preserve_first_loaded_push' and not out['override']
            else:
                anchor=xyz[t]+rot[t]@independent_anchor
                world_cop=xyz[t]+rot[t]@cop
                wanted=prev[0]+anchor[0]-independent_world[0]+.05*(anchor[0]-world_cop[0])
                low=max(prev[0]-.002,reference[0]-.030);high=min(prev[0]+.002,reference[0]+.030)
                if low>high:
                    assert not out['override']
                    independent_anchor=None;independent_world=None
                else:
                    expected=parent.copy();expected[0]=min(high,max(low,wanted))
                    assert out['override'] and np.max(abs(np.array(out['command_xyz'])-expected))<1e-12
                    assert np.array_equal(np.array(out['command_xyz'])[1:],parent[1:])
                    assert abs(expected[0]-prev[0])<=.002+1e-12
                    assert abs(expected[0]-reference[0])<=.030+1e-12
                    independent_world=anchor
            rows.append(dict(step=t,mode=row['mode'],feedback=out))
            # Teacher-forced replay: all subsequent measurements and prior commands
            # remain the original executed history, never synthetic success evidence.
            previous=parent
        reports.append(dict(run=run,episode=ep.name,steps=len(rows),
            overrides=sum(r['feedback']['override'] for r in rows),rows=rows,
            source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz',
                            'frontal_bypass.json','solved_contact_forces.json']},
            collision_source_sha256=sha(config)))

# Guards, first-step continuity, inward sign and incompatible bounds.
base=dict(mode='top_push',parent_xyz=[.5,.1,.8],previous_xyz=[.5,.097,.8],
          reference_xyz=[.5,.1,.8],object_xyz=[.5,0,.77],object_rotation=np.eye(3),
          core_size=[.12,.08,.04],cop_local=[-.059,0,.02],normal_load_n=5.)
probe=mod.RearCopCentering();assert not probe.update(**base)['override']
out=probe.update(**base);assert out['override'] and out['command_xyz'][0]>.5
for mode in ['top_lift','top_cross','top_descend','top_press','top_release','region_guard_lift']:
    assert not probe.update(**dict(base,mode=mode))['override']
    assert probe.anchor_local is None
    assert not probe.update(**base)['override']
assert not probe.update(**dict(base,cop_local=None,normal_load_n=0))['override']
assert not probe.update(**base)['override']
assert not probe.update(**dict(base,reference_xyz=[.6,.1,.8]))['override']
assert probe.anchor_local is None
for bad in [dict(normal_load_n=float('nan')),dict(object_rotation=np.zeros((3,3))),
            dict(core_size=[.01,.08,.04]),dict(cop_local=[float('nan'),0,.02])]:
    try: mod.RearCopCentering().update(**dict(base,**bad))
    except ValueError: pass
    else: raise AssertionError('Invalid input accepted')
report=dict(passed=True,rows=reports,total_real_steps=sum(r['steps'] for r in reports),
    total_counterfactual_overrides=sum(r['overrides'] for r in reports),
    candidate_sha256=sha(stage/'rear_cop_centering.py'),checker_sha256=sha(Path(__file__)),
    contact_measurement_source_sha256=sha(repo/'simfoundry/data/top_contact_load_geometry.py'),
    collector_wired=False,physical_started=False,training_ready=False,
    scope='Six full rear histories, independent scalar algebra and current contact packet '
          'alignment. Checks fixed original inputs only; hypothetical X commands were not '
          'executed and do not prove continued contact or improved sorting. No runtime '
          'controller integration/guards-order validation yet.')
(stage/'CHECK.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
for r in reports: print(r['run'],r['episode'],r['steps'],r['overrides'])
