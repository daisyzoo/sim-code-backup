"""Derive diagnostic run/watch/review wrappers; no launch, no training admission."""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;P=W/'front_normal_physical_preparation_r3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mapping={
 'front_effective_height_physical_preparation_r2':'front_normal_physical_preparation_r3',
 'front_effective_height_physical_r1':'front_normal_physical_r1',
 'front_effective_height_stage_source_binding_v1':'front_normal_stage_source_binding_v3',
 'front_effective_height_r1_v4_stage_run_contract':'front_normal_stage_run_contract_v1',
 'audit_front_effective_height_r1_v1_stage_contract':'audit_front_normal_stage_contract_v2',
 'audit_front_effective_height_r1_v1_stage_contacts':'audit_front_normal_contacts_v2',
 'audit_front_effective_height_r1_v1_stage_pressure':'audit_front_normal_pressure_files_v1',
 'audit_front_effective_height_r1_v1_stage_release':'audit_front_normal_stage_r1_v1_stage_release',
 'run_front_effective_height_trial1_physical_r2':'run_front_normal_trial1_physical_v1',
 'watch_front_effective_height_trial1_physical_audits_r2':'watch_front_normal_trial1_physical_audits_v1',
 'watch_front_effective_height_trial1_numeric_reviews_r2':'watch_front_normal_trial1_numeric_reviews_v1',
 'review_front_effective_height_trial1_v1_stage_episode':'review_front_normal_trial1_episode_v1',
 'review_front_effective_height_trial1_incomplete_episode':'review_front_normal_trial1_incomplete_episode_v1',
 'FRONT_EFFECTIVE_HEIGHT_R1':'FRONT_NORMAL_R1',
}
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
files=[]
for name in ['watch_front_effective_height_trial1_physical_audits_r2','watch_front_effective_height_trial1_numeric_reviews_r2','review_front_effective_height_trial1_v1_stage_episode','review_front_effective_height_trial1_incomplete_episode']:
 src=W/(name+'.py');dest=W/(mapping[name]+'.py');assert not dest.exists();s=rename(src.read_text());compile(s,str(dest),'exec');dest.write_text(s);files.append(dict(parent=str(src),path=str(dest),parent_sha256=sha(src),sha256=sha(dest),binding_names_only=True))
src=W/'run_front_effective_height_trial1_physical_r2.py';s=rename(src.read_text());s=s.replace("S=W/'staged_front_effective_height_v1';PREVIOUS=W/'front_loaded_z_quarter_physical_r2'", "S=W/'staged_front_normal_nondegradation_v3';PREVIOUS=W/'front_effective_height_physical_r1'")
# Parent is current effective-height run, not the older quarter-height run.
s=s.replace("watch_front_loaded_z_quarter_trial2_physical_audits_r2.py", "watch_front_effective_height_trial1_physical_audits_r2.py")
start=s.index('def configuration():');end=s.index('\ndef parent_readiness():',start)
config='''def configuration():
 plan=read(P/'PLAN.json');check=read(P/'PLAN_CHECK.json');assert check['passed'] and plan['status']=='prepared_not_launched' and not plan['simulation_started'] and not plan['training_ready']
 assert plan['collector']==str(S/'collect_paired_sorting.py') and plan['collector_sha256']==sha(plan['collector'])
 assert plan['parent_run']==str(PREVIOUS) and plan['parent_protocol_sha256']==sha(PREVIOUS/'PROTOCOL.json')
 parent=read(PREVIOUS/'PROTOCOL.json');assert plan['groups']==parent['plan']['groups'] and len(plan['commands'])==6
 for item,old in zip(plan['commands'],parent['plan']['commands']):
  expected=list(old['args']);expected[expected.index('--out-dir')+1]=item['args'][item['args'].index('--out-dir')+1];expected.append('--front-normal-nondegradation');assert item==dict(old,args=expected)
 assert sum(len(c['tasks']) for c in plan['commands'])==10
 sources=dict(parent['frozen_files_sha256']);bound(sources);bound(check['source_sha256']);sources.update(check['source_sha256']);used,prep=verify_preparation();assert len(used)==101;sources.update(prep)
 checks=['front_normal_native_stream_r4','front_normal_command_stream_r1','front_normal_command_records_r1','front_normal_observation_binding_checks_r2','front_normal_observation_wrappers_r1','front_normal_native_files_r1','front_normal_parent_coordinate_r1','front_normal_parent_math_files_r1','front_normal_geometry_files_r1','front_normal_geometry_files_r2','front_normal_pressure_files_r1','front_normal_parent_math_preservation_r1','front_normal_audit_dispatch_r1','front_normal_pressure_fork_audit_r1','front_normal_pressure_parent_stream_r1','front_normal_prefix_recovery_r3','front_normal_prefix_recovery_r4']
 for name in checks:
  path=W/name/'RESULT.json';r=read(path);assert r['passed'] is True,name;bound(r['source_sha256']);sources.update(r['source_sha256']);sources[str(path)]=sha(path)
 dispatch=read(W/'front_normal_audit_dispatch_r1/RESULT.json');assert len(dispatch['conditions'])==10 and dispatch['total_checks']==224
 for row in dispatch['created']:
  assert sha(row['original'])==row['original_sha256'] and sha(row['destination'])==row['destination_sha256'];sources[row['original']]=row['original_sha256'];sources[row['destination']]=row['destination_sha256']
 from watch_front_normal_trial1_numeric_reviews_v1 import check as numeric_check
 numeric=numeric_check();assert numeric['passed'];bound(numeric['source_sha256']);sources.update(numeric['source_sha256'])
 derivation=read(P/'RUNNER_PREPARATION.json')
 for row in derivation['files']:
  assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256'];sources[row['parent']]=row['parent_sha256'];sources[row['path']]=row['sha256']
 dest=P/'CONFIGURATION_CHECK.json'
 paths=list(read(dest)['source_sha256']) if dest.exists() else [p for p in W.iterdir() if p.is_file() and p.suffix=='.py' and p.name.startswith(('audit_front_normal','front_normal','watch_front_normal','review_front_normal','run_front_normal'))]
 for p in [*paths,Path(__file__),P/'PLAN.json',P/'PLAN_CHECK.json',P/'RUNNER_PREPARATION.json',PREVIOUS/'PROTOCOL.json',*[S/n for n in used]]:sources[str(p)]=sha(p)
 result=dict(passed=True,conditions=10,expected_audits=224,direct_parent=str(PREVIOUS),source_sha256=sources,simulation_started=False,training_ready=False)
 if dest.exists():assert read(dest)==result
 else:
  with dest.open('x') as f:json.dump(result,f,indent=2)
 return plan,result
'''
s=s[:start]+config+s[end:]
# Legacy declaration is unused by the new explicit proof list; remove ambiguity.
a=s.index('CHECKS=');b=s.index('\ndef bound',a);s=s[:a]+s[b+1:]
dest=W/'run_front_normal_trial1_physical_v1.py';assert not dest.exists();compile(s,str(dest),'exec');dest.write_text(s);files.append(dict(parent=str(src),path=str(dest),parent_sha256=sha(src),sha256=sha(dest),explicit_new_configuration_proofs=True))
# Native collection loop, no-retry failure handling, budgets and markers remain original.
def fn(text,name):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(fn(s,'main'),include_attributes=False)==ast.dump(fn(rename(src.read_text()),'main'),include_attributes=False)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,files=files,native_collection_main_exact_after_binding_rename=True,simulation_started=False,training_ready=False,configuration_pending_full_geometry_result=True,source_sha256={str(Path(__file__)):sha(Path(__file__))})
(P/'RUNNER_PREPARATION.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,prepared_files=len(files),simulation_started=False))
