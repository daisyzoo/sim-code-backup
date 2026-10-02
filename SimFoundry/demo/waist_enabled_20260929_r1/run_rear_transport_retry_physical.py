"""Complete paired diagnostic of one bounded unloaded feasible-witness retry, no admission.
All original quality and control checks remain, including original h10 model goal.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,shutil,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_transport_retry_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';EDGE=W/'joint_edge_intersection_physical_r1';PREVIOUS=W/'rear_tracking_physical_r1'
from close_closed_peak_trials import live
from rear_transport_retry_source_binding import verify_trial_provenance,verify_preparation
from rear_transport_retry_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['REAR_TRANSPORT_FEASIBLE_RETRY_REGRESSION.json', 'rear_tracking_physical_r1/case_840015/layout_840015_push_box_to_bin/REAR_TRANSPORT_RETRY_LIFECYCLE_FAILURE_V2_CHECK.json', 'REAR_TRANSPORT_RETRY_ORIGINAL_AUDIT_CHECK.json', 'REAR_TRANSPORT_RETRY_SOURCE_PREPARATION_CHECK.json']
MANIFESTS=['REAR_TRANSPORT_RETRY_ORIGINAL_AUDIT_PREPARATION.json', 'REAR_TRANSPORT_RETRY_RUNTIME_PREPARATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def preflight():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and not plan['simulation_started'] and not plan['joint_edge_repair_combined'] and not plan['front_interval_repair_combined']
 assert sha(plan['collector'])==plan['collector_sha256'];assert Path(plan['collector']).parent==W/'staged_rear_transport_retry'
 verify_preparation()
 old_plan_path=W/'rear_tracking_physical_preparation_r1/PLAN.json';assert sha(old_plan_path)==plan['parent_comparison_plan_sha256'];oldplan=json.loads(old_plan_path.read_text());olditems={x['layout_id']:x for x in oldplan['commands']}
 assert len(plan['commands'])==6 and {x['layout_id'] for x in plan['commands']}==set(olditems) and sum(len(x['tasks']) for x in plan['commands'])==10 and sum(x['wait'] for x in plan['commands'])==2
 assert plan['groups']==oldplan['groups'];assert len(REPORTS)==28
 for item in plan['commands']:
  original=olditems[item['layout_id']];projected=dict(item,args=[x for x in item['args'] if x!='--rear-transport-feasible-retry']);assert projected==original
  args=item['args'];assert args.count('--rear-transport-feasible-retry')==args.count('--rear-recovery-tracking')==args.count('--rear-corridor-hysteresis')==args.count('--rear-corridor-recovery')==1
  assert not any(x in args for x in ['--front-corridor-interval','--edge-clearance-intersection','--push-assist']) and args[args.index('--expert-frontal-top-load-n')+1]=='5.'
  if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
  scripts=primary(item['wait'])+['audit_rear_transport_retry_stage_contacts.py','audit_rear_transport_retry_stage_pressure.py']+([] if item['wait'] else controls(dict(initial_top_selected=True,front_route_selected=True))+ADDITIONAL)
  assert all(s in REPORTS and (W/s).exists() for s in scripts)
 checks={}
 for name in CHECKS:
  report=json.loads((W/name).read_text());assert report.get('passed') is True and report.get('status','complete')=='complete',('check not complete',name)
  for field in ['source_sha256','frozen_sha256','auditor_sha256']:
   mapping=report.get(field,{})
   if not isinstance(mapping,dict):continue
   prefix=W/'rear_corridor_physical_r1/case_840015/layout_840015_push_box_to_bin' if name=='REAR_LATCHED_HELD_NATIVE_CHECK.json' and field=='source_sha256' else W
   bound({str(prefix/k) if not Path(k).is_absolute() else k:v for k,v in mapping.items()})
  checks[name]=sha(W/name)
 prepared=json.loads((W/'REAR_TRANSPORT_RETRY_ORIGINAL_AUDIT_PREPARATION.json').read_text())
 for item in prepared['files']:
  a=W/(item['parent']+'.py');b=W/(item['output']+'.py');assert sha(a)==item['parent_sha256'] and sha(b)==item['output_sha256'];s=b.read_text()
  for e in reversed(item['edits']):assert s.count(e['new'])==e['count'];s=s.replace(e['new'],e['old'])
  assert s==a.read_text()
 for item in json.loads((W/'REAR_TRANSPORT_RETRY_RUNTIME_PREPARATION.json').read_text())['files']:
  assert sha(W/item['parent'])==item['parent_sha256'] and sha(W/item['new'])==item['new_sha256']
 old=json.loads((PREVIOUS/'RESULT.json').read_text());assert old['status']=='diagnostic_complete_failures_retained' and old['conditions']==10 and old['push_passed']==5 and old['wait_passed']==2 and not old['training_ready']
 bound(json.loads((PREVIOUS/'PROTOCOL.json').read_text())['frozen_files_sha256']);bound(old['source_sha256'])
 for state_name in ['STATUS.json','AUDIT_STATUS.json']:
  state=json.loads((PREVIOUS/state_name).read_text());proc=Path('/proc')/str(state['pid']);assert not proc.exists() or (proc/'stat').read_text().split()[2]=='Z'
 result=json.loads((BASE/'RESULT.json').read_text());assert result['status']=='complete_trial_audited' and result['conditions']==60 and len(result['groups'])==12
 for group in plan['groups']:
  assert sha(group['source'])==group['sha256'];review=json.loads((BASE/'GROUP_REVIEWS'/(group['group']+'.json')).read_text());assert review['status']=='complete_group_audited' and len(review['rows'])==5;bound(review['evidence_sha256'])
 try:verify_trial_provenance(PREVIOUS/'case_840004')
 except (AssertionError,KeyError):pass
 else:raise AssertionError('Old stage incorrectly admitted as new stage')
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 release=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preflight_passed=True,conditions=10,distinct_audits=28,plan_sha256=sha(P/'PLAN.json'),check_sha256=checks,runner_sha256=sha(__file__),previous_result_sha256=sha(PREVIOUS/'RESULT.json'),storage=storage,simulation_started=False,training_ready=False)
 (P/'LAUNCH_PREFLIGHT.json').write_text(json.dumps(release,indent=2))
 return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=28,simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*[Path(c['args'][c['args'].index('--diagnostic-layout-json')+1]) for c in plan['commands'] if not c['wait']],P/'PLAN.json',BASE/'RESULT.json',PREVIOUS/'RESULT.json',PREVIOUS/'STATUS.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),remaining_edge_cpu_audits_may_overlap=False,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_rear_transport_retry_physical_audits.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_rear_transport_retry_physical_audits.py')),indent=2))
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'rear_transport_retry_physical_r1'));parser.add_argument('--check-only',action='store_true');args=parser.parse_args();main(args.out,check_only=args.check_only)
