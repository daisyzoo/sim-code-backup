"""Full matched projection diagnostic with unchanged quality gates."""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_projection_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_loaded_physical_r1';S=W/'staged_front_loaded_projection'
sys.path.insert(0,str(ROOT))
from front_projection_stage_source_binding import verify_trial_provenance
from front_projection_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_loaded_projection/CHECK.json','FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json','FRONT_LOADED_PROJECTION_STAGE_CHECK.json','FRONT_LOADED_PROJECTION_AUDIT_CHECK.json','FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json','FRONT_PROJECTION_WAIT_SOURCE_FIXTURE_CHECK.json']
MANIFESTS=['FRONT_PROJECTION_STAGE_AUDITS_PREPARATION.json','FRONT_LOADED_PROJECTION_AUDIT_PREPARATION.json','FRONT_PROJECTION_PHYSICAL_PREPARATION.json','FRONT_PROJECTION_RUNNER_V2_PREPARATION.json','FRONT_LOADED_CLOSED_FAILURE_CLASSIFICATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def configuration():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_plan'])==plan['parent_plan_sha256'];old=json.loads(Path(plan['parent_plan']).read_text())
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for current,original in zip(plan['commands'],old['commands']):
  args=current['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-loaded-material-projection'];assert current==dict(original,args=expected)
  for flag in ['--front-loaded-material-projection','--front-loaded-reference-cap','--front-initial-center-landing','--terminal-release-margin','--edge-clearance-intersection']:assert args.count(flag)==1
  assert not any(x in args for x in ['--terminal-directional-lead','--push-assist'])
  if not current['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==current['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_loaded_material_projection','front_loaded_reference_cap','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'PREPARATION.json').read_text());bound({str(S/k):h for k,h in prep['stage_sha256'].items()})
 for name in CHECKS:
  r=json.loads((W/name).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})
 for row in json.loads((W/MANIFESTS[0]).read_text())['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']
 bound(json.loads((W/MANIFESTS[1]).read_text())['source_sha256'])
 bound(json.loads((W/MANIFESTS[2]).read_text())['files_sha256'])
 bound(json.loads((W/'FRONT_PROJECTION_RUNNER_V2_PREPARATION.json').read_text())['files_sha256'])
 classification=json.loads((W/'FRONT_LOADED_CLOSED_FAILURE_CLASSIFICATION.json').read_text());assert classification['passed'] and classification['retained_failures']==36;bound(classification['source_sha256'])
 dependent=json.loads((W/'FRONT_PROJECTION_AUDIT_DEPENDENCIES_CHECK.json').read_text());assert dependent['missing']==[] and dependent['conditions']==10 and dependent['expected_audit_invocations']==194
 assert json.loads((W/'FRONT_PROJECTION_WAIT_SOURCE_FIXTURE_CHECK.json').read_text())['fixture_only'] is True
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent accepted as new candidate')
 return plan

def preflight():
 plan=configuration();old=json.loads(Path(plan['parent_plan']).read_text())
 state=json.loads((PREVIOUS/'STATUS.json').read_text());assert state['completed_conditions']==10 and state['status']=='collection_complete_audits_visual_pending'
 parent_protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());assert parent_protocol['plan']==old;bound(parent_protocol['frozen_files_sha256'])
 parent_result=PREVIOUS/'RESULT.json';assert parent_result.exists(),'parent complete original closure still pending'
 closed=json.loads(parent_result.read_text());assert closed['conditions']==10 and closed['audit_invocations']==194;bound(closed['source_sha256'])
 assert closed['status']=='diagnostic_complete_failures_retained' and closed['training_ready'] is False
 # Only the two already diagnosed short cap stops are expected. Every full
 # control/wait episode must pass all original audits, not only task scores.
 failures=closed['failed_audit_invocations'];shorts={'layout_840023_nudge_mailer_to_bin':191,'layout_840020_push_box_to_bin':212}
 assert len(failures)==36 and {x['episode'] for x in failures}==set(shorts)
 for row in closed['rows']:
  if row['episode'] in shorts:assert row['incomplete_episode'] and row['frames']==shorts[row['episode']] and not row['original_task_and_pose_passed']
  else:assert row['control_audits_passed'] and not row['failed_audits'] and not row['incomplete_episode']
 for f in failures:
  assert f['incomplete_episode'] and f['returncode']!=0
  ep=next(PREVIOUS.glob('case_*/'+f['episode']));log=ep/(f['script']+'.log');assert sha(log)==f['log_sha256'];text=log.read_text()
  from verify_front_loaded_closed_failures import verify_log
  verify_log(text,ep)
  failure=json.loads((ep/'self_clearance.json').read_text())['failure'];assert failure['reason']=='empty_original_slew_lead_material_intersection' and failure['step']==shorts[ep.name]
 for name in ['FRONT_LOADED_TWO_EARLY_STOP_FINDINGS.json','FRONT_LOADED_STOP_STATE_EVIDENCE_CORRECTION.json']:
  diagnosis=json.loads((W/name).read_text())
  if 'source_sha256' in diagnosis:bound(diagnosis['source_sha256'])
 closure=json.loads((PREVIOUS/'CLOSURE_QUEUE_STATUS.json').read_text());assert closure['status']=='closed_original_failures_retained'
 for pid in [parent_protocol['producer_pid'],json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text())['pid'],closure['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('parent process active',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 # Stop context implementation is a separate diagnostic prerequisite. It must
 # be explicitly checked before this prepared runner may launch.
 stop_check=W/'FRONT_PROJECTION_STOP_CONTEXT_CHECK.json';assert stop_check.exists(),'independent stop context checks still pending'
 stop=json.loads(stop_check.read_text());assert stop['passed'];bound(stop['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),checks={n:sha(W/n) for n in CHECKS},stop_context_check_sha256=sha(stop_check),storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=len(REPORTS),simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*[Path(c['args'][c['args'].index('--diagnostic-layout-json')+1]) for c in plan['commands'] if not c['wait']],P/'PLAN.json',BASE/'RESULT.json',PREVIOUS/'PROTOCOL.json',PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'RESULT.json',W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json',W/'FRONT_PROJECTION_STOP_CONTEXT_CHECK.json',W/'FRONT_LOADED_STOP_STATE_EVIDENCE_CORRECTION.json',W/'FRONT_LOADED_TWO_EARLY_STOP_FINDINGS.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),matched_parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),matched_parent_collection_sha256=sha(PREVIOUS/'COLLECTION_EXECUTION.json'),matched_parent_audits_and_visuals_required_for_comparison=True,remaining_edge_cpu_audits_may_overlap=True,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_front_projection_physical_audits_v2.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_front_projection_physical_audits_v2.py')),indent=2))
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'front_projection_physical_r1'));parser.add_argument('--check-only',action='store_true');args=parser.parse_args();main(args.out,check_only=args.check_only)
