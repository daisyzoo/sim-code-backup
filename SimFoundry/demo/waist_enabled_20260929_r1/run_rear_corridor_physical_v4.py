"""Isolated rear-corridor comparison on original complete8push2wait.
No quality retries, no admission; source-frozen full original audits plus new
native recovery are mandatory. Preflight evidence is separate from the proposal.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,shutil,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'rear_corridor_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';EDGE=W/'joint_edge_intersection_physical_r1'
from close_closed_peak_trials import live
from rear_corridor_stage_source_binding import verify_trial_provenance
from rear_corridor_stage_run_contract_v2 import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['REAR_CORRIDOR_STATIONARITY_CHECK.json','REAR_CORRIDOR_STATIONARITY_NEGATIVE_CHECK.json','REAR_CORRIDOR_NATIVE_FIXTURE_CHECK.json','REAR_CORRIDOR_STATE_RECONSTRUCTION_V3_CHECK.json','REAR_TRANSPORT_WITNESS_INDEPENDENT_CHECK.json','REAR_CORRIDOR_TRANSPORT_EVENT_CHECK.json','REAR_CORRIDOR_POSE_BOUNDARY_V2_CHECK.json','REAR_CORRIDOR_PARENT_TASK_CHECK.json','REAR_CORRIDOR_FRONT_POSE_CHECK.json','REAR_CORRIDOR_FRONT_GEOMETRY_CHECK.json','REAR_CORRIDOR_AUDIT_INVENTORY_CHECK.json','REAR_CORRIDOR_PRESSURE_TRANSITION_CHECK.json']
MANIFESTS=['REAR_CORRIDOR_POSE_AUDIT_PREPARATION.json','REAR_CORRIDOR_COMMAND_AUDITS_PREPARATION.json','REAR_CORRIDOR_REMAINING_AUDITS_PREPARATION.json','REAR_CORRIDOR_RUN_CONTRACT_V2_PREPARATION.json','REAR_CORRIDOR_RUNTIME_TOOLS_PREPARATION.json','REAR_CORRIDOR_RUNTIME_V2_PREPARATION.json','REAR_CORRIDOR_RUNTIME_V3_PREPARATION.json','REAR_CORRIDOR_RUNTIME_V4_PREPARATION.json']
def bound(mapping):
 for path,h in mapping.items():assert sha(path)==h,path

def preflight():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and not plan['simulation_started'] and not plan['joint_edge_repair_combined'] and not plan['front_interval_repair_combined']
 assert sha(plan['collector'])==plan['collector_sha256'];assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10 and sum(c['wait'] for c in plan['commands'])==2
 checks={}
 for name in CHECKS:
  report=json.loads((W/name).read_text());assert report.get('passed') is True and report.get('status','complete')=='complete',('check not completed',name,report.get('status'))
  for field in ['source_sha256','frozen_sha256']:
   mapping=report.get(field,{})
   # Inventory paths are relative to W; other check sources are absolute.
   bound({str(W/k) if not Path(k).is_absolute() else k:v for k,v in mapping.items()})
  checks[name]=sha(W/name)
 for name in MANIFESTS:
  report=json.loads((W/name).read_text());entries=report.get('files',[report] if 'parent_sha256' in report else [])
  for row in entries:
   assert sha(W/row['parent'])==row['parent_sha256'] and sha(W/row['new'])==row['new_sha256']
 inventory=json.loads((W/'REAR_CORRIDOR_AUDIT_INVENTORY_CHECK.json').read_text());assert len(REPORTS)==28 and inventory['original_audits']==27 and inventory['current_audits']==28 and sha(W/'rear_corridor_stage_run_contract_v2.py')==inventory['run_contract_sha256']
 for item in plan['commands']:
  args=item['args'];assert args.count('--rear-corridor-recovery')==1 and not any(x in args for x in ['--front-corridor-interval','--edge-clearance-intersection','--push-assist'])
  assert args[args.index('--expert-frontal-top-load-n')+1]=='5.'
  if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
  scripts=primary(item['wait'])+['audit_rear_corridor_stage_contacts.py','audit_rear_corridor_stage_pressure.py']
  if not item['wait']:scripts+=controls(dict(initial_top_selected=True,front_route_selected=True))+ADDITIONAL
  assert all(s in REPORTS and (W/s).exists() for s in scripts)
 result=json.loads((BASE/'RESULT.json').read_text());assert result['status']=='complete_trial_audited' and result['conditions']==60 and len(result['groups'])==12
 bound(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for group in plan['groups']:
  assert sha(group['source'])==group['sha256'];review=json.loads((BASE/'GROUP_REVIEWS'/(group['group']+'.json')).read_text());assert review['status']=='complete_group_audited' and len(review['rows'])==5;bound(review['evidence_sha256']);assert review['full_group_checks_passed'] is (group['group']=='fresh_diagonal_02')
 for directory,name in [(EDGE,'RESULT_WITH_SUPPLEMENT.json'),(W/'front_interval_physical_r2','RESULT.json')]:
  final=json.loads((directory/name).read_text());assert final['conditions']==10 and final['status']==('diagnostic_complete_with_separate_audit_corrections' if directory==EDGE else 'diagnostic_complete_failures_retained')
  bound(json.loads((directory/'PROTOCOL.json').read_text())['frozen_files_sha256'])
  for status_name in ['STATUS.json','AUDIT_STATUS.json']:
   state=json.loads((directory/status_name).read_text());pid=state['pid'];proc=Path('/proc')/str(pid)
   assert not proc.exists() or (proc/'stat').read_text().split()[2]=='Z',('previous diagnostic still live',pid)
 try:verify_trial_provenance(EDGE/'case_840014')
 except KeyError as e:assert e.args==('rear_corridor_recovery',)
 else:raise AssertionError('Wrong stage admitted')
 from rear_corridor_storage_budget import require_storage
 require_storage(ROOT,plan['commands'])
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 release=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),preflight_passed=True,conditions=10,distinct_audits=28,plan_sha256=sha(P/'PLAN.json'),check_sha256=checks,runner_sha256=sha(__file__),simulation_started=False,training_ready=False)
 with (P/'LAUNCH_PREFLIGHT.json').open('w') as f:json.dump(release,f,indent=2)
 return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=28,simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*P.glob('layouts/*.json'),P/'PLAN.json',BASE/'RESULT.json',EDGE/'STATUS.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),remaining_edge_cpu_audits_may_overlap=False,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_rear_corridor_physical_audits_v4.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_rear_corridor_physical_audits_v4.py')),indent=2))
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'rear_corridor_physical_r1'));parser.add_argument('--check-only',action='store_true');args=parser.parse_args();main(args.out,check_only=args.check_only)
