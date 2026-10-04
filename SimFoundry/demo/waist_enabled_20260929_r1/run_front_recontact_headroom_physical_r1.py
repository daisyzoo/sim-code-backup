"""Matched front-bag recovery-center physical diagnostic, full8push2wait only.
All204 original audits plus10 complete recovery-stream audits; failures retained. The
source/old-context checks establish readiness to try, never physical success.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_recontact_headroom_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_corridor_midpoint_physical_r1';S=W/'staged_front_recontact_headroom'
sys.path[:0]=[str(W),str(ROOT)]
from front_recontact_headroom_v2_stage_source_binding import verify_trial_provenance
from front_recontact_headroom_v3_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_recontact_center/PARSER_DISPATCH_CHECK.json', 'staged_front_recontact_center/COLLECTOR_HOOK_CHECK.json', 'staged_front_recontact_center/REFERENCE_LEDGER_CHECK.json', 'staged_front_recontact_center/SOURCE_BINDING_CHECK.json', 'staged_front_recontact_center/INDEPENDENT_STREAM_CHECK.json', 'staged_front_recontact_center/CAPTURE_AUDIT_CHECK.json', 'staged_front_recontact_center/INITIAL_REFERENCE_SWITCH_CHECK.json', 'staged_front_recontact_center/AUDIT_FAMILY_IMPORT_CHECK.json', 'staged_front_recontact_center/LOADED_INPUT_CHECK.json', 'staged_front_recontact_center/CONTROL_HISTORY_V2_CHECK.json', 'staged_front_recontact_center/NATIVE_WAIT_CHECK.json', 'staged_front_recontact_center/NATIVE_JOINT_BRANCH_CHECK.json', 'front_recontact_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json', 'staged_front_recontact_headroom/SOURCE_BINDING_CHECK.json', 'staged_front_recontact_headroom/INDEPENDENT_STREAM_CHECK.json', 'staged_front_recontact_headroom/WAIT_STREAM_CHECK.json', 'staged_front_recontact_headroom/AUDIT_FAMILY_IMPORT_CHECK.json', 'staged_front_recontact_headroom/LOADED_INPUT_CHECK.json', 'staged_front_recontact_headroom/NATIVE_WAIT_CHECK.json', 'staged_front_recontact_headroom/NATIVE_JOINT_BRANCH_CHECK.json', 'front_bag_recontact_headroom_draft_r1/GUARD_CHECK.json', 'front_bag_recontact_headroom_draft_r1/PROBE_RESULT.json', 'front_recontact_headroom_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json']
MANIFESTS=['staged_front_recontact_center/AUDIT_FAMILY_PREPARATION.json', 'staged_front_recontact_center/LOADED_INPUT_PREPARATION.json', 'staged_front_recontact_center/CAPTURE_AUDIT_PREPARATION.json', 'staged_front_recontact_center/AUDIT_V3_PREPARATION.json', 'front_recontact_preparation_r1/PHYSICAL_PREPARATION.json', 'staged_front_recontact_headroom/AUDIT_FAMILY_PREPARATION.json', 'front_recontact_headroom_preparation_r1/PHYSICAL_PREPARATION.json']
_cache={}
def bound(mapping):
 for p,h in mapping.items():
  if p not in _cache:_cache[p]=sha(p)
  assert _cache[p]==h,p

def configuration():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_protocol'])==plan['parent_protocol_sha256'];old=json.loads(Path(plan['parent_protocol']).read_text())['plan']
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for item,original in zip(plan['commands'],old['commands']):
  args=item['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-recontact-center-landing'];assert item==dict(original,args=expected)
  for flag in ['--front-recontact-center-landing','--front-corridor-midpoint-replan','--front-loaded-z-priority','--front-initial-center-landing','--terminal-release-margin','--edge-clearance-intersection']:assert args.count(flag)==1
  assert not any(x in args for x in ['--front-loaded-reference-cap','--front-loaded-material-projection','--terminal-directional-lead','--push-assist'])
  if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());bound(prep['source_sha256']);bound({str(S/n):h for n,h in prep['stage_sha256'].items()})
 for n in CHECKS:
  r=json.loads((W/n).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str((W/n).parent/k):h for k,h in r['stage_sha256'].items()})
 bound(json.loads((P/'AUDIT_DEPENDENCIES.json').read_text())['source_sha256'])
 for name in MANIFESTS:
  manifest=json.loads((W/name).read_text());bound(manifest.get('source_sha256',{}))
  for row in manifest.get('adapters',[])+manifest.get('records',[])+manifest.get('files',[]):
   assert sha(row['parent'])==row['parent_sha256']
   target=row.get('path',row.get('target'));digest=row.get('sha256',row.get('target_sha256'));assert sha(target)==digest,target
 deps=json.loads((P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json').read_text());assert deps['passed'] and deps['condition_count']==10 and deps['expected_audits']==214
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent admitted as new stage')
 from watch_front_recontact_headroom_numeric_reviews_r1 import check
 numeric=check();assert numeric['passed'];bound(numeric['source_sha256'])
 result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),conditions=10,original_audits=204,new_recontact_stream_audits=10,total_audits=214,plan_sha256=sha(P/'PLAN.json'),checks={n:sha(W/n) for n in CHECKS},numeric_routing=numeric,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'CONFIGURATION_CHECK.json').write_text(json.dumps(result,indent=2));return plan

def preflight():
 plan=configuration();closed_path=PREVIOUS/'RESULT.json';parent=json.loads(closed_path.read_text())
 assert parent['status']=='diagnostic_complete_failures_retained' and parent['conditions']==10 and parent['audit_invocations']==204
 from close_midpoint_rigid_axis_supplement import verify_saved_closed
 resolved=verify_saved_closed();assert resolved['unresolved_audits']==[] and resolved['original_audit_invocations']==204
 assert parent['training_ready'] is False and parent['model_goal_achieved'] is False
 bound(parent['source_sha256']);assert parent['closer_sha256']==sha(W/'close_front_corridor_midpoint_physical.py')
 protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());audit=json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text());bound(protocol['frozen_files_sha256'])
 assert audit['status']=='complete' and len(audit['rows'])==204
 for pid in [protocol['producer_pid'],audit['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('previous process live',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 visual=json.loads((PREVIOUS/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert visual['actual_reviews']==10 and len(visual['rows'])==10;bound(visual['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),configuration_check_sha256=sha(P/'CONFIGURATION_CHECK.json'),matched_parent_closure_sha256=sha(closed_path),matched_parent_supplement_closure_sha256=sha(PREVIOUS/'RESULT_WITH_RIGID_AXIS_SUPPLEMENT.json'),storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=len(REPORTS),simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*[Path(c['args'][c['args'].index('--diagnostic-layout-json')+1]) for c in plan['commands'] if not c['wait']],P/'PLAN.json',BASE/'RESULT.json',PREVIOUS/'PROTOCOL.json',PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'RESULT.json',PREVIOUS/'RESULT_WITH_RIGID_AXIS_SUPPLEMENT.json',PREVIOUS/'RIGID_AXIS_CERTIFICATE_CHECK.json',PREVIOUS/'case_840023/layout_840023_nudge_mailer_to_bin/MIDPOINT_RIGID_AXIS_TASK_OPTIMALITY_SUPPLEMENT.json',W/'front_projection_physical_r1/RESULT.json',W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),matched_parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),matched_parent_collection_sha256=sha(PREVIOUS/'COLLECTION_EXECUTION.json'),matched_parent_audits_and_visuals_required_for_comparison=True,remaining_edge_cpu_audits_may_overlap=True,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_front_recontact_headroom_physical_audits_r1.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_front_recontact_headroom_physical_audits_r1.py')),indent=2))
  with (out/'numeric_watcher.log').open('x') as log:numeric=subprocess.Popen([sys.executable,str(W/'watch_front_recontact_headroom_numeric_reviews_r1.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'NUMERIC_LAUNCH.json').write_text(json.dumps(dict(pid=numeric.pid,script=str(W/'watch_front_recontact_headroom_numeric_reviews_r1.py')),indent=2))
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'front_recontact_headroom_physical_r1'));parser.add_argument('--check-only',action='store_true');parser.add_argument('--configuration-only',action='store_true');args=parser.parse_args()
 if args.configuration_only:configuration();print('CONFIGURATION_CHECKED_NO_PHYSICS')
 else:main(args.out,check_only=args.check_only)
