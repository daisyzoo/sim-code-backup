"""Explicit temporary new-source wait fixture; original arrays remain unchanged.
Tests provenance and metadata only, never native physical candidate success.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,tempfile,shutil,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v2';sys.path[:0]=[str(W),str(ROOT)]
from inactive_transport_stage_source_binding_v2 import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding
from audit_inactive_transport_stream_v2 import inspect
from audit_inactive_transport_a3_v2_execution import inspect as inspect_parent_execution
from inactive_transport_command_ledger_v2 import load_transport_ledger
from audit_inactive_transport_a3_v3_stage_self_clearance import audit as audit_clearance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();assert len(expected)==88
original=W/'front_box_recenter_physical_r2/case_841011';name='layout_841011_wait_no_package';before=sha(original/name/'raw.npz');spec=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['spec'];negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Accepted wrong binding '+label)
reject('old_parent_source',lambda:verify_trial_provenance(original))
with tempfile.TemporaryDirectory(prefix='inactive_transport_source_fixture_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;oldstage=W/'staged_front_box_recenter_v3';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=json.loads(p.read_text());p.unlink();prov['args']['inactive_transport_clearance']=True;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(rp.read_text());rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False)))
 with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
 q,u=arrays['q'][:,12:23],arrays['action'][:,12:23];meta=json.loads(str(arrays['collect_meta']));meta.update(inactive_transport_clearance=spec,inactive_transport_applied_frames=0);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz') as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 rows=[dict(step=t,selected=False,applied=False,version=spec['version'],parent_command=u[t].tolist(),output_command=u[t].tolist(),training_ready=False,reason='not_captured_front_transport',collector_context=dict(side='left',current=q[t].tolist(),previous_q=None if t==0 else q[t-1].tolist(),previous_command=np.zeros(11).tolist() if t==0 else u[t-1].tolist(),scene=None,decay=None)) for t in range(len(q))]
 data=dict(rows=rows,spec=spec,training_ready=False);record=ep/'inactive_transport_clearance.json';record.write_text(json.dumps(data));verify_trial_provenance(case);result=verify_observation_binding(ep);assert result['passed']
 stream_result=inspect(ep,fixture_only=True);assert stream_result['passed'] and stream_result['frames']==70 and stream_result['applied']==0 and not stream_result['physical_candidate_verified']
 reject('fixture_in_physical_entry',lambda:inspect(ep))
 (ep/'INACTIVE_TRANSPORT_STREAM_V2_AUDIT.json').write_text(json.dumps(stream_result))
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,u)
 parent_execution=inspect_parent_execution(ep,allow_source_fixture=True);assert parent_execution['passed'] and parent_execution['fixture_only'] and not parent_execution['physical_execution_evidence']
 reject('ledger_default_rejects_fixture',lambda:load_transport_ledger(ep))
 reject('parent_execution_default_rejects_fixture',lambda:inspect_parent_execution(ep))
 reject('self_clearance_default_rejects_fixture',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))
 for k,v in [('inactive_transport_clearance',False),('front_box_recenter',False),('push_assist',True),('steps',300)]:
  a=copy.deepcopy(prov['args']);a[k]=v;reject('setting_'+k,lambda:verify_settings(a))
 for k,v in [('measured_inactive_floor_m',.839),('nominal_predicted_floor_m',.840),('elbow_gap_m',.004),('stationarity_max',1e-5)]:
  m=copy.deepcopy(meta);m['inactive_transport_clearance'][k]=v;np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('metadata_'+k,lambda:verify_observation_binding(ep))
 np.savez_compressed(ep/'raw.npz',**arrays)
 for label in ['missing_step','wrong_output','wrong_previous','wrong_current','wrong_version','wrong_count']:
  d=copy.deepcopy(data)
  if label=='missing_step':d['rows'].pop(20)
  elif label=='wrong_output':d['rows'][20]['output_command'][3]=.001
  elif label=='wrong_previous':d['rows'][20]['collector_context']['previous_command'][3]=.001
  elif label=='wrong_current':d['rows'][20]['collector_context']['current'][3]=.001
  elif label=='wrong_version':d['rows'][20]['version']='other'
  else:d['rows'][20]['applied']=True
  record.write_text(json.dumps(d));reject(label,lambda:verify_observation_binding(ep))
 record.write_text(json.dumps(data))
 changed=case/'source_snapshot'/prefix/'inactive_transport_runtime.py';changed.write_text(changed.read_text()+'\n# fixture tamper\n');reject('snapshot_tamper',lambda:verify_trial_provenance(case))
assert sha(original/name/'raw.npz')==before
out=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage_sources=88,fixture_frames=len(q),negative_cases=negative,original_physical_arrays_identical=True,temporary_fixture_removed=True,source_sha256={**bound,**{str(p):sha(p) for p in [Path(__file__),W/'inactive_transport_stage_source_binding_v2.py',W/'audit_inactive_transport_stream_v2.py',W/'inactive_transport_command_ledger_v2.py',W/'audit_inactive_transport_a3_v2_execution.py',W/'audit_inactive_transport_a3_v2_z_execution.py',W/'inactive_transport_a3_loaded_episode_inputs.py',S/'AUDIT_FAMILY_V3_IMPORT_CHECK.json',S/'SOURCE_BINDING_PREPARATION.json',original/name/'raw.npz']}},native_wait_stream=stream_result,parent_execution=parent_execution,parent_ledger=ledger,full_parent_audit_family_ready=False,physics_started=False,training_ready=False)
with (S/'FAMILY_NATIVE_WAIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,sources=88,fixture_frames=len(q),negative=len(negative))))
