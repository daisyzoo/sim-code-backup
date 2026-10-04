"""Complete actual front transport stream with only new rear-policy/source metadata.
Physical arrays and every non-path joint field remain unchanged. Path certificates
are independently recomputed for bounded stage and labeled metadata-only. Temporary fixture,
not a changed-action trajectory or new physical task-success claim.
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
case_id=int(sys.argv[1]) if len(sys.argv)>1 else 840023;task='nudge_mailer_to_bin' if case_id==840023 else 'push_box_to_bin';assert case_id in (840023,840020)
original=W/'joint_transport_physical_r1'/f'case_{case_id}';name=f'layout_{case_id}_{task}';before=sha(original/name/'raw.npz');negative=[]
policy=dict(version='rear_box_trailing_preference_v1',offset_m=.020,world_direction=[0.,1.,0.],original_inset_m=.020,center_weight_per_m2=400.,not_physical_contact_proof=True,enabled=True,right_rear_recovery_only=True)
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Accepted invalid binding '+label)
reject('old_source',lambda:verify_trial_provenance(original))
with tempfile.TemporaryDirectory(prefix='rear_trailing_front_fixture_',dir='/tmp') as tmp:
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
 # Bind original completed independent stream proof before adapting only certificate metadata.
 original_proof=json.loads((original/name/'JOINT_TRANSPORT_STREAM_V1_AUDIT.json').read_text());assert original_proof['passed'] and not original_proof['fixture_only'] and original_proof['frames']==1200
 for file,h in original_proof['source_sha256'].items():assert sha(file)==h,file
 from joint_transport_paths import JointTransportPaths
 paths=JointTransportPaths(ROOT,S);jp=ep/'joint_transport_clearance.json';joint=json.loads(jp.read_text());jp.unlink();certificate_changes=[]
 for record in joint['rows']:
  if 'paths' not in record:continue
  proposal=record['proposal'];changed={}
  for label,old_certificate in record['paths'].items():
   end=proposal['command'] if label=='nominal' else proposal['predicted_q']
   fresh=paths.certify(proposal['current'],end,proposal['scene'])
   assert fresh['passed'] is old_certificate['passed'],('changed path decision',record['step'],label)
   certificate_changes.append(dict(step=record['step'],path=label,same_accept_reject=True,old_sha256=hashlib.sha256(json.dumps(old_certificate,sort_keys=True).encode()).hexdigest(),new_sha256=hashlib.sha256(json.dumps(fresh,sort_keys=True).encode()).hexdigest()))
   changed[label]=fresh
  record['paths']=changed
 jp.write_text(json.dumps(joint));cp=ep/'coordination.json';coords=json.loads(cp.read_text());cp.unlink()
 for c in coords:c['joint_transport_clearance']=joint['rows'][c['step']]
 cp.write_text(json.dumps(coords))
 # All non-path fields, including every input, proposal and output, must remain exact.
 original_joint=json.loads((original/name/'joint_transport_clearance.json').read_text())
 for a,b in zip(joint['rows'],original_joint['rows']):assert {k:v for k,v in a.items() if k!='paths'}=={k:v for k,v in b.items() if k!='paths'}
 original_coords=json.loads((original/name/'coordination.json').read_text())
 for a,b in zip(coords,original_coords):assert {k:v for k,v in a.items() if k!='joint_transport_clearance'}=={k:v for k,v in b.items() if k!='joint_transport_clearance'}
 print(json.dumps(dict(certificate_metadata_recomputed=len(certificate_changes),all_original_decisions_preserved=True)),flush=True)
 verify_trial_provenance(case);binding=verify_observation_binding(ep);assert binding['passed']
 result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and not result['physical_candidate_verified'];reject('physical_transport_entry',lambda:inspect(ep));(ep/'REAR_TRAILING_TRANSPORT_STREAM_V1_AUDIT.json').write_text(json.dumps(result))
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,arrays['action'][:,12:23])
 parent=inspect_parent(ep,allow_source_fixture=True);assert parent['passed'] and parent['fixture_only'] and not parent['physical_execution_evidence']
 reject('physical_ledger_entry',lambda:load_transport_ledger(ep));reject('physical_parent_entry',lambda:inspect_parent(ep));reject('physical_clearance_entry',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))
 from audit_rear_trailing_r1_v1_stage_pose_live import verify_files
 pose=verify_files(ep,S);assert pose['passed'] and pose['frames']==1200 and not pose['selected']
 print(json.dumps(dict(front_pose_verified=True,frames=1200,applied=result['applied'])),flush=True)
assert sha(original/name/'raw.npz')==before
files=[Path(__file__),W/'rear_trailing_stage_source_binding_v1.py',W/'audit_rear_trailing_transport_stream_v1.py',W/'rear_trailing_command_ledger_v1.py',W/'audit_rear_trailing_r1_v2_execution.py',W/'audit_rear_trailing_r1_v1_stage_pose_live.py',D/'AUDIT_FAMILY_IMPORT_CHECK.json',original/name/'raw.npz',original/name/'joint_transport_clearance.json',original/name/'coordination.json',original/name/'JOINT_TRANSPORT_STREAM_V1_AUDIT.json',D/'FRONT_CERTIFICATE_FORMAT_DIAGNOSIS.json']
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,active_stage_sources=97,fixture_frames=1200,certificate_changes=certificate_changes,non_path_records_unchanged=True,negative_cases=negative,original_arrays_unchanged=True,temporary_fixture_removed=True,transport_stream=result,front_pose=pose,parent_execution=parent,parent_ledger=ledger,source_sha256={**bound,**{str(p):sha(p) for p in files}},physical_started=False,training_ready=False)
with (D/f'NATIVE_FRONT_{case_id}_V2_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,frames=1200,negative=len(negative))),flush=True)
