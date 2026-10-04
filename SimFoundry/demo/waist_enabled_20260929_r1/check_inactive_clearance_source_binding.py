"""Synthetic new-source declaration on unchanged original70-frame wait arrays.
Tests strict provenance and metadata wiring; it is not new candidate physics.
"""
from pathlib import Path
import copy,json,hashlib,datetime,sys,tempfile,shutil,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';sys.path[:0]=[str(W),str(ROOT)]
from front_inactive_clearance_stage_source_binding import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected,bound=verify_preparation();assert len(expected)==79;prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());spec=prep['inactive_clearance'];headroom=json.loads((W/'staged_front_recontact_headroom/COLLECTOR_PREPARATION.json').read_text())['planning_headroom'];negative=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError('invalid binding accepted '+label)
original=W/'front_corridor_midpoint_physical_r1/case_841010';name='layout_841010_wait_no_package';before=sha(original/name/'raw.npz')
reject('old_headroom_source',lambda:verify_trial_provenance(W/'front_recontact_headroom_physical_r1/case_841010'))
with tempfile.TemporaryDirectory(prefix='inactive_clearance_source_fixture_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name;p=case/'provenance.json';prov=json.loads(p.read_text());p.unlink();oldstage=W/'staged_front_corridor_midpoint_integrated';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 prov['args'].update(front_recontact_center_landing=True,front_recontact_inactive_clearance=True);prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);assert sha(dest)==h;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));rp=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(rp.read_text());rp.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};rp.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False)))
 with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));meta.update(front_recontact_center_landing=True,front_recontact_center_failure=None,front_recontact_center_handovers=0,front_recontact_planning_headroom=headroom,front_inactive_clearance=spec);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz') as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 (ep/'front_recontact_center.json').write_text(json.dumps(dict(selected=False,rows=[],training_ready=False)))
 verify_trial_provenance(case);result=verify_observation_binding(ep);assert result['passed']
 for key,val in [('front_recontact_inactive_clearance',False),('front_recontact_center_landing',False),('front_cop_drive_step_m',.001),('steps',300),('push_assist',True)]:
  args=copy.deepcopy(prov['args']);args[key]=val;reject('setting_'+key,lambda:verify_settings(args))
 for key,val in [('version','other'),('original_measured_gate_m',.839),('recovery_measured_entry_m',.84),('preparation_nominal_predicted_height_m',.84),('shared_command_budget',241),('measured_only_recovery_entry',False),('unloaded_only',False)]:
  m=copy.deepcopy(meta);m['front_inactive_clearance'][key]=val;np.savez_compressed(ep/'raw.npz',**dict(arrays,collect_meta=np.array(json.dumps(m))));reject('metadata_'+key,lambda:verify_observation_binding(ep))
assert sha(original/name/'raw.npz')==before
files=[Path(__file__),S/'COLLECTOR_PREPARATION.json',S/'SOURCE_BINDING_PREPARATION.json',W/'front_inactive_clearance_stage_source_binding.py',original/name/'raw.npz']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,stage_sources=79,fixture_frames=70,original_physical_arrays_identical=True,temporary_fixture_removed=True,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},full_native_stream_ready=False,physical_started=False,training_ready=False)
with (S/'SOURCE_BINDING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,sources=79,negative=len(negative),original_arrays_identical=True)))
