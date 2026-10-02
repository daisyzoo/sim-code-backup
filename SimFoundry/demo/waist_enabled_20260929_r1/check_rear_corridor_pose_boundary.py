"""New boundary and complete pose adapter checks; NO new physics or data admission.
Sparse synthetic branches check verified parent projection and pending causality.
Three full recorded no-request histories retain raw files byte-for-byte; adding
an unchanged boundary log tests integration only, not new controller trajectories.
"""
from pathlib import Path
import json,sys,hashlib,datetime,os,copy,tempfile,shutil
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from rear_corridor_audit_inputs import verify_inputs
from audit_rear_corridor_stage_pose_live import verify_files,source_contract
from audit_joint_edge_stage_pose_live_v2 import verify_files as parent_files
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dest=W/'REAR_CORRIDOR_POSE_BOUNDARY_CHECK.json';assert not dest.exists()
tmp=Path(tempfile.mkdtemp(prefix='rear_pose_boundary_NO_PHYSICS_'));rows=[];negative=[];sources={}
frozen={str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_audit_inputs.py',W/'audit_rear_corridor_stage_pose_live.py',W/'audit_rear_corridor_transport_events_v2.py',W/'REAR_CORRIDOR_POSE_AUDIT_PREPARATION.json',W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json']}
def save(status,**extra):
    p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_root=str(tmp),rows=rows,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**extra),indent=2));p.replace(dest)
def refused(fn,label):
    try:fn()
    except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:negative.append(dict(case=label,error_type=type(e).__name__))
    else:raise AssertionError('invalid evidence accepted '+label)
def clone(src,dst):
    dst.mkdir()
    for p in src.iterdir():
        if p.is_file():shutil.copy2(p,dst/p.name)
try:
    save('running')
    fixture=json.loads((W/'REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json').read_text())
    for case in fixture['cases']:
        if case['kind']=='wait':continue
        src=Path(case['fixture']);ep=tmp/src.name;clone(src,ep);v=verify_inputs(ep,ROOT,S);assert len(v.overrides)==1
        t=case['source_step'];r=v.overrides[t];fr=json.loads((ep/'frontal_bypass.json').read_text());f=next(x for x in fr['rows'] if x['step']==t);ex=json.loads((ep/'expert_control.json').read_text())[0]
        assert v.parent_row(t,f)==r['parent_row'];px=v.parent_expert(t,ex);assert px['mode']==r['parent_row']['mode'] and px['target_xyz']==r['parent_row']['target_xyz']
        with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].copy()
        assert np.array_equal(v.parent_command(t,u[t]),r['parent_command'])
        # Following step gets actual emitted command as previous, never the parent's.
        assert np.array_equal(v.parent_command(t+1,u[t+1]),u[t+1]);assert not np.array_equal(u[t],r['parent_command'])
        assert v.required_transport_steps==(frozenset([t+1]) if case['kind']=='unload' else frozenset())
        mutated=v.parent_row(t,f);mutated['mode']='CORRUPTED';assert v.parent_row(t,f)==r['parent_row']
        refused(lambda:verify_files(ep,S),src.name+'_sparse_fixture_not_full_pose')
        original=(ep/'expert_control.json').read_bytes();(ep/'expert_control.json').write_bytes(original+b' ');refused(v.assert_unchanged,src.name+'_changed_native_file');(ep/'expert_control.json').write_bytes(original);v.assert_unchanged()
        if case['kind']=='unload':
            original=(ep/'rear_corridor_recovery.json').read_bytes();bad=json.loads(original);bad['handovers']=[];(ep/'rear_corridor_recovery.json').write_text(json.dumps(bad));refused(lambda:verify_inputs(ep,ROOT,S),'missing_pending_handover');(ep/'rear_corridor_recovery.json').write_bytes(original)
        rows.append(dict(case=src.name,parent_projection_verified=True,raw_action_unchanged=True,required_transport_steps=sorted(v.required_transport_steps),synthetic=True));save('running');print('boundary',src.name,flush=True)
    histories=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text())['episodes']
    for item in histories:
        if item['rows']:continue
        src=W/item['episode'];ep=tmp/src.name;ep.mkdir()
        # Hard links preserve potentially large native logs. Never modify linked files.
        for p in src.iterdir():
            if p.is_file():os.link(p,ep/p.name)
        assert not (ep/'rear_corridor_recovery.json').exists()
        with np.load(ep/'raw.npz') as z:u=z['action'][:,12:23].copy()
        fr=json.loads((ep/'frontal_bypass.json').read_text());cs={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};rr=[]
        for f in fr['rows']:
            t=f['step'];c=cs[t]
            if f['mode']!='top_push' or f.get('route_stop_reason') or f.get('release_reason') or c.get('region_joint_override') or c.get('terminal_joint_hold'):reason='original_mode_guard'
            elif not f.get('rear_cop_centering',{}).get('override'):reason='original_contact_or_first_load_guard'
            else:reason='no_rear_corridor_deficit'
            rr.append(dict(step=t,kind='unchanged',recovery=dict(applied=False,reason=reason),parent_command=u[t].tolist()))
        (ep/'rear_corridor_recovery.json').write_text(json.dumps(dict(rows=rr,handovers=[],executed_action_count=len(u),pending_recontact=False,training_ready=False)))
        baseline=parent_files(ep,S);actual=verify_files(ep,S);assert {k:v for k,v in actual.items() if k not in ('recovery_boundary','required_transport_steps')}==baseline
        assert actual['recovery_boundary']['overrides']==0 and not actual['required_transport_steps']
        refused(lambda:source_contract(ep),'historical_data_cannot_claim_new_provenance_'+src.name)
        for n in ['raw.npz','frontal_bypass.json','coordination.json','recontact_pose.json','expert_control.json','peak_load_updates.json']:sources[str(src/n)]=sha(src/n)
        rows.append(dict(case=item['episode'],frames=actual['frames'],unchanged_full_pose_equal=True,command_events=actual['command_events'],historical_not_new_physics=True));save('running');print('native pose',src.name,flush=True)
    for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
    save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
