"""Bind independent unloaded pose audit to native episode files and provenance.
No candidate control helper is imported. Full-length control evidence only;
not original task/pose success, whole-body safety, images or training admission.
Short/aborted episodes are rejected, never silently truncated into a pass.
"""
from pathlib import Path
import sys,json,hashlib,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_slow_drag_events import EventAudit
from audit_recontact_pose_normal import verify_normal_rows
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FILES=['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','expert_control.json','region_approach.json','recontact_pose.json','solved_contact_forces.json','self_clearance.json','terminal_joint_hold.json']
def unique(rows,key='step'):
    out={r[key]:r for r in rows};assert len(out)==len(rows),'duplicate record indices';return out

def loads(fr,packets,side,actor):
    packets=unique(packets,'after_action_step');filtered=0.;out={}
    for f in fr:
        if 'contact_load' not in f:continue
        t=f['step'];assert t-1 in packets,('missing previous force packet',t)
        observed=0.
        for c in packets[t-1]['parcel_contacts']:
            if any(side+'_wrist_roll' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes']):
                force=float(c['force_world_N'][2]);assert np.isfinite(force);observed+=abs(force)
        filtered=.25*observed+.75*filtered
        near(f['contact_load']['observed_vertical_load_n'],observed,1e-10)
        near(f['contact_load']['filtered_vertical_load_n'],filtered,1e-10)
        out[t]=(observed,filtered)
    return out

def verify_files(ep,stage):
    """Native-file check without provenance; fixture callers must label as synthetic."""
    ep=Path(ep)
    with np.load(ep/'raw.npz') as z:
        q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
    assert task in ('push_box_to_bin','nudge_mailer_to_bin') and q.shape==u.shape and q.shape[1]==11 and np.isfinite(q).all() and np.isfinite(u).all()
    side='right' if task=='push_box_to_bin' else 'left';inactive='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';actor='parcel_box' if key=='box' else 'mailer'
    def read(name):return json.loads((ep/name).read_text())
    fr=read('frontal_bypass.json');fs=unique(fr['rows']);coords=read('coordination.json');cs=unique(coords);experts=unique(read('expert_control.json'));regions=unique(read('region_approach.json')['rows']) if (ep/'region_approach.json').exists() else {};evs=unique(read('recontact_pose.json')['rows']);holds=unique(read('terminal_joint_hold.json')['rows']);clear=read('self_clearance.json')
    assert clear['failure'] is None and clear['recorded_frames']==len(q) and clear['requested_frames']==len(q),'incomplete/aborted control episode'
    assert sorted(cs)==sorted(fs)==list(range(1,len(q)))
    assert sorted(experts)==list(range(len(q)))
    observed=loads(fr['rows'],read('solved_contact_forces.json')['rows'],side,actor)
    final=unique([r for r in clear['rows'] if r['phase']=='final_command'])
    assert sorted(final)==list(range(len(q)))
    with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);oxyz=z[other].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float);oquat=z[other].astype(float)
    assert xyz.shape==oxyz.shape==(len(q),3) and quat.shape==oquat.shape==(len(q),4)
    selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'))
    assert (ep/'region_approach.json').exists()==bool(fr['plan'].get('region_approach',{}).get('enabled'))
    assert not selected or bool(regions)
    assert set(evs)==({t for t in observed if t in regions} if selected else set()),'recovery event coverage'
    for raw in evs.values():
        if raw.get('planning') is not None:assert raw['planning'].get('minimum_motion_pose',{}).get('enabled') is True,'new planning metadata missing'
    audit=EventAudit(repo,stage);verified={};records=[];anchor=None;center=None;surface=None;core=fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz')
    for t in range(1,len(q)):
        f=fs[t];c=cs[t];raw=evs.get(t);event={k:v for k,v in raw.items() if k!='step'} if raw else None
        assert not (event and event['kind']=='stop'),'stopped recovery is not a passing episode'
        if event and event['kind'] in ('command','handover'):
            region=regions[t];ctx=event['context'];scene=dict(side=side,target_xyz=xyz[t].tolist(),target_quat=quat[t].tolist(),core_size=core,other_xyz=oxyz[t].tolist(),other_quat=oquat[t].tolist(),other_size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045])
            # Parent phase is declared before adapter; guards/recontact count survive
            # adapter unchanged and are independently bound to final expert rows.
            assert ctx['parent_mode'] in ('top_cross','top_descend')
            record=audit.verify(event,step=t,current=q[t],previous_q=q[t-1],previous_command=u[t-1],final_command=u[t],scene=scene,decay=fr['plan']['region_causal_response']['decay'],selected=bool(selected and region['center_local'] is not None),parent_mode=ctx['parent_mode'],recontacts=f['recontacts'],guard_stop=bool(f.get('route_stop_reason') or f.get('release_reason') or region['abort_reason']),observed_load_n=observed[t][0],filtered_load_n=observed[t][1])
            assert c['recontact_pose_override']==event and c['controller_kind']=='verified_unloaded_recontact_joint_path'
            near(c['upper_q'],q[t],1e-7);assert c['active_side']==side and c['bounded_solver'] is True and c['task_inputs'] is None and c['contact_normal_tracking'] is None and c['contact_bout_yaw_tracking'] is None
            assert not c.get('region_joint_override') and not c.get('terminal_joint_hold')
            assert c.get('joint_edge_refinement',{}).get('override',False) is False
            expected_mode='top_press' if event['kind']=='handover' else 'top_cross';assert f['mode']==experts[t]['mode']==region['mode']==expected_mode
            assert f['recontact_pose_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')
            assert f['contact_load']['applied_z_bias_m']==f['contact_load']['stored_z_bias_m']==0
            assert t in holds and holds[t]['held'] is False;near(holds[t]['output_upper_command'],u[t],0)
            near(holds[t]['previous_upper_command'],u[t-1],0);near(holds[t]['current_upper_q'],q[t],1e-7)
            assert final[t]['accepted'] is True;near(final[t]['command'],u[t],0);near(final[t]['current'],q[t],1e-7);near(final[t]['previous'],u[t-1],0)
            if anchor is not None:near(event['old_inactive_anchor'],anchor,1e-9)
            if event['kind']=='handover':
                anchor=event['captured_inactive_anchor_world'];center=event['captured_center_local'];surface=event['selected_surface_local_xy']
                assert region['active'] is False;near(f['target_xyz'],event['observed_support_xyz'],1e-9);near(experts[t]['target_xyz'],f['target_xyz'],1e-9)
                near(f['observed_support_xyz'],event['observed_support_xyz'],1e-9)
                near(f['control_offset_local'],event['reference']['reference_local'],1e-9)
                assert f['projected_support_reference']==c['active_support_reference']==event['reference']
                near(c['control_point_positions'][side],event['observed_support_xyz'],2e-6)
                assert f['push_x_anchor_m'] is None and f['approach_xy_bias_m']==[0.,0.]
            verified[t]=event;records.append(record)
        else:
            assert not audit.active,'missing event during active path'
            assert c.get('controller_kind')!='verified_unloaded_recontact_joint_path' and 'recontact_pose_override' not in c
            if event:assert event['kind']=='unchanged'
            if event and event.get('planning') is not None:
                ctx=event['context'];scene=dict(side=side,target_xyz=xyz[t].tolist(),target_quat=quat[t].tolist(),core_size=core,other_xyz=oxyz[t].tolist(),other_quat=oquat[t].tolist(),other_size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045])
                near(ctx['current'],q[t],1e-7);assert ctx['scene']==scene and not event['planning']['accepted']
                audit.verify_preference(event['planning'],current=q[t],scene=scene,step=t)
        if anchor is not None:
            near(c['inactive_anchor'],anchor,1e-9)
            if t in regions:
                near(regions[t]['center_local'],center,1e-9);near(regions[t]['selected_surface_local_xy'],surface,1e-9)
    assert not audit.active,'unfinished recovery path'
    normal=verify_normal_rows(q,coords,experts,set(fs),verified,audit.hand,side)
    return dict(passed=True,selected=selected,frames=len(q),command_events=len(records),handovers=sum(r['kind']=='handover' for r in records),records=records,normal=normal,scope=__doc__,training_ready=False)

def source_contract(ep):
    prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];source=prov['source_sha256'];snap=ep.parent/'source_snapshot';stage=w/'staged_rear_slow_drag'
    from audit_slow_drag_source_contract import verify_slow_drag_source
    verify_slow_drag_source(ep)
    for k in ['minimum_motion_recontact','recontact_interior_preference','unloaded_recontact_pose','rear_short_recovery','self_clearance_task_ik','rear_joint_xy_progress','region_causal_response','region_separate_measured_bounds','expert_top_contact_normal_hold','waist_coordinated_expert','bounded_coupled_ik']:assert args[k] is True,k
    assert args['role']=='diagnostic' and args['motion_protocol']=='waist_yaw_enabled_v1' and args['waist_limit_rad']==1.
    for k in ['policy_port','waist_probe','idle','push_assist','push_force_n','wait_force_n']:assert not args.get(k),k
    for n,h in source.items():assert sha(snap/n)==h,('archive changed',n)
    for name in ['collect_paired_sorting.py','waist_coordination_clearance.py','recontact_tracking.py','recontact_lifecycle.py','recontact_plan.py','recontact_plan_original.py','recontact_plan_deeper.py','recontact_scene.py','recontact_adapter.py','minimum_motion_recontact.py','minimum_motion_lifecycle.py','elbow_torso_hulls.json']:
        keys=[n for n in source if n.endswith('/'+name)];assert len(keys)==1 and sha(stage/name)==source[keys[0]],name
    for name in ['simfoundry/robots/g1_assets.py','simfoundry/calibration/sorting_station.py','third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf','assets/robots/g1_hand_support_vertices.json']:assert sha(repo/name)==source[name]
    if not (ep/'frontal_bypass.json').exists():
        with np.load(ep/'raw.npz') as z:assert str(z['task_id'])=='wait_no_package','Missing push plan'
        return stage
    fr=json.loads((ep/'frontal_bypass.json').read_text())
    if fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'):
        pref=fr['plan']['unloaded_recontact_pose']['interior_preference']
        assert pref==dict(enabled=True,preferred_inset_m=.020,original_inset_m=.012,original_fallback=True,interpolated_path_check=True,measured_handover_inset_m=.01,training_ready=False)
        cfg=fr['plan']['region_causal_response']
        names=[n for n in source if n.endswith('/causal_response_parameters.json')];assert len(names)==1
        assert sha(stage/'causal_response_parameters.json')==source[names[0]]
        with np.load(ep/'raw.npz') as z:task=str(z['task_id'])
        params=json.loads((snap/names[0]).read_text());near(cfg['decay'],params['tasks'][task]['decay'],0)
        path='simfoundry/scene_bridge/isaac_cfg.py';tree=ast.parse((snap/path).read_text());assert sha(snap/path)==source[path]
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='core_scale' for t in n.targets))
        assert ast.unparse(node.value.test)=="obj.semantic == 'mailer'"
        size=np.array([.14,.09,.045] if task=='push_box_to_bin' else [.15,.145,.04]);scale=np.array(ast.literal_eval(node.value.orelse if task=='push_box_to_bin' else node.value.body))
        near(cfg['actual_core']['collision_core_size_xyz'],size*scale,1e-7)
    return stage

def inspect(ep):
    ep=Path(ep).resolve();stage=source_contract(ep)
    with np.load(ep/'raw.npz') as z:
        q=z['q'][:,12:23];u=z['action'][:,12:23];meta=json.loads(str(z['collect_meta']))
    assert q.shape==u.shape==(1200,11) and np.max(abs(q[0]))<1e-4 and np.array_equal(u[0],np.zeros(11))
    assert meta['minimum_motion_recontact'] is True
    assert meta['recontact_interior_preference'] is True and meta['unloaded_recontact_pose'] is True and meta['unloaded_recontact_failure'] is None and meta['assist_frames']==0
    out=verify_files(ep,stage);out.update(source_sha256={n:sha(ep/n) for n in FILES if n!='region_approach.json' or (ep/n).exists()},provenance_sha256=sha(ep.parent/'provenance.json'),auditor_sha256=sha(Path(__file__)),dependent_auditors_sha256={n:sha(w/n) for n in ['audit_slow_drag_plan.py','audit_slow_drag_events.py','audit_recontact_interior_events.py','audit_recontact_pose_events.py','audit_recontact_pose_normal.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py']})
    return out
if __name__=='__main__':
    ep=Path(sys.argv[1]);out=ep/'SLOW_DRAG_POSE_LIVE_AUDIT.json';assert not out.exists();result=inspect(ep);out.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['records','normal','source_sha256','scope']})
