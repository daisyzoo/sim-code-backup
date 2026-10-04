"""Default-off full front stream compatibility with new-source fixture only.
All physical arrays and control records remain identical. No enabled candidate
rollout, candidate response or physical success is inferred from old future states.
"""
from pathlib import Path
import sys,json,hashlib,datetime,tempfile,shutil,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'front_corridor_lateral_preparation_r1';S=W/'staged_front_corridor_lateral_v1';sys.path[:0]=[str(W),str(ROOT)]
from front_corridor_lateral_stage_source_binding_v1 import verify_preparation,verify_trial_provenance,verify_observation_binding
from audit_front_corridor_lateral_stream_v2 import inspect
from audit_front_corridor_lateral_r1_v2_execution import inspect as inspect_parent
from front_corridor_lateral_command_ledger_v2 import load_transport_ledger
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
expected,bound=verify_preparation();assert len(expected)==92
original=W/'joint_transport_reserve_physical_r1/case_840023';name='layout_840023_nudge_mailer_to_bin';negative=[]
files=['raw.npz','frontal_bypass.json','coordination.json','joint_transport_clearance.json','expert_control.json'];before={n:sha(original/name/n) for n in files}
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(label)
 else:raise AssertionError('Fixture incorrectly accepted '+label)
with tempfile.TemporaryDirectory(prefix='front_lateral_defaultoff_fixture_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;oldstage=W/'staged_joint_transport_reserve_v1';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 p=case/'provenance.json';prov=read(p);p.unlink();prov['args']['front_corridor_lateral_replan']=False;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);assert sha(dest)==h;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=read(rp);rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,lateral_enabled=False)))
 for n,h in before.items():assert sha(ep/n)==h
 verify_trial_provenance(case);binding=verify_observation_binding(ep);assert binding['passed'];print('Source and observation bindings passed',flush=True)
 result=inspect(ep,fixture_only=True);assert result['passed'] and result['frames']==1200 and not result['physical_candidate_verified'];reject('physical_transport_entry',lambda:inspect(ep));(ep/'FRONT_CORRIDOR_LATERAL_STREAM_V2_AUDIT.json').write_text(json.dumps(result));print('Full transport fixture passed',flush=True)
 parents,ledger=load_transport_ledger(ep,allow_source_fixture=True);assert ledger['passed'] and ledger['fixture_only'];loaded=np.asarray([r['output_command'] for r in read(ep/'front_loaded_z_priority.json')['rows']],dtype=np.float32);np.testing.assert_array_equal(parents,loaded)
 parent=inspect_parent(ep,allow_source_fixture=True);assert parent['passed'] and parent['fixture_only'] and not parent['physical_execution_evidence'];reject('physical_ledger_entry',lambda:load_transport_ledger(ep));reject('physical_parent_entry',lambda:inspect_parent(ep))
 for n,h in before.items():assert sha(ep/n)==h
for n,h in before.items():assert sha(original/name/n)==h
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,frames=1200,lateral_enabled=False,raw_and_control_records_unchanged=True,temporary_fixture_removed=True,negative_cases=negative,transport_stream=result,parent_ledger=ledger,parent_execution=parent,source_sha256={**bound,**{str(p):sha(p) for p in [Path(__file__),W/'audit_front_corridor_lateral_stream_v2.py',W/'front_corridor_lateral_command_ledger_v2.py',W/'audit_front_corridor_lateral_r1_v2_execution.py',D/'AUDIT_FAMILY_IMPORT_CHECK.json',*[original/name/n for n in files]]}},physical_started=False,training_ready=False)
with (D/'NATIVE_FRONT_DEFAULTOFF_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,frames=1200,lateral_enabled=False,negative=len(negative))),flush=True)
