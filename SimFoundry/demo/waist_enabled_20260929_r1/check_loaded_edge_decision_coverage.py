"""Independent all-branch replay of actual8 streams; counterfactual, no new physics."""
from pathlib import Path
import sys,json,hashlib,datetime,collections,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(w),str(repo)]
from loaded_edge_coverage_adapter import refine_record
from clearance_runtime import ClearanceGuard
from simfoundry.data.top_contact_bypass import rotation_xyzw
from audit_loaded_edge_coverage_decision import verify_decision
from audit_unloaded_wrist_prior_live import HandModel
from audit_unloaded_wrist_task_optimality import IndependentElbows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
fixture=stage/'ADAPTER_ACTUAL_CHECK.json';d=json.loads(fixture.read_text());sources=dict(d['source_sha256'])
for p,h in sources.items():assert sha(p)==h
urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=repo/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices);elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf);guard=ClearanceGuard(repo,stage)
records=[];counts=collections.Counter();negative=[]
for item in d['rows']:
    ep=next((w/'recontact_pose_groups_r1').glob('case_*/'+item['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
    side='right' if 'push_box' in ep.name else 'left';key='box' if side=='right' else 'mailer';selected=bool(fr['plan'].get('rear_joint_xy_progress',{}).get('enabled'));core=fr['plan'].get('region_causal_response',{}).get('actual_core',{}).get('collision_core_size_xyz')
    with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].copy()
    with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
    with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].copy()
    last=None
    for row in fr['rows']:
        t=row['step'];ctx=dict(row=row,previous_row=last,coordinate=cs[t],current=q[t],previous_command=u[t-1],parent_command=u[t],packet=packets.get(t-1),object_xyz=xyz[t],object_quat=quat[t].astype(float),core_size=core,side=side,selected=selected,hand=hand,elbows=elbows)
        runtime=dict(enabled=True,selected=selected,row=row,previous_row=last,coordinate=cs[t],current=q[t],previous=u[t-1],parent_command=u[t],packet=packets.get(t-1),object_xyz=xyz[t],object_rotation=rotation_xyzw(quat[t].tolist()),core_size=core,model=guard.model,geometry=guard.geometry,side=side)
        cmd,tr=refine_record(**runtime);checked=verify_decision(tr,**ctx,final_command=cmd);assert checked['passed'];counts[checked['reason']]+=1
        records.append(dict(episode=ep.name,**checked))
        if checked['reason'] not in negative:
            bad=copy.deepcopy(tr);bad['reason']='false_claim'
            try:verify_decision(bad,**ctx,final_command=cmd)
            except AssertionError:negative.append(checked['reason'])
            else:raise AssertionError('accepted wrong branch label')
        last=row
    print(ep.name,'all decisions independently checked',flush=True)
assert len(records)==9592 and sum(r['override'] for r in records)==58
for p in [Path(__file__),fixture,w/'audit_loaded_edge_coverage_decision.py',w/'audit_loaded_edge_coverage_record.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,frames=len(records),overrides=58,reason_counts=dict(counts),branch_label_corruption_rejections=negative,records=records,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'DECISION_COVERAGE_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(records),dict(counts),flush=True)
