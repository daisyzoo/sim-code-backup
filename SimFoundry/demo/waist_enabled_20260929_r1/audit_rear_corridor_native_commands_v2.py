"""Bind independent rear command verification to complete native episode files.
This audits the new command boundary only. Original phase/contact/pressure/KKT/
scene-path audits and task/visual quality remain mandatory and separate.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
from audit_rear_corridor_command_records import RecoveryVerifier
from rear_corridor_stationarity import verify as verify_recovery_stationarity


def verify_files(ep,root,stage):
    ep=Path(ep);audit=RecoveryVerifier(root,stage)
    def read(n):return json.loads((ep/n).read_text())
    def unique(rows):
        out={r['step']:r for r in rows};assert len(out)==len(rows);return out
    with np.load(ep/'raw.npz') as z:
        q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
    wait=task=='wait_no_package';n=len(q)
    assert task in ['wait_no_package','push_box_to_bin','nudge_mailer_to_bin']
    assert n==(70 if wait else 1200) and q.shape==u.shape==(n,11)
    assert np.isfinite(q).all() and np.isfinite(u).all() and np.array_equal(u[0],np.zeros(11))
    log=read('rear_corridor_recovery.json');assert log['executed_action_count']==n and log['training_ready'] is False
    assert log['pending_recontact'] is False,'uncompleted recovery is not a passing control episode'
    rr=unique(log['rows']);hands=unique(log['handovers']);records=[]
    if wait:
        assert not rr and not hands and np.array_equal(u,np.zeros_like(u))
        return dict(passed=True,wait=True,frames=n,overrides=0,records=[],training_ready=False)
    fr=read('frontal_bypass.json');fs=unique(fr['rows']);cs=unique(read('coordination.json'));ex=unique(read('expert_control.json'));evs=unique(read('recontact_pose.json')['rows']);pressure=unique(read('peak_load_updates.json')['final_control_states'])
    assert list(fs)==list(cs)==list(range(1,n))
    selected=fr['plan'].get('rear_joint_xy_progress',{}).get('enabled',False)
    assert list(rr)==(list(range(1,n)) if selected else [])
    assert not selected or fr['plan']['region_approach']['enabled']
    side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
    with np.load(ep/'trace.npz') as z:pos={k:z[k].astype(float) for k in sizes}
    with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k]).as_matrix() for k in sizes}
    pending=False;pending_count=None;completed=[]
    for t in range(1,n):
        f,c=fs[t],cs[t];event=evs.get(t)
        if t in hands:
            h=hands[t];assert pending and event['kind']=='handover'
            assert event['measured_ready_count']>=3 and event['rear_transport_handover_witness']['accepted'] is True
            ctx=event['context'];assert ctx['observed_load_n']==0. and 0.<=ctx['filtered_load_n']<=.05
            assert ctx['recontacts']==pending_count==h['recontacts']
            assert h['kind']=='measured_directional_handover'
            pending=False;pending_count=None;completed.append(t)
        if pending:
            assert event is not None and event['kind']!='stop'
            assert not (event['kind']=='unchanged' and event['context']['parent_mode'] in ['top_descend','top_press','top_push'])
        if t not in rr:
            assert 'rear_corridor_override' not in f and 'rear_corridor_override' not in c
            continue
        r=rr[t];kind=r['kind'];assert kind!='stop'
        if kind=='unchanged':
            assert not r['recovery']['applied'] and np.array_equal(u[t],r['parent_command'])
            assert 'rear_corridor_override' not in f and 'rear_corridor_override' not in c
            reason=r['recovery']['reason']
            if f['mode']!='top_push' or f.get('route_stop_reason') or f.get('release_reason') or c.get('region_joint_override') or c.get('terminal_joint_hold'):
                assert reason=='original_mode_guard'
            elif not f.get('rear_cop_centering',{}).get('override'):
                assert reason=='original_contact_or_first_load_guard'
            else:
                rad=abs(rot[key][t])@np.array(sizes[key])/2;orad=abs(rot[other][t])@np.array(sizes[other])/2;direction=-1 if side=='right' else 1
                obstacle_pending=direction*(pos[key][t,1]-pos[other][t,1])<=rad[1]+orad[1]+.020
                deficit=pos[other][t,0]+orad[0]+rad[0]+.020-pos[key][t,0]
                assert (not obstacle_pending or deficit<=0) and reason=='no_rear_corridor_deficit'
            continue
        assert not pending,'Loaded recovery cannot precede required measured handover'
        geometry=dict(target_xyz=pos[key][t],obstacle_xyz=pos[other][t],target_rotation=rot[key][t],obstacle_rotation=rot[other][t],target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'])
        proof=audit.verify(r,row=f,coordinate=c,current=q[t],previous=u[t-1],action=u[t],geometry=geometry)
        stationarity=verify_recovery_stationarity(audit,row=r['parent_row'],coordinate=r['parent_coordinate'],current=q[t],previous=u[t-1],command=u[t],kind=kind,geometry=geometry)
        assert stationarity['passed'],('new recovery KKT failed',t,stationarity['reason'],stationarity['stationarity_residual'])
        proof['changed_task_stationarity']=stationarity
        assert ex[t]['mode']==f['mode'] and np.array_equal(ex[t]['target_xyz'],f['target_xyz'])
        assert pressure[t]['mode']==pressure[t]['top_mode']==f['mode']
        parent_pressure=r['parent_pressure_final_state'];assert parent_pressure['step']==t
        assert parent_pressure['filtered_n']==pressure[t]['filtered_n']==f['contact_load']['filtered_vertical_load_n']
        assert parent_pressure['pressure_update_count']==pressure[t]['pressure_update_count']
        assert parent_pressure['bias_m']==r['parent_row']['contact_load']['stored_z_bias_m']
        if kind=='unload':
            assert pressure[t]['bias_m']==0.;pending=True;pending_count=f['recontacts']
        else:assert pressure[t]['bias_m']==parent_pressure['bias_m']
        records.append(proof)
    assert not pending and completed==list(hands)
    return dict(passed=True,wait=False,frames=n,selected=selected,overrides=len(records),records=records,measured_directional_handovers=completed,training_ready=False)


def main():
    w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();root=w.parents[1];stage=w/'staged_rear_corridor_recovery_guarded'
    from rear_corridor_stage_source_binding import verify_observation_binding
    binding=verify_observation_binding(ep);out=verify_files(ep,root,stage)
    files=['raw.npz','rear_corridor_recovery.json']
    if not out['wait']:files+=['frontal_bypass.json','coordination.json','expert_control.json','recontact_pose.json','peak_load_updates.json','trace.npz','parcel_orientation.npz']
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    out.update(scope=__doc__,source_binding=binding,file_sha256={n:sha(ep/n) for n in files},auditor_sha256=sha(__file__),independent_verifier_sha256=sha(w/'audit_rear_corridor_command_records.py'))
    out['stationarity_source_sha256']={n:sha(w/n) for n in ['rear_corridor_stationarity.py','support_vertex_stationarity.py']}
    dest=ep/'REAR_CORRIDOR_NATIVE_COMMAND_V2_AUDIT.json'
    with dest.open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k not in ['records','source_binding','file_sha256','scope']}))
if __name__=='__main__':main()
