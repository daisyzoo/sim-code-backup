"""Actual70 wait arrays with explicitly substituted candidate source metadata.
This temporary source-contract fixture is NOT candidate physics. Default real
execution rejects the fixture. Every modified hardlinked file is unlinked first.
"""
from pathlib import Path
import copy,datetime,hashlib,json,os,shutil,subprocess,sys,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_recenter_v3';R=W/'front_corridor_midpoint_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
from front_box_recenter_stage_source_binding import verify_trial_provenance,verify_observation_binding
from audit_front_box_recenter_a2_v2_execution import inspect
from audit_front_box_recenter_stream import audit as audit_stream
from audit_front_box_recenter_a2_v3_stage_self_clearance import audit as audit_clearance
from audit_front_box_recenter_a2_v1_stage_contacts import audit as audit_contacts
from audit_front_box_recenter_a2_v1_stage_pressure import audit as audit_pressure
from audit_front_box_recenter_a2_v1_stage_release import audit as audit_release
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();negative=[];sources={};results={}
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('unexpected acceptance '+label)
original=R/'case_841010';name='layout_841010_wait_no_package';raw_before=sha(original/name/'raw.npz');wait_report_before=sha(original/name/'WAIT_STABILITY_AUDIT.json')
with tempfile.TemporaryDirectory(prefix='front_recontact_declared_wait_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name
 provpath=case/'provenance.json';prov=json.loads(provpath.read_text());provpath.unlink();prov['args']['front_recontact_center_landing']=True;prov['args']['front_box_recenter']=True
 oldstage=W/'staged_front_corridor_midpoint_integrated';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
 for n,h in prep['stage_sha256'].items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);assert sha(dest)==h;prov['source_sha256'][prefix+n]=h
 provpath.write_text(json.dumps(prov));runtimepath=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(runtimepath.read_text());runtimepath.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};runtimepath.write_text(json.dumps(runtime))
 (case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
 with np.load(ep/'raw.npz',allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));meta.update(front_recontact_center_landing=True,front_recontact_center_failure=None,front_recontact_center_handovers=0,front_recontact_planning_headroom=json.loads((W/'staged_front_recontact_headroom/COLLECTOR_PREPARATION.json').read_text())['planning_headroom'],front_box_recenter=prep['box_recenter']);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz',allow_pickle=False) as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 (ep/'front_recontact_center.json').write_text(json.dumps(dict(selected=False,rows=[],training_ready=False)))
 verify_trial_provenance(case);assert verify_observation_binding(ep)['passed'];results['stream']=audit_stream(ep);assert results['stream']['passed'] and results['stream']['wait']
 results['execution']=inspect(ep,allow_source_fixture=True);assert results['execution']['passed'] and results['execution']['fixture_only'] and not results['execution']['physical_execution_evidence']
 reject('execution_rejects_fixture_by_default',lambda:inspect(ep))
 # Self-clearance correctly calls the default native execution gate; source
 # fixture must be rejected there too. Native geometry is tested by temporarily
 # removing ONLY the marker in this local fixture and immediately restoring it,
 # retaining explicit nonphysical labeling in this external check report.
 reject('self_clearance_rejects_fixture_by_default',lambda:audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={}))
 marker=case/'SOURCE_CONTRACT_FIXTURE.json';marker_bytes=marker.read_bytes();marker.unlink()
 try:results['self_clearance']=audit_clearance(ep,{},verified_front_events={},verified_front_recovery_events={})
 finally:marker.write_bytes(marker_bytes)
 assert results['self_clearance']['episode_clearance_passed']
 # Recreate the ordinary wait report only in fixture; never write original hardlink.
 (ep/'WAIT_STABILITY_AUDIT.json').unlink();proc=subprocess.run([sys.executable,str(W/'audit_normal_wait.py'),str(ep)],capture_output=True,text=True);assert proc.returncode==0,proc.stderr
 results['wait']=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());assert results['wait']['passed']
 for key,fn in [('contacts',audit_contacts),('pressure',audit_pressure),('release',audit_release)]:results[key]=fn(ep);assert results[key]['passed']
 for key,val in [('front_box_recenter',False),('front_recontact_center_landing',False),('front_recontact_center_landing',1),('front_cop_drive_step_m',.001),('steps',1199),('push_assist',True),('expert_frontal_top_load_n',6.)]:
  bad=copy.deepcopy(prov);bad['args'][key]=val;provpath.write_text(json.dumps(bad));reject('changed_'+key+'_'+str(val),lambda:verify_trial_provenance(case))
 provpath.write_text(json.dumps(prov));verify_trial_provenance(case)
 assert sha(original/name/'raw.npz')==raw_before and sha(original/name/'WAIT_STABILITY_AUDIT.json')==wait_report_before
 fixture_hashes={key:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest() for key,value in results.items()}
paths=[Path(__file__),S/'AUDIT_FAMILY_V2_PREPARATION.json',W/'front_box_recenter_stage_source_binding.py',W/'audit_front_box_recenter_a2_v2_execution.py',W/'audit_front_box_recenter_a2_v2_z_execution.py',W/'front_box_recenter_a2_loaded_episode_inputs.py',W/'audit_front_box_recenter_stream.py',W/'audit_front_box_recenter_a2_v3_stage_self_clearance.py',W/'audit_front_box_recenter_a2_v1_stage_contacts.py',W/'audit_front_box_recenter_a2_v1_stage_pressure.py',W/'audit_front_box_recenter_a2_v1_stage_release.py',W/'audit_normal_wait.py',original/'provenance.json',original/name/'raw.npz']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_frames=70,original_arrays_identical=True,original_raw_and_report_unchanged=True,temporary_fixture_removed=True,checks=list(results),result_hashes=fixture_hashes,negative_cases=negative,source_sha256={str(p):sha(p) for p in paths},new_physics=False,training_ready=False)
with (S/'NATIVE_WAIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,checks=len(results),negative=len(negative),original_arrays_identical=True)))
