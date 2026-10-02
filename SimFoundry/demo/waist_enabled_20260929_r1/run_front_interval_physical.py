"""Isolated front-interval physical comparison: complete original8push2wait.
Source-frozen collection and independent CPU audits may overlap. No retry,
trajectory overwriting, data admission or altered task/quality thresholds.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,shutil,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_interval_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1';EDGE=W/'joint_edge_intersection_physical_r1'
from close_closed_peak_trials import live
from front_interval_stage_source_binding import verify_trial_provenance
from front_interval_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHECKS=['FRONT_INTERVAL_INDEPENDENT_ENABLED_CHECK.json','FRONT_INTERVAL_COP_REGRESSION_CHECK.json','FRONT_INTERVAL_AUDIT_INVENTORY_CHECK.json','COMPACT_SCENE_REJECTION_CHECK.json']
MANIFESTS=['FRONT_INTERVAL_CORE_AUDIT_PREPARATION.json','FRONT_INTERVAL_REMAINING_AUDITS_PREPARATION.json','FRONT_INTERVAL_REVIEW_PREPARATION.json','FRONT_CORRIDOR_INTERVAL_CANDIDATE_PREPARATION.json','FRONT_CORRIDOR_INTERVAL_CANDIDATE_CHECK.json','COMPACT_SCENE_POSE_AUDIT_PREPARATION.json']
def preflight():
 plan=json.loads((P/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and not plan['simulation_started'] and plan['joint_edge_repair_combined'] is False
 assert sha(plan['collector'])==plan['collector_sha256'];assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10 and sum(c['wait'] for c in plan['commands'])==2
 for name in CHECKS:
  report=json.loads((W/name).read_text());assert report['passed']
  for path,h in report.get('source_sha256',{}).items():assert sha(path)==h,path
 for row in json.loads((W/'FRONT_INTERVAL_AUDIT_INVENTORY_CHECK.json').read_text())['files']:assert sha(W/row['auditor'])==row['sha256']
 for row in json.loads((W/'FRONT_INTERVAL_REMAINING_AUDITS_PREPARATION.json').read_text())['files']:assert sha(W/row['parent'])==row['parent_sha256'] and sha(W/row['new'])==row['new_sha256']
 for item in plan['commands']:
  args=item['args'];assert args.count('--front-corridor-interval')==1 and '--edge-clearance-intersection' not in args and '--push-assist' not in args
  assert args[args.index('--expert-frontal-top-load-n')+1]=='5.'
  if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
  scripts=primary(item['wait'])+['audit_front_interval_stage_contacts.py','audit_front_interval_stage_pressure.py']
  if not item['wait']:scripts+=controls(dict(initial_top_selected=True,front_route_selected=True))+ADDITIONAL
  assert all(s in REPORTS and (W/s).exists() for s in scripts)
 # Fully closed original baseline and fully bound exact comparison groups.
 result=json.loads((BASE/'RESULT.json').read_text());assert result['status']=='complete_trial_audited' and result['conditions']==60 and len(result['groups'])==12
 for path,h in json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'].items():assert sha(path)==h,path
 for group in plan['groups']:
  assert sha(group['source'])==group['sha256'];review=json.loads((BASE/'GROUP_REVIEWS'/(group['group']+'.json')).read_text());assert review['status']=='complete_group_audited' and len(review['rows'])==5
  for path,h in review['evidence_sha256'].items():assert sha(path)==h,path
  assert review['full_group_checks_passed'] is (group['group']=='fresh_diagonal_02')
 edge=json.loads((EDGE/'STATUS.json').read_text());assert edge['status']=='collection_complete_audits_visual_pending' and edge['completed_conditions']==edge['total_conditions']==10;assert not live(edge['pid'],'resume_joint_edge_physical_collection.py')
 # Old edge evidence must be rejected only after all new stage source checks.
 try:verify_trial_provenance(EDGE/'case_840014')
 except KeyError as e:assert e.args==('front_corridor_interval',)
 else:raise AssertionError('Wrong stage admitted')
 assert shutil.disk_usage(ROOT).free>30*1024**3
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True);assert not gpu.stdout.strip(),gpu.stdout.strip()
 return plan

def main(out,check_only=False):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,conditions=10,distinct_audits=27,simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists();out.mkdir();frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*P.glob('layouts/*.json'),P/'PLAN.json',BASE/'RESULT.json',EDGE/'STATUS.json',*[W/n for n in CHECKS+MANIFESTS]]:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),producer_pid=os.getpid(),plan=plan,frozen_files_sha256=frozen,scope=__doc__,baseline_result_sha256=sha(BASE/'RESULT.json'),remaining_edge_cpu_audits_may_overlap=True,all_edge_audits_still_required=True,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for path,h in frozen.items():assert sha(path)==h,path
 def save(status,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  with (out/'audit_watcher.log').open('x') as log:watcher=subprocess.Popen([sys.executable,str(W/'watch_front_interval_physical_audits.py'),str(out)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (out/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_front_interval_physical_audits.py')),indent=2))
  for item in plan['commands']:
   unchanged();assert shutil.disk_usage(ROOT).free>30*1024**3;case=out/f"case_{item['layout_id']}";assert not case.exists();args=list(item['args']);args[args.index('--out-dir')+1]=str(case)
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
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'front_interval_physical_r1'));parser.add_argument('--check-only',action='store_true');args=parser.parse_args();main(args.out,check_only=args.check_only)
