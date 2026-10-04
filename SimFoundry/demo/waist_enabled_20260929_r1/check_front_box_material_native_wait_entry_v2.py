"""Explicit temporary source/unchanged-wait fixture, never candidate physics.
Old wait states/actions/contacts are copied unchanged. Only declared source,
new flag and new unchanged-decision log are constructed for contract checks.
Default execution CLI rejects this fixture's marker. No push trajectory is made.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,tempfile,os,shutil,ast
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_material_preload';P=W/'staged_front_corridor_midpoint_integrated';C=W/'front_corridor_midpoint_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
from front_box_material_stage_source_binding import verify_trial_provenance,verify_observation_binding
from audit_front_box_material_execution import inspect
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};positive=[];negative=[]
def reject(name,call):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(('negative accepted',name))
for case in sorted(C.glob('case_*')):
 if (case/'provenance.json').exists():reject('old_original_source_'+case.name,lambda case=case:verify_trial_provenance(case))
oldcase=C/'case_841010';oldep=oldcase/'layout_841010_wait_no_package';prov=json.loads((oldcase/'provenance.json').read_text());oldprefix=str(P.relative_to(ROOT))+'/';newprefix=str(S.relative_to(ROOT))+'/'
with tempfile.TemporaryDirectory(prefix='front_midpoint_source_fixture_') as temporary:
 case=Path(temporary)/'case_841010';ep=case/oldep.name;ep.mkdir(parents=True);(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
 new=copy.deepcopy(prov);new['args']['front_box_material_preload']=True;new['source_sha256']={}
 for name,h in prov['source_sha256'].items():
  if name.startswith(oldprefix):continue
  source=oldcase/'source_snapshot'/name;assert sha(source)==h;sources[str(source)]=h;dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest);new['source_sha256'][name]=h
 prepared=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())
 for name,h in prepared['stage_sha256'].items():
  p=S/name
  assert sha(p)==h;name=newprefix+Path(p).name;dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);new['source_sha256'][name]=h
 def saveprov(value): (case/'provenance.json').write_text(json.dumps(value))
 saveprov(new);verify_trial_provenance(case);positive.append('all73_stage_sources_bound')
 for n in ['front_box_material_preload','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','expert_top_contact_normal_hold']:
  bad=copy.deepcopy(new);bad['args'][n]=False;saveprov(bad);reject('flag_'+n,lambda:verify_trial_provenance(case))
 bad=copy.deepcopy(new);bad['args']['steps']=1199;saveprov(bad);reject('changed_original_horizon',lambda:verify_trial_provenance(case))
 bad=copy.deepcopy(new);bad['source_sha256'].pop(newprefix+'loaded_z_priority_checks.py');saveprov(bad);reject('missing_candidate_verifier_source',lambda:verify_trial_provenance(case))
 bad=copy.deepcopy(new);bad['source_sha256'][newprefix+'front_loaded_z_priority.py']='0'*64;saveprov(bad);reject('wrong_candidate_source_hash',lambda:verify_trial_provenance(case))
 saveprov(new)
 runtime=json.loads((oldcase/'SUBSTEP_RUNTIME_BINDING.json').read_text());sources[str(oldcase/'SUBSTEP_RUNTIME_BINDING.json')]=sha(oldcase/'SUBSTEP_RUNTIME_BINDING.json');runtime['source_files']={str(S/Path(p).name) if Path(p).parent==P else p:v for p,v in runtime['source_files'].items()}
 for value in runtime['source_files'].values():
  src=oldcase/value['snapshot'];dest=case/value['snapshot'];dest.parent.mkdir(parents=True,exist_ok=True);os.link(src,dest);sources[str(src)]=sha(src)
 (case/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(runtime))
 os.link(oldcase/'runtime_collision_arrays.npz',case/'runtime_collision_arrays.npz');sources[str(oldcase/'runtime_collision_arrays.npz')]=sha(oldcase/'runtime_collision_arrays.npz')
 for name in ['trace.npz','quality.json','substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','peak_load_updates.json','front_initial_center.json','self_clearance.json','solved_contact_forces.json']:
  os.link(oldep/name,ep/name);sources[str(oldep/name)]=sha(oldep/name)
 if (oldep/'coordination.json').exists():shutil.copyfile(oldep/'coordination.json',ep/'coordination.json')
 with np.load(oldep/'raw.npz',allow_pickle=False) as z:raw={k:z[k].copy() for k in z.files}
 meta=json.loads(str(raw['collect_meta']));meta['front_box_material_preload']=prepared['specification'];meta['front_box_material_preload_applied_frames']=0;raw['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**raw);sources[str(oldep/'raw.npz')]=sha(oldep/'raw.npz')
 log=json.loads((oldep/'front_loaded_z_priority.json').read_text());(ep/'front_loaded_z_priority.json').write_text(json.dumps(log));sources[str(oldep/'front_loaded_z_priority.json')]=sha(oldep/'front_loaded_z_priority.json')
 binding=verify_observation_binding(ep);assert binding['passed'];positive.append('original_observation_contract_retained')
 result=inspect(ep,allow_source_fixture=True);assert result['passed'] and result['fixture_only'] and not result['physical_execution_evidence'] and result['frames']==70 and result['loaded_z_applied']==0;positive.append('complete_unchanged_wait_execution_fixture70')
 reject('default_cli_rejects_synthetic_fixture',lambda:inspect(ep))
 for name,mutate in [('missing_frame',lambda x:x['rows'].pop()),('duplicate_frame',lambda x:x['rows'].__setitem__(1,x['rows'][0])),('wrong_previous',lambda x:x['rows'][10]['context']['previous'].__setitem__(0,.01)),('wrong_decision',lambda x:x['rows'][10].__setitem__('reason','not_top_push')),('wrong_output',lambda x:x['rows'][10]['output_command'].__setitem__(0,.01))]:
  bad=copy.deepcopy(log);mutate(bad);(ep/'front_loaded_z_priority.json').write_text(json.dumps(bad));reject(name,lambda:inspect(ep,allow_source_fixture=True))
 (ep/'front_loaded_z_priority.json').write_text(json.dumps(log))
 for name,value in [('missing_material_specification',None),('false_material_count',1)]:
  bad_meta=copy.deepcopy(meta)
  if value is None:bad_meta.pop('front_box_material_preload')
  else:bad_meta['front_box_material_preload_applied_frames']=value
  bad_raw=dict(raw);bad_raw['collect_meta']=np.array(json.dumps(bad_meta));np.savez_compressed(ep/'raw.npz',**bad_raw);reject(name,lambda:verify_observation_binding(ep))
 np.savez_compressed(ep/'raw.npz',**raw)
 with np.load(ep/'raw.npz') as z:
  with np.load(oldep/'raw.npz') as old:
   for key in old.files:
    if key!='collect_meta':assert np.array_equal(z[key],old[key]),key
 positive.append('all_original_raw_arrays_unchanged')
 from audit_front_box_material_v1_stage_pose_live import source_contract
 assert source_contract(ep)==S;positive.append('native_pose_source_contract')
 import subprocess
 with (ep/'wait_cli.log').open('x') as log:
  subprocess.run([sys.executable,str(W/'audit_normal_wait.py'),str(ep)],stdout=log,stderr=subprocess.STDOUT,check=True)
 assert json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text())['passed'] is True;positive.append('native_wait_stability_cli')
 from audit_front_box_material_v1_stage_contacts import audit as contacts
 from audit_front_box_material_v1_stage_pressure import audit as pressure
 from audit_front_box_material_v1_stage_release import audit as release
 for name,fn in [('contacts',contacts),('pressure',pressure),('release',release)]:
  report=fn(ep);assert report['passed'] is True;positive.append('native_'+name+'_unchanged_wait')

for p,h in sources.items():assert sha(p)==h,p
for name in ['check_front_box_material_native_wait_entry_v2.py','front_box_material_stage_source_binding.py','audit_front_box_material_execution.py','audit_front_box_material_z_execution.py','front_loaded_z_priority_episode_inputs.py','audit_front_loaded_z_priority_record.py']:sources[str(W/name)]=sha(W/name)
sources[str(S/'PARSER_DISPATCH_CHECK.json')]=sha(S/'PARSER_DISPATCH_CHECK.json');sources[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,positive=positive,negative=negative,source_sha256=sources,temporary_fixture_removed=True,new_physical_started=False,full_audit_chain_ready=False,training_ready=False)
p=S/'NATIVE_WAIT_ENTRY_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,positive=positive,negative_cases=len(negative),fixture_removed=True,physical_started=False),indent=2))
