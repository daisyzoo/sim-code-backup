"""Bind every new edge decision to native executed episode records.
Requires complete requested frames, initial zero, causal packet, duplicate trace
identity, preceding legacy output and recorded final clearance. Independent
record math covers new overrides. Original legacy task assembly, unloaded pose,
full geometry/quality, images and training admission require separate audits.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_loaded_edge_coverage_decision import verify_decision
from audit_loaded_edge_coverage_record import near
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FILES=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','self_clearance.json','loaded_edge_coverage.json']

def unique(rows,key='step'):
    out={r[key]:r for r in rows};assert len(out)==len(rows),'duplicate index';return out

def plan_contract():
    return dict(enabled=True,version='current_contact_edge_coverage_v1',current_packet_only=True,first_press_to_push_preserved=True,requires_cartesian_override=False,previous_load_is_admission_gate=False,core_inset_m=.01,nominal_elbow_margin_m=.005,nominal_direction_tolerance_m=1e-7,final_float32_stationarity_threshold=1e-6,selection='minimum_cost_among_feasible_stationary_candidates',infeasible='explicit_stop_no_parent_fallback',scope='Nominal fixed reference only; no contact-stability guarantee',training_ready=False)

def verify_files(ep,stage):
    ep=Path(ep);stage=Path(stage);read=lambda name:json.loads((ep/name).read_text())
    with np.load(ep/'raw.npz') as z:
        q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id']);meta=json.loads(str(z['collect_meta']))
    waiting=task=='wait_no_package';n=70 if waiting else 1200
    assert q.shape==u.shape==(n,11) and np.isfinite(q).all() and np.isfinite(u).all(),'incomplete/nonfinite trajectory'
    near(q[0],np.zeros(11),1e-4);near(u[0],np.zeros(11),0);assert np.max(abs(np.diff(u,axis=0)))<=.0550002
    assert meta['loaded_edge_coverage'] is True and meta['loaded_edge_coverage_failure'] is None and meta['assist_frames']==0
    coverage=read('loaded_edge_coverage.json');assert coverage['failure'] is None
    traced=unique(coverage['rows']);clear=read('self_clearance.json');assert clear['failure'] is None and clear['recorded_frames']==clear['requested_frames']==n
    finals=unique([r for r in clear['rows'] if r['phase']=='final_command']);assert set(finals)==set(range(n))
    for t,f in finals.items():
        assert f['accepted'] is True;near(f['command'],u[t],0);near(f['current'],q[t],1e-7);near(f['previous'],u[t-1] if t else np.zeros(11),0)
    if waiting:
        assert not traced and not (ep/'frontal_bypass.json').exists(),'wait edge work'
        return dict(passed=True,wait=True,frames=n,decision_frames=0,overrides=0,records=[],scope=__doc__,training_ready=False)
    assert task in ('push_box_to_bin','nudge_mailer_to_bin')
    fr=read('frontal_bypass.json');fs=unique(fr['rows']);cs=unique(read('coordination.json'));assert set(fs)==set(range(1,n)) and set(cs)==set(range(1,n))
    selected=bool(fr['plan'].get('rear_joint_edge_command',{}).get('enabled'));declared={t for t,c in cs.items() if 'loaded_edge_coverage' in c}
    assert set(traced)==declared==(set(range(1,n)) if selected else set()),'decision coverage'
    if not selected:return dict(passed=True,wait=False,selected=False,frames=n,decision_frames=0,overrides=0,records=[],scope=__doc__,training_ready=False)
    assert fr['plan']['loaded_edge_coverage']==plan_contract()
    assert fr['plan']['unloaded_recontact_pose']['original_loaded_math_unchanged'] is False
    assert fr['plan']['rear_joint_xy_progress']['enabled'] is True
    packets=unique(read('solved_contact_forces.json')['rows'],'after_action_step');assert set(packets)==set(range(n))
    side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer'
    with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
    assert xyz.shape==(n,3) and quat.shape==(n,4)
    urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';hand=HandModel(urdf,repo/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];records=[]
    for t in range(1,n):
        tr=traced[t];c=cs[t];assert c['loaded_edge_coverage']==tr,'coordination/edge trace mismatch'
        legacy=c['joint_edge_refinement'];near(legacy['previous_upper_command'],u[t-1],0)
        record=verify_decision(tr,row=fs[t],previous_row=fs.get(t-1),coordinate=c,current=q[t],previous_command=u[t-1],parent_command=legacy['final_upper_command'],final_command=u[t],packet=packets[t-1],object_xyz=xyz[t],object_quat=quat[t],core_size=core,side=side,selected=True,hand=hand,elbows=elbows)
        records.append(record)
    return dict(passed=all(r['passed'] for r in records),wait=False,selected=True,frames=n,decision_frames=len(records),overrides=sum(r['override'] for r in records),records=records,scope=__doc__,training_ready=False)

def inspect(ep):
    from audit_loaded_edge_pose_live import source_contract
    ep=Path(ep).resolve();stage=source_contract(ep);result=verify_files(ep,stage)
    result.update(source_sha256={name:sha(ep/name) for name in FILES if (ep/name).exists()},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(Path(__file__)),dependent_auditors_sha256={n:sha(w/n) for n in ['audit_loaded_edge_pose_live.py','audit_loaded_edge_coverage_record.py','audit_loaded_edge_coverage_decision.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py']})
    return result

if __name__=='__main__':
    ep=Path(sys.argv[1]);path=ep/'LOADED_EDGE_COVERAGE_LIVE_AUDIT.json';assert not path.exists();out=inspect(ep);path.write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['records','source_sha256','scope']});sys.exit(0 if out['passed'] else 1)
