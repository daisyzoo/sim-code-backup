"""Independent-copy temporary source-contract wait fixture; no candidate physics.
Original arrays stay identical. Source provenance/window declarations change only
inside an independent file copy. No hardlinks or original-source writes are used.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(W),str(ROOT)]
from front_contact_window_stage_source_binding_v2 import verify_preparation,verify_observation_binding,verify_trial_provenance
from audit_front_window_stream_v2 import inspect as inspect_parent_stream
from front_window_command_ledger_v2 import load_transport_ledger
from audit_front_window_r1_v2_execution import inspect as inspect_execution
from audit_front_contact_window_stream_v1 import inspect as inspect_window
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();enabled='--disabled' not in sys.argv
if not enabled:
 for n in ['front_window_native_v4.py','contact_window_evidence_v2.py','window_initial_center_top_v2.py','window_initial_center_route_v2.py','window_initial_center_cop_v2.py']:expected.pop(n)
oldstage=W/'staged_front_loaded_z_quarter_v1';original=W/'front_loaded_z_quarter_physical_r2/case_841011';name='layout_841011_wait_no_package';before={str(p):sha(p) for p in [original/'provenance.json',original/'SUBSTEP_RUNTIME_BINDING.json',original/name/'raw.npz']};negative=[]
def reject(label,call):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError,AttributeError):negative.append(label)
 else:raise AssertionError('Accepted '+label)
with tempfile.TemporaryDirectory(prefix='window-wait-independent-copy-') as td:
 case=Path(td)/original.name;shutil.copytree(original,case,copy_function=shutil.copy2);ep=case/name;oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 # Check independence before any fixture mutation. Every copied regular file
 # owns a different inode; no test write can change a source through hardlinks.
 for p in case.rglob('*'):
  if p.is_file():assert not p.is_symlink() and p.stat().st_ino!=(original/p.relative_to(case)).stat().st_ino
 p=case/'provenance.json';prov=json.loads(p.read_text());prov['args']['front_contact_window']=enabled;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/n,dest);assert dest.stat().st_ino!=(S/n).stat().st_ino;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));p=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(p.read_text());runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};p.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False)))
 with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));log=None
 if enabled:
  meta['front_contact_window']=dict(version='front_window_native_v4',enabled=True,selected_front=False,recorded_intervals=0,training_ready=False);log=dict(version='front_window_native_v4',enabled=True,selected_front=False,rows=[],executed_frames=len(arrays['q']),training_ready=False);(ep/'front_contact_window.json').write_text(json.dumps(log))
 arrays['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz') as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 binding=verify_observation_binding(ep);assert binding['passed']
 stream=inspect_parent_stream(ep,fixture_only=True);assert stream['passed'] and stream['fixture_only'] and stream['frames']==70
 report=ep/'FRONT_WINDOW_PARENT_STREAM_V2_AUDIT.json';assert not report.exists();report.write_text(json.dumps(stream))
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,arrays['action'][:,12:23])
 execution=inspect_execution(ep,allow_source_fixture=True);assert execution['passed'] and execution['fixture_only'] and not execution['physical_execution_evidence']
 window=inspect_window(ep);assert window['passed'] and window['selected_front'] is False and window['enabled'] is enabled and window['task_success_proven'] is False
 reject('parent_stream_real_entry_rejects_fixture',lambda:inspect_parent_stream(ep));reject('ledger_real_entry_rejects_fixture',lambda:load_transport_ledger(ep));reject('parent_execution_real_entry_rejects_fixture',lambda:inspect_execution(ep))
 if enabled:
  for label,mutate in [('nonempty_wait_window',lambda d:d['rows'].append(dict(step=1))),('wait_selected_as_front',lambda d:d.update(selected_front=True)),('wrong_version',lambda d:d.update(version='wrong')),('wrong_frames',lambda d:d.update(executed_frames=69))]:
   bad=copy.deepcopy(log);mutate(bad);(ep/'front_contact_window.json').write_text(json.dumps(bad));reject(label,lambda:inspect_window(ep))
  (ep/'front_contact_window.json').unlink();reject('missing_enabled_log',lambda:inspect_window(ep));(ep/'front_contact_window.json').write_text(json.dumps(log))
 else:
  (ep/'front_contact_window.json').write_text('{}');reject('disabled_unexpected_log',lambda:inspect_window(ep));(ep/'front_contact_window.json').unlink()
 # Mutate only the independently copied temporary source snapshot.
 p=case/'source_snapshot'/prefix/'collect_paired_sorting.py';assert p.stat().st_ino!=(S/p.name).stat().st_ino;p.write_text(p.read_text()+'\n# intentionally damaged independent fixture\n');reject('changed_source_snapshot',lambda:verify_trial_provenance(case))
for p,h in before.items():assert sha(p)==h
paths=[Path(__file__),W/'audit_front_contact_window_stream_v1.py',W/'front_contact_window_stage_source_binding_v2.py',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,window_enabled=enabled,stage_sources=len(expected),frames=70,parent_stream_passed=True,parent_ledger_passed=True,parent_execution_passed=True,window_empty_stream_passed=True,negative_rejections=negative,source_sha256={**bound,**before,**{str(p):sha(p) for p in paths}},independent_copy_inodes_verified=True,missing_enabled_log_rejects_with_attribute_error=True,original_physical_arrays_identical=True,temporary_fixture_removed=True,actual_new_window_episode_audited=False,training_ready=False)
with (D/('NATIVE_WAIT_ENABLED_CHECK_V2.json' if enabled else 'NATIVE_WAIT_DISABLED_CHECK_V2.json')).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}))
