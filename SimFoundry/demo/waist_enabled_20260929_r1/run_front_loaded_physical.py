"""Complete matched material-cap physics after full parent closure; no admission."""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_loaded_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';PREVIOUS=W/'front_initial_physical_r1';S=W/'staged_front_loaded_reference'
sys.path.insert(0,str(ROOT))
from front_loaded_stage_source_binding import verify_trial_provenance
from front_loaded_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['staged_front_loaded_reference/CHECK.json','FRONT_INITIAL_LOADED_REFERENCE_CAP_CHECK.json','FRONT_LOADED_REFERENCE_HISTORY_V2_CHECK.json','FRONT_LOADED_REFERENCE_STAGE_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json','FRONT_LOADED_AUDIT_DEPENDENCIES_CHECK.json','FRONT_LOADED_WAIT_SOURCE_FIXTURE_CHECK.json']
MANIFESTS=['FRONT_LOADED_STAGE_AUDITS_PREPARATION.json','FRONT_LOADED_STAGE_RUN_CONTRACT_PREPARATION.json','FRONT_LOADED_REFERENCE_COP_AUDIT_PREPARATION.json','FRONT_LOADED_PHYSICAL_PREPARATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def preflight():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert Path(plan['collector'])==S/'collect_paired_sorting.py' and sha(plan['collector'])==plan['collector_sha256']
 assert sha(plan['parent_plan'])==plan['parent_plan_sha256'];old=json.loads(Path(plan['parent_plan']).read_text())
 assert plan['groups']==old['groups'] and len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10
 from prepare_closed_peak_trial import parser_namespace
 from simfoundry.data.waist_pilot_protocol import semantic_settings
 for current,original in zip(plan['commands'],old['commands']):
  args=current['args'];expected=list(original['args']);expected[expected.index('--out-dir')+1]=args[args.index('--out-dir')+1];expected+=['--front-loaded-reference-cap'];assert current==dict(original,args=expected)
  for flag in ['--front-loaded-reference-cap','--front-initial-center-landing','--terminal-release-margin','--edge-clearance-intersection']:assert args.count(flag)==1
  assert not any(x in args for x in ['--terminal-directional-lead','--push-assist'])
  if not current['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==current['layout_sha256']
  resolved,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);settings=semantic_settings(resolved)
  for key in ['front_loaded_reference_cap','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
  assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 prep=json.loads((S/'PREPARATION.json').read_text());bound({str(S/k):h for k,h in prep['stage_sha256'].items()});checks={}
 for name in CHECKS:
  r=json.loads((W/name).read_text());assert r['passed'] is True
  if isinstance(r.get('source_sha256'),dict):bound(r['source_sha256'])
  if 'stage_sha256' in r:bound({str(S/k):h for k,h in r['stage_sha256'].items()})
  checks[name]=sha(W/name)
 for row in json.loads((W/MANIFESTS[0]).read_text())['adapters']:assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256']
 for name in MANIFESTS[1:3]:
  r=json.loads((W/name).read_text());assert sha(r['parent'])==r['parent_sha256'] and sha(r['path'])==r['sha256']
 dependent=json.loads((W/'FRONT_LOADED_AUDIT_DEPENDENCIES_CHECK.json').read_text());assert dependent['missing']==[] and dependent['conditions']==10 and dependent['expected_audit_invocations']==194
 for name in ['FRONT_LOADED_MATERIAL_AUDIT_CHECK.json','FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json']:
  r=json.loads((W/name).read_text());assert len(r['positive'])==1 and len(r['negative'])==9
 assert json.loads((W/'FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json').read_text())['pending']==[]
 assert json.loads((W/'FRONT_LOADED_MATERIAL_AUDIT_V2_CHECK.json').read_text())['earlier_bag_fixture_sha256']==sha(W/'FRONT_LOADED_MATERIAL_AUDIT_CHECK.json')
 assert json.loads((W/'FRONT_LOADED_WAIT_SOURCE_FIXTURE_CHECK.json').read_text())['fixture_only'] is True
 try:verify_trial_provenance(PREVIOUS/'case_840022')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old-source parent accepted as new candidate')
 # Parent numerical failure is expected and retained. Unknown control failures
 # require diagnosis, not an automatic new launch or threshold exception.
 state=json.loads((PREVIOUS/'STATUS.json').read_text());assert state['completed_conditions']==10 and state['status']=='collection_complete_audits_visual_pending'
 parent_protocol=json.loads((PREVIOUS/'PROTOCOL.json').read_text());assert parent_protocol['plan']==old;bound(parent_protocol['frozen_files_sha256'])
 parent_result=PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json';assert parent_result.exists(),'parent full closure still pending'
 closed=json.loads(parent_result.read_text());assert closed['conditions']==10 and not closed['unresolved_audits'];bound(closed['source_sha256'])
 closure=json.loads((PREVIOUS/'CLOSURE_QUEUE_STATUS.json').read_text());assert closure['status']=='closed_original_and_separate_supplement_reports'
 for pid in [parent_protocol['producer_pid'],json.loads((PREVIOUS/'AUDIT_STATUS.json').read_text())['pid'],json.loads((PREVIOUS/'REGION_SUPPLEMENT_STATUS.json').read_text())['pid'],closure['pid']]:
  path=Path('/proc')/str(pid);assert not path.exists() or (path/'stat').read_text().split()[2]=='Z',('parent process active',pid)
 records=json.loads((PREVIOUS/'COLLECTION_EXECUTION.json').read_text());assert len(records)==10
 for row in records:bound(row['source_sha256'])
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 result=dict(preflight_passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(P/'PLAN.json'),checks=checks,storage=storage,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=2));return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=len(REPORTS),simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*[Path(c['args'][c['args'].index('--diagnostic-layout-json')+1]) for c in plan['commands'] if not c['wait']],P/'PLAN.json',BASE/'RESULT.json',PREVIOUS/'PROTOCOL.json',PREVIOUS/'COLLECTION_EXECUTION.json',PREVIOUS/'RESULT_WITH_REGION_SUPPLEMENT.json',W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),matched_parent_protocol_sha256=sha(PREVIOUS/'PROTOCOL.json'),matched_parent_collection_sha256=sha(PREVIOUS/'COLLECTION_EXECUTION.json'),matched_parent_audits_and_visuals_required_for_comparison=True,remaining_edge_cpu_audits_may_overlap=True,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_front_loaded_physical_audits.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_front_loaded_physical_audits.py')),indent=2))
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'front_loaded_physical_r1'));parser.add_argument('--check-only',action='store_true');args=parser.parse_args();main(args.out,check_only=args.check_only)
