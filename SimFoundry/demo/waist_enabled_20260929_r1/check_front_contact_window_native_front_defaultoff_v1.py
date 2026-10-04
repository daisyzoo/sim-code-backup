"""Complete1200-frame default-off contract fixture using independent copies.
Original arrays and control streams are unchanged; explicitly not new physics.
The parent quarter-Z remains enabled, so only the new contact window is disabled.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_contact_window_preparation_r2';S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(W),str(ROOT)]
from front_contact_window_stage_source_binding_v2 import verify_preparation,verify_observation_binding
from audit_front_window_stream_v2 import inspect
from audit_front_window_r1_v2_execution import inspect as inspect_parent
from front_window_command_ledger_v2 import load_transport_ledger
from audit_front_contact_window_stream_v1 import inspect as inspect_window
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());expected,bound=verify_preparation()
for n in ['front_window_native_v4.py','contact_window_evidence_v2.py','window_initial_center_top_v2.py','window_initial_center_route_v2.py','window_initial_center_cop_v2.py']:expected.pop(n)
assert len(expected)==93
original=W/'front_loaded_z_quarter_physical_r2/case_840023';name='layout_840023_nudge_mailer_to_bin';oldstage=W/'staged_front_loaded_z_quarter_v1';files=['raw.npz','frontal_bypass.json','coordination.json','joint_transport_clearance.json','expert_control.json'];before={n:sha(original/name/n) for n in files};negative=[]
def reject(label,call):
 try:call()
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('Accepted fixture '+label)
with tempfile.TemporaryDirectory(prefix='window-front-independent-copy-') as tmp:
 case=Path(tmp)/original.name
 # Case metadata/snapshots and exactly the requested physical episode are copied;
 # unrelated paired episode and viewer images are not inputs to these audits.
 def ignored(directory,names):
  if Path(directory)==original:return [n for n in names if n.startswith('viewer_') or (n.startswith('layout_') and n!=name)]
  return []
 shutil.copytree(original,case,copy_function=shutil.copy2,ignore=ignored);ep=case/name
 for p in case.rglob('*'):
  if p.is_file():assert not p.is_symlink() and p.stat().st_ino!=(original/p.relative_to(case)).stat().st_ino
 prefix=str(S.relative_to(ROOT))+'/';oldprefix=str(oldstage.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=read(p);prov['args']['front_contact_window']=False;assert prov['args']['front_loaded_z_quarter'] is True;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(S/n,dest);assert dest.stat().st_ino!=(S/n).stat().st_ino;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));p=case/'SUBSTEP_RUNTIME_BINDING.json';r=read(p);r['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in r['source_files'].items()};p.write_text(json.dumps(r));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,window_enabled=False)))
 for n,h in before.items():assert sha(ep/n)==h
 binding=verify_observation_binding(ep);assert binding['passed'];print('SOURCE_BINDING_PASS',flush=True)
 result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and not result['physical_candidate_verified'];(ep/'FRONT_WINDOW_PARENT_STREAM_V2_AUDIT.json').write_text(json.dumps(result));print('FULL_TRANSPORT_STREAM_PASS',flush=True)
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];np.testing.assert_array_equal(parents,np.asarray([r['output_command'] for r in read(ep/'front_loaded_z_priority.json')['rows']],dtype=np.float32));print('PARENT_LEDGER_PASS',flush=True)
 execution=inspect_parent(ep,allow_source_fixture=True);assert execution['passed'] and execution['fixture_only'] and not execution['physical_execution_evidence'];print('PARENT_EXECUTION_PASS',flush=True)
 window=inspect_window(ep);assert window['passed'] and window['enabled'] is False and not window['task_success_proven']
 reject('physical_stream',lambda:inspect(ep));reject('physical_parent',lambda:inspect_parent(ep));reject('physical_ledger',lambda:load_transport_ledger(ep))
 for n,h in before.items():assert sha(ep/n)==h
for n,h in before.items():assert sha(original/name/n)==h
paths=[Path(__file__),W/'audit_front_contact_window_stream_v1.py',D/'AUDIT_FAMILY_PREPARATION.json',D/'AUDIT_FAMILY_IMPORT_INVENTORY_CHECK_V2.json',*[original/name/n for n in files]]
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,frames=1200,window_enabled=False,quarter_z_enabled=True,independent_copy_inodes_verified=True,raw_and_control_streams_unchanged=True,temporary_fixture_removed=True,transport_stream_passed=True,parent_ledger_passed=True,parent_execution_passed=True,window_disabled_stream_passed=True,negative_rejections=negative,source_sha256={**bound,**{str(p):sha(p) for p in paths}},physical_started=False,training_ready=False)
with (D/'NATIVE_FRONT_DEFAULTOFF_CHECK_V1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='source_sha256'}),flush=True)
