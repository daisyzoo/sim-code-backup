"""Native-format coverage I/O fixtures on original measured states.
New actions are sequential counterfactual proposals; next measured q/objects
remain recorded parent values, NOT a simulated plant or training trajectory.
Legacy parent solver math is NOT claimed verified by this coverage-only test.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,tempfile,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_loaded_edge_coverage';sys.path[:0]=[str(stage),str(w),str(repo)]
from loaded_edge_coverage_adapter import refine_record
from clearance_runtime import ClearanceGuard
from simfoundry.data.top_contact_bypass import rotation_xyzw
from audit_loaded_edge_coverage_live import verify_files,plan_contract
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage)
fixture=Path(tempfile.mkdtemp(prefix='loaded_edge_native_fixture_',dir='/tmp'));records=[];negative=[];sources={}
# Source version changes only provenance contract/report name; unloaded math exact.
old=ast.parse((w/'audit_recontact_pose_live.py').read_text());new=ast.parse((w/'audit_loaded_edge_pose_live.py').read_text())
for name in ['unique','loads','verify_files']:
 a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
# Actual collector plan declaration and audit contract exact, no executed AppLauncher.
tree=ast.parse((stage/'collect_paired_sorting.py').read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and ast.unparse(t)=="frontal_plan['loaded_edge_coverage']" for t in n.targets));assert {k.arg:ast.literal_eval(k.value) for k in node.value.keywords}==plan_contract()
for original in sorted((w/'recontact_pose_groups_r1').glob('case_*/layout_*/quality.json')):
    original=original.parent;ep=fixture/original.parent.name/original.name;ep.mkdir(parents=True)
    with np.load(original/'raw.npz') as z:q=z['q'].copy();parent=z['action'].copy();meta=json.loads(str(z['collect_meta']));task=str(z['task_id'])
    u=parent.copy();meta.update(loaded_edge_coverage=True,loaded_edge_coverage_failure=None,coverage_fixture_only=True)
    waiting=task=='wait_no_package';rows=[];fr=None;coords=[]
    if not waiting:
        fr=json.loads((original/'frontal_bypass.json').read_text());coords=json.loads((original/'coordination.json').read_text());cs={r['step']:r for r in coords};pack=json.loads((original/'solved_contact_forces.json').read_text());packets={r['after_action_step']:r for r in pack['rows']};selected=bool(fr['plan'].get('rear_joint_edge_command',{}).get('enabled'))
        side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer'
        with np.load(original/'trace.npz') as z:xyz=z[key].copy()
        with np.load(original/'parcel_orientation.npz') as z:quat=z[key].copy()
        if selected:
            fr['plan']['loaded_edge_coverage']=plan_contract();fr['plan']['unloaded_recontact_pose']['original_loaded_math_unchanged']=False;core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];last=None
            for f in fr['rows']:
                t=f['step'];c=cs[t]
                if c.get('task_inputs') is not None:c['task_inputs']['previous']=u[t-1,12:23].tolist()
                c['joint_edge_refinement']['previous_upper_command']=u[t-1,12:23].tolist()
                command,tr=refine_record(enabled=True,selected=True,row=f,previous_row=last,coordinate=c,current=q[t,12:23],previous=u[t-1,12:23],parent_command=parent[t,12:23],packet=packets[t-1],object_xyz=xyz[t],object_rotation=rotation_xyzw(quat[t].tolist()),core_size=core,model=guard.model,geometry=guard.geometry,side=side)
                assert command is not None,(ep.name,t,tr['reason']);u[t,12:23]=command;rows.append(tr);c['loaded_edge_coverage']=tr;last=f
        (ep/'frontal_bypass.json').write_text(json.dumps(fr));(ep/'coordination.json').write_text(json.dumps(coords));(ep/'solved_contact_forces.json').write_text(json.dumps(pack));np.savez(ep/'trace.npz',**{key:xyz});np.savez(ep/'parcel_orientation.npz',**{key:quat})
    np.savez(ep/'raw.npz',q=q,action=u,collect_meta=json.dumps(meta),task_id=task)
    (ep/'loaded_edge_coverage.json').write_text(json.dumps(dict(rows=rows,failure=None,fixture_only=True)))
    finals=[dict(step=t,phase='final_command',accepted=True,command=u[t,12:23].tolist(),current=q[t,12:23].tolist(),previous=u[t-1,12:23].tolist() if t else [0.]*11) for t in range(len(q))]
    (ep/'self_clearance.json').write_text(json.dumps(dict(rows=finals,failure=None,recorded_frames=len(q),requested_frames=len(q),fixture_only=True)))
    result=verify_files(ep,stage);assert result['passed'];records.append(dict(episode=ep.name,fixture=str(ep),frames=result['frames'],decisions=result['decision_frames'],overrides=result['overrides']));print(ep.name,result['frames'],result['decision_frames'],result['overrides'],flush=True)
    if rows and not negative:
        cases=[]
        def mutate(name,file,fn):cases.append((name,file,fn))
        mutate('missing_row','loaded_edge_coverage.json',lambda d:d['rows'].pop())
        mutate('duplicate_row','loaded_edge_coverage.json',lambda d:d['rows'].append(copy.deepcopy(d['rows'][0])))
        mutate('explicit_stop','loaded_edge_coverage.json',lambda d:d.__setitem__('failure',{'step':50,'reason':'test'}))
        mutate('coord_trace_mismatch','coordination.json',lambda d:d[0]['loaded_edge_coverage'].__setitem__('reason','false'))
        mutate('wrong_final_command','self_clearance.json',lambda d:d['rows'][1]['command'].__setitem__(0,.1))
        mutate('false_final_guard','self_clearance.json',lambda d:d['rows'][1].__setitem__('accepted',False))
        mutate('wrong_frame_budget','self_clearance.json',lambda d:d.__setitem__('requested_frames',1199))
        mutate('relaxed_threshold','frontal_bypass.json',lambda d:d['plan']['loaded_edge_coverage'].__setitem__('final_float32_stationarity_threshold',1e-5))
        mutate('wrong_parent_chain','coordination.json',lambda d:d[0]['joint_edge_refinement']['final_upper_command'].__setitem__(0,.1))
        for name,file,fn in cases:
            path=ep/file;original_bytes=path.read_bytes();d=json.loads(original_bytes);fn(d);path.write_text(json.dumps(d))
            try:
                try:bad=verify_files(ep,stage)
                except (AssertionError,KeyError):negative.append(name)
                else:assert not bad['passed'],name;negative.append(name)
            finally:path.write_bytes(original_bytes)
        path=ep/'raw.npz';original_bytes=path.read_bytes()
        try:
            for name,qq,uu,mm in [('short_raw',q[:-1],u[:-1],meta),('nonzero_initial',q.copy(),u.copy(),meta),('assist',q,u,dict(meta,assist_frames=1))]:
                if name=='nonzero_initial':qq[0,12]=.1
                np.savez(path,q=qq,action=uu,collect_meta=json.dumps(mm),task_id=task)
                try:verify_files(ep,stage)
                except AssertionError:negative.append(name)
                else:raise AssertionError(name)
        finally:path.write_bytes(original_bytes)
    for name in ['raw.npz','frontal_bypass.json','coordination.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']:
        p=original/name
        if p.exists():sources[str(p)]=sha(p)
assert len(records)==10 and sum(r['frames'] for r in records)==9740 and len(negative)==12
for p in [Path(__file__),w/'audit_loaded_edge_coverage_live.py',w/'audit_loaded_edge_pose_live.py',w/'audit_recontact_pose_live.py',w/'audit_loaded_edge_coverage_decision.py',w/'audit_loaded_edge_coverage_record.py',stage/'collect_paired_sorting.py',stage/'loaded_edge_coverage_adapter.py',stage/'loaded_edge_coverage_current_contact.py',stage/'clearance_runtime.py',stage/'articulated_hand_geometry.py',stage/'self_clearance.py',stage/'elbow_torso_hulls.json',repo/'simfoundry/data/top_contact_bypass.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py']:
    sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_root=str(fixture),records=records,negative_checks=negative,original_unloaded_math_ast_exact=True,actual_plan_contract_exact=True,source_sha256=sources,physical_validation=False,training_ready=False)
(stage/'NATIVE_FILES_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(records),len(negative),flush=True)
