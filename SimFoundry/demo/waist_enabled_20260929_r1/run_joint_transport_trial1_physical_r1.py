"""Matched diagnostic joint11 collection: original8 pushes +2 waits, no retries.
All original214 audit calls plus10 joint stream calls and actual image review
remain required. This runner does not admit training or claim model success.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'joint_transport_physical_preparation_r1';D=W/'joint_transport_runtime_preparation_r1';S=W/'staged_joint_transport_v1';PREVIOUS=W/'front_box_recenter_physical_r2'
sys.path[:0]=[str(W),str(ROOT)]
from joint_transport_stage_source_binding_v1 import verify_preparation,verify_settings,verify_trial_provenance
from joint_transport_j2_v4_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['PARSER_CHECK.json','RUNTIME_CONTEXT_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json','SOURCE_PREPARATION_CHECK.json','NATIVE_WAIT_STREAM_CHECK.json','AUDIT_FAMILY_IMPORT_CHECK.json','FAMILY_NATIVE_WAIT_CHECK.json','J2_PARENT_CONTEXT_CHECK.json','AUDIT_FAMILY_V2_IMPORT_CHECK.json','FAMILY_NATIVE_WAIT_V2_CHECK.json','NATIVE_REAR_STREAM_CHECK.json','FRONT_PREFIX_CHECK.json']
def bound(mapping):
 for p,h in mapping.items():assert sha(p)==h,p

def configuration():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and not plan['simulation_started'] and not plan['training_ready']
 assert plan['collector']==str(S/'collect_paired_sorting.py') and sha(plan['collector'])==plan['collector_sha256']
 assert plan['parent_run']==str(PREVIOUS) and sha(plan['parent_protocol'])==plan['parent_protocol_sha256'] and sha(PREVIOUS/'RESULT.json')==plan['parent_result_sha256']
 parent=json.loads((PREVIOUS/'PROTOCOL.json').read_text());old=parent['plan'];assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 sources=dict(parent['frozen_files_sha256']);bound(sources);used,prep_sources=verify_preparation();sources.update(prep_sources)
 for item,original in zip(plan['commands'],old['commands']):
  args=item['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--joint-transport-clearance'];assert item==dict(original,args=expected)
  assert args.count('--joint-transport-clearance')==1 and '--inactive-transport-clearance' not in args and '--push-assist' not in args
  parsed,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  from simfoundry.data.waist_pilot_protocol import semantic_settings
  prelaunch=dict(parsed);assert prelaunch.pop('joint_transport_clearance') is True and prelaunch.pop('inactive_transport_clearance') is False and prelaunch.pop('front_box_recenter') is True
  settings=semantic_settings(prelaunch)
  for key in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
  assert parsed['steps']==1200 and parsed['wait_steps']==70 and parsed['role']=='diagnostic' and parsed['motion_protocol']=='waist_yaw_enabled_v1'
  if not item['wait']:
   path=Path(args[args.index('--diagnostic-layout-json')+1]);assert sha(path)==item['layout_sha256'];sources[str(path)]=sha(path)
 for name in CHECKS:
  path=D/name;r=json.loads(path.read_text());assert r['passed'] is True,name;bound(r['source_sha256']);sources.update(r['source_sha256']);sources[str(path)]=sha(path)
 for name in ['AUDIT_FAMILY_PREPARATION.json','AUDIT_FAMILY_V2_PREPARATION.json']:
  path=D/name;r=json.loads(path.read_text());bound(r['source_sha256']);sources.update(r['source_sha256']);sources[str(path)]=sha(path)
  for row in r['adapters']+r.get('shared_unchanged_adapters',[]):
   assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256'];sources[row['parent']]=row['parent_sha256'];sources[row['path']]=row['sha256']
 inventory=json.loads((D/'AUDIT_FAMILY_V2_IMPORT_CHECK.json').read_text())['inventory'];assert len(inventory)==10 and sum(x['count'] for x in inventory)==224
 # Source snapshot includes only runtime dependencies; retained inactive-only helpers are disabled.
 assert len(used)==88
 from watch_joint_transport_trial1_numeric_reviews_r1 import check
 numeric=check();assert numeric['passed'];sources.update(numeric['source_sha256'])
 for path in [*W.glob('*.py'),*S.glob('*.py'),*S.glob('*.json'),P/'PLAN.json',P/'ORCHESTRATION_PREPARATION.json',PREVIOUS/'PROTOCOL.json',PREVIOUS/'RESULT.json',PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json']:
  sources[str(path)]=sha(path)
 result=dict(passed=True,conditions=10,expected_audits=224,direct_parent=str(PREVIOUS),source_sha256=sources,simulation_started=False,training_ready=False)
 dest=P/'CONFIGURATION_CHECK.json'
 if dest.exists():assert json.loads(dest.read_text())==result
 else:
  with dest.open('x') as f:json.dump(result,f,indent=2)
 return plan,result

def preflight():
 plan,config=configuration();parent=json.loads((PREVIOUS/'RESULT.json').read_text());assert parent['conditions']==10 and parent['audit_invocations']==214 and parent['training_ready'] is False
 bound(parent['source_sha256']);audit=json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text());assert audit['status']=='complete' and len(audit['rows'])==214
 visual=json.loads((PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert visual['actual_reviews']==10 and len(visual['rows'])==10;bound(visual['source_sha256'])
 for pid in [audit['pid'],json.loads((PREVIOUS/'PROTOCOL.json').read_text())['producer_pid']]:
  proc=Path('/proc')/str(pid);assert not proc.exists() or (proc/'stat').read_text().split()[2]=='Z'
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands']);gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),configuration_sha256=sha(P/'CONFIGURATION_CHECK.json'),direct_parent_result_sha256=sha(PREVIOUS/'RESULT.json'),storage=storage,simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=len(REPORTS),simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((P/'CONFIGURATION_CHECK.json').read_text())['source_sha256'])
 for path in [P/'CONFIGURATION_CHECK.json',P/'LAUNCH_PREFLIGHT.json']:frozen[str(path)]=sha(path)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,matched_parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),matched_parent_collection_sha256=sha(PREVIOUS/'COLLECTION_EXECUTION.json'),matched_parent_result_sha256=sha(PREVIOUS/'RESULT.json'),matched_parent_audits_and_visuals_required_for_comparison=True,remaining_inactive_only_cpu_audits_may_overlap=True,all_original_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_joint_transport_trial1_physical_audits_r1.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_joint_transport_trial1_physical_audits_r1.py')),indent=2))
  with (out/'numeric_watcher.log').open('x') as log:numeric=subprocess.Popen([sys.executable,str(W/'watch_joint_transport_trial1_numeric_reviews_r1.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'NUMERIC_LAUNCH.json').write_text(json.dumps(dict(pid=numeric.pid,script=str(W/'watch_joint_transport_trial1_numeric_reviews_r1.py')),indent=2))
  from rear_corridor_storage_budget import require_storage
  for case_index,item in enumerate(plan['commands']):
   unchanged();storage=require_storage(ROOT,plan['commands'],case_index)
   with (out/f'storage_before_case_{case_index}.json').open('x') as f:json.dump(storage,f,indent=2)
   case=out/f"case_{item['layout_id']}";assert not case.exists();args=list(item['args']);args[args.index('--out-dir')+1]=str(case)
   with (out/f"case_{item['layout_id']}.log").open('x') as log:child=subprocess.Popen([sys.executable,plan['collector'],*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);save('collecting',collector_pid=child.pid,layout_id=item['layout_id']);code=child.wait()
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'joint_transport_physical_r1'));parser.add_argument('--check-only',action='store_true');parser.add_argument('--configuration-only',action='store_true');args=parser.parse_args()
 if args.configuration_only:configuration();print('CONFIGURATION_CHECKED_NO_PHYSICS')
 else:main(args.out,check_only=args.check_only)
