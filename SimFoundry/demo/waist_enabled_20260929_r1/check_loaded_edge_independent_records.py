"""Check all actual-adapter historical-state overrides independently, not new physics."""
from pathlib import Path
import sys, json, hashlib, datetime, copy
import numpy as np
w=Path(__file__).resolve().parent; repo=w.parents[1]; sys.path[:0]=[str(w),str(repo)]
from audit_loaded_edge_coverage_record import verify
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
stage=w/'staged_loaded_edge_coverage'; run=w/'recontact_pose_groups_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fixture=stage/'ADAPTER_ACTUAL_CHECK.json'; data=json.loads(fixture.read_text())
for p,h in data['source_sha256'].items(): assert sha(p)==h,('stale fixture',p)
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'; vertices=repo/'assets/robots/g1_hand_support_vertices.json'
hand=HandModel(urdf,vertices); elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf)
records=[]; negative=[]; sources=dict(data['source_sha256'])
for episode in data['rows']:
    paths=list(run.glob('case_*/'+episode['episode'])); assert len(paths)==1
    ep=paths[0]; fr=json.loads((ep/'frontal_bypass.json').read_text()); fs={r['step']:r for r in fr['rows']}; cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}; packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
    side='right' if 'push_box' in ep.name else 'left'; key='box' if side=='right' else 'mailer'
    with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
    with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
    for r in episode['records']:
        if not r['override']:continue
        t=r['step']; tr=r['trace']; ctx=dict(row=fs[t],previous_row=fs[t-1],coordinate=cs[t],current=q[t],previous_command=u[t-1],parent_command=u[t],final_command=tr['final_upper_command'],packet=packets[t-1],object_xyz=xyz[t],object_quat=quat[t],core_size=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'],side=side,selected=bool(fr['plan']['rear_joint_xy_progress']['enabled']),hand=hand,elbows=elbows)
        result=verify(tr,**ctx);records.append(dict(episode=ep.name,**result))
        if not result['passed']:
            for attempt in tr['attempts']:
                if not attempt['accepted']:continue
                alt=copy.deepcopy(tr);alt['command']=alt['final_upper_command']=attempt['final']['command']
                checked=verify(alt,**dict(ctx,final_command=alt['command']))
                print('ALTERNATIVE',ep.name,t,attempt['seed'],checked,flush=True)
        if not negative:
            cases=[]
            def change_trace(label,fn):
                bad=copy.deepcopy(tr);fn(bad);cases.append((label,bad,ctx))
            change_trace('wrong_COP',lambda b:b['context']['current_cop_local'].__setitem__(0,b['context']['current_cop_local'][0]+.001))
            change_trace('wrong_bounds',lambda b:b['bound_low'].__setitem__(0,b['bound_low'][0]-.01))
            change_trace('wrong_final',lambda b:b['final_upper_command'].__setitem__(0,b['final_upper_command'][0]+.01))
            change_trace('wrong_load',lambda b:b['context'].__setitem__('load_n',b['context']['load_n']+1))
            change_trace('false_branch',lambda b:b.__setitem__('override',False))
            change_trace('nonfinite_command',lambda b:b['command'].__setitem__(0,float('nan')))
            for label,field,fn in [('future_packet','packet',lambda b:b.__setitem__('after_action_step',t)),('no_contact','packet',lambda b:b.__setitem__('parcel_contacts',[])),('true_transition','previous_row',lambda b:b.__setitem__('mode','top_press')),('new_bout','previous_row',lambda b:b.__setitem__('recontacts',b['recontacts']+1)),('terminal_precedence','coordinate',lambda b:b.__setitem__('terminal_joint_hold',{'held':True})),('guard_precedence','row',lambda b:b.__setitem__('route_stop_reason','test'))]:
                bad=copy.deepcopy(ctx[field]);fn(bad);cases.append((label,tr,dict(ctx,**{field:bad})))
            for label,bad,kwargs in cases:
                try: verify(bad,**kwargs)
                except AssertionError:negative.append(label)
                else:raise AssertionError('accepted corruption '+label)
assert len(records)==data['overrides']==58 and len(negative)==12
for p in [Path(__file__),w/'audit_loaded_edge_coverage_record.py',fixture,repo/'simfoundry/data/top_contact_bypass.py']:
    sources[str(p)]=sha(p)
out=dict(passed=all(r['passed'] for r in records),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=len(records),max_stationarity_residual=max(r['stationarity_residual'] for r in records),negative_checks=negative,records=records,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'INDEPENDENT_RECORD_CHECK.json').write_text(json.dumps(out,indent=2));print({k:out[k] for k in ['passed','commands','max_stationarity_residual','negative_checks']});sys.exit(0 if out['passed'] else 1)
