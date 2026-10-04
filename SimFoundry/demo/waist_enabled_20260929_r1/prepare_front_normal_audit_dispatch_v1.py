"""Create versioned dispatch for the complete original ten-condition audit set.
Already implemented new consumers are reused. Remaining independent audits only
change source/import/report bindings; original mathematical bodies are retained.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys,datetime
W=Path(__file__).resolve().parent;D=W/'front_normal_audit_dispatch_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
import front_effective_height_r1_v4_stage_run_contract as old
mapping={
 'front_effective_height_stage_source_binding_v1':'front_normal_stage_source_binding_v3',
 'audit_front_effective_height_r1_v1_stage_contract':'audit_front_normal_stage_contract_v2',
 'audit_front_effective_height_r1_v1_stage_contacts':'audit_front_normal_contacts_v2',
 'audit_front_effective_height_r1_v1_stage_pressure':'audit_front_normal_pressure_files_v1',
 'audit_front_effective_height_stream_v2':'audit_front_normal_native_stream_v1',
 'front_effective_height_command_ledger_v2':'front_normal_command_ledger_v1',
 'front_effective_height_r1_loaded_episode_inputs':'front_normal_loaded_episode_inputs_v1',
 'audit_front_effective_height_front_recovery_stream_v2':'audit_front_normal_recovery_stream_v1',
 'audit_front_effective_height_r1_initial_live':'audit_front_normal_initial_live_v1',
 'audit_front_effective_height_r1_v1_stage_pose_live':'audit_front_normal_pose_live_v1',
 'front_effective_height_r1_v1_stage_audit_context':'front_normal_stage_audit_context_v1',
 'audit_front_effective_height_r1_v3_stage_self_clearance':'audit_front_normal_self_clearance_v1',
 'audit_front_effective_height_r1_v2_z_execution':'audit_front_normal_z_execution_v1',
 'audit_front_effective_height_r1_v2_execution':'audit_front_normal_execution_v1',
 'front_effective_height_r1_v4_stage_run_contract':'front_normal_stage_run_contract_v1',
}
reports={
 'FRONT_EFFECTIVE_HEIGHT_R1_V1_STAGE_CONTACT_AUDIT':'FRONT_NORMAL_V3_CONTACT_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_V1_STAGE_PRESSURE_V2_AUDIT':'FRONT_NORMAL_PRESSURE_FILES_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_STREAM_V2_AUDIT':'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT',
 'JOINT_TRANSPORT_FRONT_RECOVERY_STREAM_V1_AUDIT':'FRONT_NORMAL_FRONT_RECOVERY_STREAM_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_INITIAL_LIVE_AUDIT':'FRONT_NORMAL_INITIAL_LIVE_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_V1_STAGE_POSE_LIVE_V2_AUDIT':'FRONT_NORMAL_POSE_LIVE_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_V3_STAGE_SELF_CLEARANCE_V2_AUDIT':'FRONT_NORMAL_SELF_CLEARANCE_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_V2_Z_EXECUTION_AUDIT':'FRONT_NORMAL_Z_EXECUTION_V1_AUDIT',
 'FRONT_EFFECTIVE_HEIGHT_R1_V2_EXECUTION_AUDIT':'FRONT_NORMAL_EXECUTION_V1_AUDIT',
}
reuse=set(mapping);shared={'audit_front_effective_height_r1_normal_rows'}
queue=[Path(n).stem for n in old.REPORTS if n.startswith('audit_front_effective_height') and Path(n).stem not in reuse]+['front_effective_height_r1_v4_stage_run_contract'];create={}
while queue:
 name=queue.pop(0)
 if name in create or name in shared or (name in reuse and name!='front_effective_height_r1_v4_stage_run_contract'):continue
 p=W/(name+'.py');assert p.is_file(),name;source=p.read_text();create[name]=source
 mapping.setdefault(name,name.replace('front_effective_height','front_normal_stage'))
 for dep in set(re.findall(r'\b(?:audit_)?front_effective_height\w*',source)):
  if dep not in shared and dep not in reuse and dep not in create and (W/(dep+'.py')).exists():queue.append(dep)
# Only module/source/report names and the selected immutable stage may change.
replacements={**mapping,**reports,'staged_front_effective_height_v1':'staged_front_normal_nondegradation_v3'}
created=[]
for oldname,source in create.items():
 new=source
 for a,b in sorted(replacements.items(),key=lambda x:-len(x[0])):new=new.replace(a,b)
 new=new.replace('FRONT_EFFECTIVE_HEIGHT','FRONT_NORMAL_STAGE')
 dest=W/(mapping[oldname]+'.py');assert not dest.exists(),dest;compile(new,str(dest),'exec');dest.write_text(new)
 created.append(dict(original=str(W/(oldname+'.py')),destination=str(dest),original_sha256=sha(W/(oldname+'.py')),destination_sha256=sha(dest),only_explicit_binding_renames=True))
# Import the resulting contract and compare every chosen check, including order.
spec=importlib.util.spec_from_file_location('new_normal_contract',W/'front_normal_stage_run_contract_v1.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
plan=json.loads((W/'front_effective_height_physical_r1/PROTOCOL.json').read_text())['plan'];cases=[];total=0
for item in plan['commands']:
 for task in item['tasks']:
  ep=W/'front_effective_height_physical_r1'/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
  scripts=old.primary(item['wait'])+['audit_front_effective_height_r1_v1_stage_contacts.py','audit_front_effective_height_r1_v1_stage_pressure.py']
  actual=new.primary(item['wait'])+['audit_front_normal_contacts_v2.py','audit_front_normal_pressure_files_v1.py']
  if not item['wait']:
   p=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts+=old.controls(p)+old.ADDITIONAL;actual+=new.controls(p)+new.ADDITIONAL
  scripts+=['audit_front_effective_height_r1_v1_stage_release.py'];actual+=[mapping['audit_front_effective_height_r1_v1_stage_release']+'.py']
  expected=[mapping.get(Path(n).stem,Path(n).stem)+'.py' for n in scripts];assert actual==expected
  unique=list(dict.fromkeys(actual));total+=len(unique)
  for n in unique:
   assert (W/n).is_file() and n in new.REPORTS,n
   report,keys=new.REPORTS[n];assert isinstance(keys,tuple) and keys
   assert report in (W/n).read_text(),(n,report)
  cases.append(dict(episode=ep.name,wait=item['wait'],checks=unique,checks_count=len(unique)))
assert len(cases)==10 and total==224
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,mapping=mapping,report_mapping=reports,shared_independent_math=list(shared),created=created,conditions=cases,total_checks=total,whole_dynamic_dispatch_tested=False,physical_launch_ready=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'front_normal_stage_run_contract_v1.py',W/'front_effective_height_r1_v4_stage_run_contract.py']})
(D/'RESULT.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,new_files=len(created),conditions=len(cases),distinct_applicable_checks=total))
