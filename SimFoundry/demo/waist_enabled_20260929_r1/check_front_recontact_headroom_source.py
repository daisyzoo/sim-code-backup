"""Verify new77-source configuration and explicitly synthetic source-contract wait.
Original70-frame physical arrays stay identical. This is not headroom physics,
full native execution audit, or permission to start a new experiment.
"""
from pathlib import Path
import copy,datetime,hashlib,json,os,shutil,sys,tempfile
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';P=W/'staged_front_recontact_center';sys.path[:0]=[str(W),str(ROOT)]
from front_recontact_headroom_stage_source_binding import verify_preparation,verify_settings,verify_trial_provenance,verify_observation_binding
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());expected,bound=verify_preparation();assert len(expected)==77;spec=prep['planning_headroom'];negative=[]
plan=json.loads((W/'front_recontact_preparation_r1/PLAN.json').read_text())
for c in plan['commands']:
 ns,_=parser_namespace(S/'collect_paired_sorting.py',c['args'],full=True);settings=semantic_settings(ns)
 for k in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(k) is True
 assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('invalid source accepted '+label)
reject('old77_source',lambda:verify_trial_provenance(W/'front_recontact_physical_r1/case_840022'))
original=W/'front_corridor_midpoint_physical_r1/case_841010';name='layout_841010_wait_no_package';before=sha(original/name/'raw.npz')
with tempfile.TemporaryDirectory(prefix='front_headroom_source_fixture_') as tmp:
 case=Path(tmp)/original.name;shutil.copytree(original,case,copy_function=os.link);ep=case/name
 p=case/'provenance.json';prov=json.loads(p.read_text());p.unlink();oldstage=W/'staged_front_corridor_midpoint_integrated';oldprefix=str(oldstage.relative_to(ROOT))+'/';prefix=str(S.relative_to(ROOT))+'/'
 prov['args']['front_recontact_center_landing']=True;prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if not k.startswith(oldprefix)}
 for n,h in expected.items():
  dest=case/'source_snapshot'/prefix/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/n,dest);assert sha(dest)==h;prov['source_sha256'][prefix+n]=h
 p.write_text(json.dumps(prov));runtimepath=case/'SUBSTEP_RUNTIME_BINDING.json';runtime=json.loads(runtimepath.read_text());runtimepath.unlink();runtime['source_files']={str(S/Path(k).name) if Path(k).parent==oldstage else k:v for k,v in runtime['source_files'].items()};runtimepath.write_text(json.dumps(runtime));(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False)))
 with np.load(ep/'raw.npz') as z:arrays={k:z[k].copy() for k in z.files}
 meta=json.loads(str(arrays['collect_meta']));meta.update(front_recontact_center_landing=True,front_recontact_center_failure=None,front_recontact_center_handovers=0,front_recontact_planning_headroom=spec);arrays['collect_meta']=np.array(json.dumps(meta));(ep/'raw.npz').unlink();np.savez_compressed(ep/'raw.npz',**arrays)
 with np.load(original/name/'raw.npz') as z:
  for k,v in arrays.items():
   if k!='collect_meta':assert np.array_equal(z[k],v),k
 (ep/'front_recontact_center.json').write_text(json.dumps(dict(selected=False,rows=[],training_ready=False)))
 verify_trial_provenance(case);result=verify_observation_binding(ep);assert result['passed']
 for key,val in [('front_cop_drive_step_m',.001),('front_recontact_center_landing',False),('front_loaded_z_priority',False),('front_corridor_midpoint_replan',False),('steps',300),('push_assist',True)]:
  args=copy.deepcopy(prov['args']);args[key]=val;reject('setting_'+key,lambda:verify_settings(args))
 for key,val in [('entry_inactive_height_m',.84),('nominal_predicted_inactive_height_m',.84),('original_measured_inactive_height_m',.839),('original_numerical_tolerance_m',.001),('version','other')]:
  bad=copy.deepcopy(meta);bad['front_recontact_planning_headroom'][key]=val;altered=dict(arrays,collect_meta=np.array(json.dumps(bad)));np.savez_compressed(ep/'raw.npz',**altered);reject('metadata_'+key,lambda:verify_observation_binding(ep))
assert sha(original/name/'raw.npz')==before
sources=[Path(__file__),S/'COLLECTOR_PREPARATION.json',S/'SOURCE_BINDING_PREPARATION.json',W/'front_recontact_headroom_stage_source_binding.py',W/'front_recontact_preparation_r1/PLAN.json']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runtime_sources=77,configuration_count=6,fixture_frames=70,original_physical_arrays_identical=True,original_raw_unchanged=True,negative_cases=negative,temporary_fixture_removed=True,source_sha256={str(p):sha(p) for p in sources},full_native_execution_audit_ready=False,simulation_started=False,training_ready=False)
with (S/'SOURCE_BINDING_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,sources=77,configurations=6,negative=len(negative),new_physics=False)))
