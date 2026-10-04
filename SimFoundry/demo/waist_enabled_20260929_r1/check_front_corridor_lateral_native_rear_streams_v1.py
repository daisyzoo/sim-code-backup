"""Two complete actual1200-frame rear pushes with explicit new metadata fixtures.
All physical arrays remain byte-value identical; only source declarations and
new unchanged-command logs are synthesized. No front proposal trajectory claim.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,tempfile,shutil,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_corridor_lateral_stream_v2 import inspect
from audit_front_corridor_lateral_r1_v2_execution import inspect as inspect_parent
from front_corridor_lateral_command_ledger_v2 import load_transport_ledger
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();results=[];negative=[];sources={}
from front_corridor_lateral_stage_source_binding_v1 import verify_preparation
expected,bound=verify_preparation();spec=read(W/'joint_transport_reserve_preparation_r1/RUNTIME_CONTEXT_CHECK.json')['spec']
for case_id,task in [(840023,'push_box_to_bin'),(840020,'nudge_mailer_to_bin')]:
 original=W/'front_box_recenter_physical_r2'/f'case_{case_id}';name=f'layout_{case_id}_{task}';raw_before=sha(original/name/'raw.npz');co_before=sha(original/name/'coordination.json')
 assert read(original/name/'front_initial_center.json')['selected'] is False
 with tempfile.TemporaryDirectory(prefix='joint_transport_rear_fixture_') as tmp:
  case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;oldstage=W/'staged_front_box_recenter_v3';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
  p=case/'provenance.json';prov=read(p);p.unlink();prov['args']['front_corridor_lateral_replan']=True;prov['args']['joint_transport_clearance']=True;prov['args']['inactive_transport_clearance']=False;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
  for n,h in expected.items():
   if n in ['inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py']:continue
   dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);assert sha(dest)==h;prov['source_sha256'][prefix+n]=h
  p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=read(rp);rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
  with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
  q,u=arrays['q'][:,12:23],arrays['action'][:,12:23];assert len(q)==1200
  meta=json.loads(str(arrays['collect_meta']));meta.update(joint_transport_clearance=spec,joint_transport_applied_frames=0,front_corridor_lateral_replan=True,front_corridor_lateral_replanned_frames=0);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
  with np.load(original/name/'raw.npz') as z:
   for k,v in arrays.items():
    if k!='collect_meta':assert np.array_equal(z[k],v),k
  side='right' if task=='push_box_to_bin' else 'left';rows=[dict(step=t,selected=False,applied=False,version=spec['version'],parent_command=u[t].tolist(),output_command=u[t].tolist(),training_ready=False,reason='not_captured_front_transport',collector_context=dict(side=side,current=q[t].tolist(),previous_q=None if t==0 else q[t-1].tolist(),previous_command=np.zeros(11).tolist() if t==0 else u[t-1].tolist(),scene=None,decay=None)) for t in range(len(q))]
  record=ep/'joint_transport_clearance.json';record.write_text(json.dumps(dict(rows=rows,spec=spec,training_ready=False)))
  cp=ep/'coordination.json';coords=read(cp);cp.unlink()
  for c in coords:c['joint_transport_clearance']=rows[c['step']]
  cp.write_text(json.dumps(coords))
  result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and result['applied']==0
  (ep/'FRONT_CORRIDOR_LATERAL_STREAM_V2_AUDIT.json').write_text(json.dumps(result));parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);np.testing.assert_array_equal(parents,u)
  old=inspect_parent(ep,allow_source_fixture=True);assert old['passed'] and old['frames']==1200 and old['fixture_only'] and not old['physical_execution_evidence']
  for label,fn in [('stream_physical_entry',lambda:inspect(ep)),('ledger_physical_entry',lambda:load_transport_ledger(ep)),('parent_physical_entry',lambda:inspect_parent(ep))]:
   try:fn()
   except AssertionError:negative.append(dict(task=task,case=label,rejected=True))
   else:raise AssertionError(label)
  results.append(dict(task=task,frames=1200,unchanged_actual_arrays=True,transport_applied=0,parent_execution_passed=True,fixture_only=True,stream_result_sha256=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest(),parent_result_sha256=hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest()));print(json.dumps(results[-1]),flush=True)
 assert sha(original/name/'raw.npz')==raw_before and sha(original/name/'coordination.json')==co_before
 for p in [original/'provenance.json',original/name/'raw.npz',original/name/'coordination.json']:sources[str(p)]=sha(p)
for p in [Path(__file__),W/'front_corridor_lateral_preparation_r1/AUDIT_FAMILY_IMPORT_CHECK.json',W/'audit_front_corridor_lateral_stream_v2.py',W/'front_corridor_lateral_command_ledger_v2.py',W/'audit_front_corridor_lateral_r1_v2_execution.py',W/'audit_front_corridor_lateral_r1_v2_z_execution.py',W/'front_corridor_lateral_r1_loaded_episode_inputs.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=results,negative_cases=negative,source_sha256={**bound,**sources},temporary_fixtures_removed=True,new_front_trajectory_verified=False,physics_started=False,training_ready=False)
with (W/'front_corridor_lateral_preparation_r1/NATIVE_REAR_STREAM_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,complete_push_streams=2,frames=2400,negative=len(negative))))
