"""Explicit temporary source/metadata fixture using unchanged actual70frame wait arrays.
Never physical evidence. Physical entries must reject the fixture marker.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime,tempfile,shutil,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'rear_trailing_contact_preparation_r1';S=W/'staged_rear_trailing_contact_v1';sys.path[:0]=[str(W),str(ROOT)]
from rear_trailing_stage_source_binding_v1 import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding
from audit_rear_trailing_transport_stream_v1 import inspect
from audit_rear_trailing_r1_v2_execution import inspect as inspect_parent
from rear_trailing_command_ledger_v1 import load_transport_ledger
from audit_rear_trailing_r1_v3_stage_self_clearance import audit as audit_clearance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();assert len(expected)==97
original=W/'joint_transport_physical_r1/case_841011';name='layout_841011_wait_no_package';before=sha(original/name/'raw.npz');negative=[]
policy=dict(version='rear_box_trailing_preference_v1',offset_m=.020,world_direction=[0.,1.,0.],original_inset_m=.020,center_weight_per_m2=400.,not_physical_contact_proof=True,enabled=True,right_rear_recovery_only=True)
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Accepted invalid binding '+label)
reject('old_source',lambda:verify_trial_provenance(original))
with tempfile.TemporaryDirectory(prefix='rear_trailing_wait_fixture_',dir='/tmp') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;oldstage=W/'staged_joint_transport_v1';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=json.loads(p.read_text());p.unlink();prov['args']['rear_box_trailing_preference']=True;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(rp.read_text());rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False)))
 with np.load(ep/'raw.npz',allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));meta['rear_box_trailing_preference']=policy;arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz',allow_pickle=False) as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 verify_trial_provenance(case);binding=verify_observation_binding(ep);assert binding['passed']
 result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==70 and result['applied']==0 and not result['physical_candidate_verified'];reject('physical_transport_entry',lambda:inspect(ep));(ep/'REAR_TRAILING_TRANSPORT_STREAM_V1_AUDIT.json').write_text(json.dumps(result))
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,arrays['action'][:,12:23])
 parent=inspect_parent(ep,allow_source_fixture=True);assert parent['passed'] and parent['fixture_only'] and not parent['physical_execution_evidence']
 reject('physical_ledger_entry',lambda:load_transport_ledger(ep));reject('physical_parent_entry',lambda:inspect_parent(ep));reject('physical_clearance_entry',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))
 for k,v in [('rear_box_trailing_preference',False),('push_assist',True),('steps',2400),('role','pilot')]:
  a=copy.deepcopy(prov['args']);a[k]=v;reject('setting_'+k,lambda:verify_settings(a))
 for label,changes in [('missing',None),('offset',dict(offset_m=.01)),('direction',dict(world_direction=[0.,-1.,0.])),('inset',dict(original_inset_m=.012)),('weight',dict(center_weight_per_m2=200.)),('enabled',dict(enabled=False)),('side_scope',dict(right_rear_recovery_only=False))]:
  m=copy.deepcopy(meta)
  if changes is None:m.pop('rear_box_trailing_preference')
  else:m['rear_box_trailing_preference'].update(changes)
  np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('metadata_'+label,lambda:verify_observation_binding(ep))
 np.savez_compressed(ep/'raw.npz',**arrays)
 # Mutation is confined to the new snapshot path; original hardlinked files are never modified.
 changed=case/'source_snapshot'/prefix/'trailing_contact_plan.py';changed.write_text(changed.read_text()+'\n# invalid fixture snapshot\n');reject('snapshot_tamper',lambda:verify_trial_provenance(case))
assert sha(original/name/'raw.npz')==before
files=[Path(__file__),W/'rear_trailing_stage_source_binding_v1.py',W/'audit_rear_trailing_transport_stream_v1.py',W/'rear_trailing_command_ledger_v1.py',W/'audit_rear_trailing_r1_v2_execution.py',D/'AUDIT_FAMILY_IMPORT_CHECK.json',original/name/'raw.npz']
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,active_stage_sources=97,fixture_frames=70,negative_cases=negative,original_arrays_unchanged=True,temporary_fixture_removed=True,transport_stream=result,parent_execution=parent,parent_ledger=ledger,source_sha256={**bound,**{str(p):sha(p) for p in files}},physical_started=False,training_ready=False)
with (D/'NATIVE_WAIT_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,frames=70,negative=len(negative))),flush=True)
