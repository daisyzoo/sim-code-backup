"""Fixed matched reserve trial:8push2wait with all original224audits and image review.
Parent collection+actual views must finish and GPU must be free. Pending parent
CPU audits may overlap; final comparison requires complete parent audit closure.
Never admits diagnostic data or retries failed conditions.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_normal_physical_preparation_r3';D=W/'front_effective_height_preparation_r1';S=W/'staged_front_normal_nondegradation_v3';PREVIOUS=W/'front_effective_height_physical_r1'
sys.path[:0]=[str(W),str(ROOT)]
from front_normal_stage_source_binding_v3 import verify_preparation,verify_settings,verify_trial_provenance
from front_normal_stage_run_contract_v1 import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def bound(mapping):
 for p,h in mapping.items():assert sha(p)==h,p

def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(start=st[19],state=st[0],cmd=(p/'cmdline').read_bytes().split(b'\0')[:-1])
 except FileNotFoundError:return None

def configuration():
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

def parent_readiness():
 protocol=read(PREVIOUS/'PROTOCOL.json');state=read(PREVIOUS/'STATUS.json');audit=read(PREVIOUS/'AUDIT_STATUS.json');pending=[]
 if state['status']!='collection_complete_audits_visual_pending' or state['completed_conditions']!=10:pending.append('parent_collection_incomplete')
 if identity(protocol['producer_pid']) is not None and identity(protocol['producer_pid'])['state']!='Z':pending.append('parent_producer_still_active')
 if not (PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json').exists():pending.append('parent_ten_actual_reviews_not_summarized')
 if audit['status'] not in ['running','complete']:pending.append('parent_audit_not_running_or_complete')
 if audit['status']=='running':
  proc=identity(audit['pid'])
  if proc is None or proc['state']=='Z' or str(W/'watch_front_effective_height_trial1_physical_audits_r2.py').encode() not in proc['cmd']:pending.append('parent_original_auditor_not_live')
 return dict(ready=not pending,pending=pending,parent_completed=state['completed_conditions'],parent_audit_status=audit['status'],parent_audit_rows=len(audit['rows']),training_ready=False)

def preflight():
 plan,config=configuration();ready=parent_readiness();assert ready['ready'],ready
 rear=W/'front_box_trailing_physical_r2';rear_state=read(rear/'STATUS.json');assert rear_state['status']=='collection_complete_audits_visual_pending' and rear_state['completed_conditions']==10
 rear_summary=read(rear/'NUMERIC_VISUAL_SUMMARY.json');assert rear_summary['actual_reviews']==10;bound(rear_summary['source_sha256']);proc=identity(read(rear/'PROTOCOL.json')['producer_pid']);assert proc is None or proc['state']=='Z'
 summary=read(PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json');assert summary['actual_reviews']==10 and len(summary['rows'])==10 and summary['training_ready'] is False;bound(summary['source_sha256'])
 records=read(PREVIOUS/'COLLECTION_EXECUTION.json');assert len(records)==10
 expected={f"layout_{c['layout_id']}_{task}" for c in plan['commands'] for task in c['tasks']};assert {x['episode'] for x in records}=={x['episode'] for x in summary['rows']}==expected
 parent_sources=dict(summary['source_sha256'])
 for row in records:bound(row['source_sha256']);parent_sources.update(row['source_sha256'])
 for p in [PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json']:parent_sources[str(p)]=sha(p)
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands']);gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),configuration_sha256=sha(P/'CONFIGURATION_CHECK.json'),parent_readiness=ready,parent_source_sha256=parent_sources,parent_audit_closure_required_for_final_comparison=True,storage=storage,simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan,result

def main(out,check_only=False):
 plan,launch=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=len(REPORTS),simulation_started=False)));return
 out=Path(out).resolve();assert out==W/'front_normal_physical_r1' and not out.exists();out.mkdir();frozen=dict(json.loads((P/'CONFIGURATION_CHECK.json').read_text())['source_sha256'])
 frozen.update(launch['parent_source_sha256'])
 for path in [P/'CONFIGURATION_CHECK.json',P/'LAUNCH_PREFLIGHT.json']:frozen[str(path)]=sha(path)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,matched_parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),matched_parent_collection_sha256=sha(PREVIOUS/'COLLECTION_EXECUTION.json'),matched_parent_result_pending=not (PREVIOUS/'RESULT.json').exists(),matched_parent_numeric_visual_sha256=sha(PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json'),matched_parent_audits_and_visuals_required_for_comparison=True,parent_cpu_audits_may_overlap=True,all_original_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_front_normal_trial1_physical_audits_v1.py'),str(out)],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_front_normal_trial1_physical_audits_v1.py')),indent=2))
  with (out/'numeric_watcher.log').open('x') as log:numeric=subprocess.Popen([sys.executable,str(W/'watch_front_normal_trial1_numeric_reviews_v1.py')],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'NUMERIC_LAUNCH.json').write_text(json.dumps(dict(pid=numeric.pid,script=str(W/'watch_front_normal_trial1_numeric_reviews_v1.py')),indent=2))
  from rear_corridor_storage_budget import require_storage
  for case_index,item in enumerate(plan['commands']):
   unchanged();storage=require_storage(ROOT,plan['commands'],case_index)
   with (out/f'storage_before_case_{case_index}.json').open('x') as f:json.dump(storage,f,indent=2)
   case=out/f"case_{item['layout_id']}";assert not case.exists();args=list(item['args']);args[args.index('--out-dir')+1]=str(case)
   with (out/f"case_{item['layout_id']}.log").open('x') as log:child=subprocess.Popen([sys.executable,plan['collector'],*args],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT);save('collecting',collector_pid=child.pid,layout_id=item['layout_id']);code=child.wait()
   assert code in (0,1);state=json.loads((case/'STATUS.json').read_text());assert state['status']=='numeric_pass_visual_review_pending' or (state['status']=='blocked_quality_or_runtime' and state['error'] in ['Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.']),(code,state)
   unchanged();verify_trial_provenance(case)
   for task in item['tasks']:
    ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text());clear=json.loads((ep/'self_clearance.json').read_text());requested=70 if item['wait'] else 1200;assert clear['requested_frames']==requested and clear['recorded_frames']<=requested
    if clear['recorded_frames']<requested:assert not quality['passed'] and clear['failure'] is not None
    marker=dict(episode=ep.name,group=item['group'],task=task,wait=item['wait'],quality_passed=quality['passed'],executed_frames=clear['recorded_frames'],requested_frames=requested,source_sha256={str(p):sha(p) for p in [case/'provenance.json',ep/'quality.json',ep/'self_clearance.json']+([ep/'raw.npz'] if (ep/'raw.npz').exists() else [])},training_ready=False)
    with (ep/'READY_FOR_AUDIT.json').open('x') as f:json.dump(marker,f,indent=2)
    records.append(marker);tmp=out/'COLLECTION_EXECUTION.tmp';tmp.write_text(json.dumps(records,indent=2));tmp.replace(out/'COLLECTION_EXECUTION.json')
  assert len(records)==10;save('collection_complete_audits_visual_pending',total_conditions=10,original_task_gates_passed=sum(x['quality_passed'] for x in records))
 except Exception as e:save('runtime_or_audit_failed',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'front_normal_physical_r1'));parser.add_argument('--check-only',action='store_true');parser.add_argument('--configuration-only',action='store_true');args=parser.parse_args()
 if args.configuration_only:configuration();print('CONFIGURATION_CHECKED_NO_PHYSICS')
 else:os.chdir(ROOT.parent);main(args.out,check_only=args.check_only)
