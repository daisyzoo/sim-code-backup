"""Three explicit source-contract fixtures from actual1200-frame front/left/default-off rear pushes.
On/off metadata and source snapshots change; all physical arrays remain exact.
Fixture entry never supplies physical-candidate evidence or training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil,os,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_early_edge_v1';D=W/'rear_early_edge_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from rear_early_edge_stage_source_binding_v1 import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding
from audit_rear_early_edge_r1_stream_v2 import inspect
from audit_rear_early_edge_r1_v2_execution import inspect as inspect_execution
from rear_early_edge_r1_command_ledger_v2 import load_transport_ledger
from audit_rear_early_edge_r1_v3_stage_self_clearance import audit as audit_clearance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());expected,bound=verify_preparation();assert len(expected)==100
oldstage=W/'staged_front_box_trailing_v2';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/';spec=read(D/'STAGE_PREPARATION.json')['spec'];negative=[];results=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Accepted invalid fixture '+label)
for layout,task,enabled in [(840020,'push_box_to_bin',True),(840020,'nudge_mailer_to_bin',True),(840023,'push_box_to_bin',False)]:
 original=W/'front_box_trailing_physical_r2'/f'case_{layout}';name=f'layout_{layout}_{task}';before=sha(original/name/'raw.npz')
 reject('parent_source',lambda:verify_trial_provenance(original))
 with tempfile.TemporaryDirectory(prefix='rear_early_source_fixture_') as tmp:
  case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name
  p=case/'provenance.json';prov=read(p);p.unlink();prov['args']['rear_early_edge']=enabled;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
  used={n:h for n,h in expected.items() if enabled or n not in ['rear_cop_route_early.py','rear_early_edge_governor.py']}
  for n,h in used.items():
   dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);prov['source_sha256'][prefix+n]=h
  p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=read(rp);rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
  with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
  meta=json.loads(str(arrays['collect_meta']))
  if enabled:meta.update(rear_early_edge=spec,rear_early_edge_selected=False,rear_early_edge_candidate_selected_frames=0)
  arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
  with np.load(original/name/'raw.npz') as z:
   for k,v in arrays.items():
    if k!='collect_meta':np.testing.assert_array_equal(v,z[k])
  verify_trial_provenance(case);check=verify_observation_binding(ep);assert check['passed']
  result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and not result['physical_candidate_verified'];(ep/'REAR_EARLY_EDGE_R1_STREAM_V2_AUDIT.json').write_text(json.dumps(result))
  parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['fixture_only'];np.testing.assert_array_equal(parents,arrays['action'][:,12:23])
  execution=inspect_execution(ep,allow_source_fixture=True);assert execution['passed'] and not execution['physical_execution_evidence']
  for label,fn in [('stream',lambda:inspect(ep)),('ledger',lambda:load_transport_ledger(ep)),('execution',lambda:inspect_execution(ep)),('clearance',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))]:reject(f'{enabled}:physical_entry:{label}',fn)
  if enabled:
   for key,val in [('rear_early_edge_selected',True),('rear_early_edge_candidate_selected_frames',1),('rear_early_edge_candidate_selected_frames',False)]:
    m=copy.deepcopy(meta);m[key]=val;np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject(f'metadata:{key}:{val}',lambda:verify_observation_binding(ep))
   m=copy.deepcopy(meta);m['rear_early_edge']['warning_inset_m']=.03;np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('wrong_warning_margin',lambda:verify_observation_binding(ep))
  np.savez_compressed(ep/'raw.npz',**arrays)
  args=copy.deepcopy(prov['args']);args['rear_early_edge']=1;reject('nonbool_flag',lambda:verify_settings(args))
  changed=case/'source_snapshot'/prefix/'collect_paired_sorting.py';changed.write_text(changed.read_text()+'\n# fixture tamper\n');reject('snapshot_tamper',lambda:verify_trial_provenance(case))
  assert sha(original/name/'raw.npz')==before
  results.append(dict(enabled=enabled,stage_sources=len(used),frames=1200,episode=name,physical_arrays_unchanged=True,source_binding_passed=True,native_stream_passed=True,native_parent_execution_passed=True,fixture_only=True))
assert sha(original/name/'raw.npz')==before
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,cases=results,negative_rejections=negative,source_sha256={**bound,**{str(p):sha(p) for p in [Path(__file__),original/name/'raw.npz',D/'AUDIT_FAMILY_IMPORT_CHECK.json',W/'audit_rear_early_edge_r1_stream_v2.py',W/'rear_early_edge_r1_command_ledger_v2.py',W/'audit_rear_early_edge_r1_v2_execution.py']}},temporary_fixtures_removed=True,complete_new_runtime_chain_verified=False,physics_started=False,training_ready=False)
with (D/'NATIVE_UNCHANGED_PUSH_SOURCE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,cases=len(results),negative_rejections=len(negative))))
