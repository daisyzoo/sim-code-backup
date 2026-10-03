"""Explicit temporary source/unchanged-wait fixture, never candidate physics.
Old wait states/actions/contacts are copied unchanged. Only declared source,
new flag and new unchanged-decision log are constructed for contract checks.
Default execution CLI rejects this fixture's marker. No push trajectory is made.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy,tempfile,os,shutil,ast
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_z_priority';P=W/'staged_front_initial_center';C=W/'front_initial_physical_r1';sys.path[:0]=[str(W),str(ROOT)]
from front_z_priority_stage_source_binding import verify_trial_provenance,verify_observation_binding
from audit_front_z_priority_execution import inspect
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};positive=[];negative=[]
def reject(name,call):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError):negative.append(dict(case=name,rejected=True))
 else:raise AssertionError(('negative accepted',name))
for case in sorted(C.glob('case_*')):
 if (case/'provenance.json').exists():reject('old_original_source_'+case.name,lambda case=case:verify_trial_provenance(case))
oldcase=C/'case_841010';oldep=oldcase/'layout_841010_wait_no_package';prov=json.loads((oldcase/'provenance.json').read_text());oldprefix=str(P.relative_to(ROOT))+'/';newprefix=str(S.relative_to(ROOT))+'/'
with tempfile.TemporaryDirectory(prefix='front_z_source_fixture_') as temporary:
 case=Path(temporary)/'case_841010';ep=case/oldep.name;ep.mkdir(parents=True);(case/'SOURCE_CONTRACT_FIXTURE.json').write_text(json.dumps(dict(fixture_only=True,physical_candidate=False,scope=__doc__)))
 new=copy.deepcopy(prov);new['args']['front_loaded_z_priority']=True;new['source_sha256']={}
 for name,h in prov['source_sha256'].items():
  if name.startswith(oldprefix):continue
  source=oldcase/'source_snapshot'/name;assert sha(source)==h;sources[str(source)]=h;dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest);new['source_sha256'][name]=h
 prepared=json.loads((S/'VALIDATED_PREPARATION.json').read_text())
 for p,h in prepared['source_sha256'].items():
  assert sha(p)==h;name=newprefix+Path(p).name;dest=case/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);new['source_sha256'][name]=h
 def saveprov(value): (case/'provenance.json').write_text(json.dumps(value))
 saveprov(new);verify_trial_provenance(case);positive.append('all70_stage_sources_bound')
 for n in ['front_loaded_z_priority','front_initial_center_landing','expert_top_contact_normal_hold']:
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
 for name in ['substep_contacts.npz','SUBSTEP_CONTACT_RECORDING.json','peak_load_updates.json','front_initial_center.json','self_clearance.json','solved_contact_forces.json']:
  os.link(oldep/name,ep/name);sources[str(oldep/name)]=sha(oldep/name)
 if (oldep/'coordination.json').exists():shutil.copyfile(oldep/'coordination.json',ep/'coordination.json')
 with np.load(oldep/'raw.npz',allow_pickle=False) as z:raw={k:z[k].copy() for k in z.files}
 meta=json.loads(str(raw['collect_meta']));meta['front_loaded_z_priority']=True;meta['front_loaded_z_priority_applied_frames']=0;raw['collect_meta']=np.array(json.dumps(meta));np.savez_compressed(ep/'raw.npz',**raw);sources[str(oldep/'raw.npz')]=sha(oldep/'raw.npz')
 replay=json.loads((W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json').read_text());entry=next(e for e in replay['episodes'] if e['episode']==oldep.name);log=dict(rows=[r['metadata'] for r in entry['rows']],training_ready=False,fixture_only=True);(ep/'front_loaded_z_priority.json').write_text(json.dumps(log));sources[str(W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json')]=sha(W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json')
 binding=verify_observation_binding(ep);assert binding['passed'];positive.append('original_observation_contract_retained')
 result=inspect(ep,allow_source_fixture=True);assert result['passed'] and result['fixture_only'] and not result['physical_execution_evidence'] and result['frames']==70 and result['applied']==0;positive.append('complete_unchanged_wait_execution_fixture70')
 reject('default_cli_rejects_synthetic_fixture',lambda:inspect(ep))
 for name,mutate in [('missing_frame',lambda x:x['rows'].pop()),('duplicate_frame',lambda x:x['rows'].__setitem__(1,x['rows'][0])),('wrong_previous',lambda x:x['rows'][10]['context']['previous'].__setitem__(0,.01)),('wrong_decision',lambda x:x['rows'][10].__setitem__('reason','not_top_push')),('wrong_output',lambda x:x['rows'][10]['output_command'].__setitem__(0,.01))]:
  bad=copy.deepcopy(log);mutate(bad);(ep/'front_loaded_z_priority.json').write_text(json.dumps(bad));reject(name,lambda:inspect(ep,allow_source_fixture=True))
 (ep/'front_loaded_z_priority.json').write_text(json.dumps(log))
 with np.load(ep/'raw.npz') as z:
  with np.load(oldep/'raw.npz') as old:
   for key in old.files:
    if key!='collect_meta':assert np.array_equal(z[key],old[key]),key
 positive.append('all_original_raw_arrays_unchanged')
for p,h in sources.items():assert sha(p)==h,p
for name in ['check_front_z_priority_source_contract.py','front_z_priority_stage_source_binding.py','audit_front_z_priority_execution.py','front_loaded_z_priority_episode_inputs.py','audit_front_loaded_z_priority_record.py']:sources[str(W/name)]=sha(W/name)
sources[str(S/'CHECK.json')]=sha(S/'CHECK.json');sources[str(S/'VALIDATED_PREPARATION.json')]=sha(S/'VALIDATED_PREPARATION.json')
a=next(n for n in ast.parse((W/'front_initial_center_stage_source_binding.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='verify_observation_binding');b=next(n for n in ast.parse((W/'front_z_priority_stage_source_binding.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_verify_original_observation_binding');b.name=a.name;assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,positive=positive,negative=negative,original_observation_ast_unchanged=True,source_sha256=sources,temporary_fixture_removed=True,new_physical_started=False,full_audit_chain_ready=False,training_ready=False)
p=W/'FRONT_Z_PRIORITY_SOURCE_CONTRACT_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,positive=positive,negative_cases=len(negative),fixture_removed=True,physical_started=False),indent=2))
