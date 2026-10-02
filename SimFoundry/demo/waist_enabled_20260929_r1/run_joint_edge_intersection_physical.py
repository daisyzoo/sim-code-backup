"""Run prepared complete swap groups after collection and comparison-group closure.
Isolated diagnostic data only; failed conditions remain in the denominator.
No automatic training admission and no simulation launch before prerequisite checks.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,shutil,argparse
W=Path(__file__).resolve().parent;ROOT=W.parents[1];PREP=W/'joint_edge_intersection_physical_preparation_r1';BASE=W/'fresh_closed_peak_trials_r1'
from joint_edge_stage_run_contract import primary,controls,ADDITIONAL,run_audit
from joint_edge_stage_source_binding import verify_trial_provenance
from close_closed_peak_trials import close,live
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def preflight():
 plan=json.loads((PREP/'PLAN.json').read_text());assert plan['status']=='prepared_not_launched' and plan['simulation_started'] is False
 assert sha(plan['collector'])==plan['collector_sha256']
 assert len(plan['commands'])==6 and sum(len(c['tasks']) for c in plan['commands'])==10 and sum(c['wait'] for c in plan['commands'])==2
 for name in ['JOINT_EDGE_STAGE_LOADED_FIXTURE_CHECK.json','JOINT_EDGE_STAGE_AUDIT_INVENTORY_CHECK.json']:
  d=json.loads((W/name).read_text());assert d['passed']
 for item in json.loads((W/'JOINT_EDGE_STAGE_REMAINING_AUDITS_PREPARATION.json').read_text())['files']:
  assert sha(W/item['parent'])==item['parent_sha256'] and sha(W/item['new'])==item['new_sha256']
 for p,h in json.loads((W/'JOINT_EDGE_STAGE_LOADED_FIXTURE_CHECK.json').read_text())['source_sha256'].items():assert sha(p)==h
 # Collection, pressure configuration, all actual visual bindings, and both
 # comparison groups must be complete. Remaining CPU audits for other groups
 # may run concurrently; they read baseline inputs and do not use the GPU.
 status=json.loads((BASE/'STATUS.json').read_text())
 assert status['status']=='collection_complete_audits_visual_pending' and status['completed_conditions']==status['total_conditions']==60
 assert not live(status['pid'],'run_closed_peak_trials.py')
 protocol=json.loads((BASE/'PROTOCOL.json').read_text())
 for name,h in protocol['frozen_files_sha256'].items():assert sha(name)==h
 records=json.loads((BASE/'COLLECTION_EXECUTION.json').read_text());assert len(records)==60
 assert {(x['layout_id'],x['task']) for x in records}=={(c['layout_id'],t) for c in protocol['commands'] for t in c['tasks']}
 pressure=json.loads((BASE/'PRESSURE_SETTING_BINDING.json').read_text());assert pressure['passed'] and len(pressure['rows'])==60 and pressure['protocol_sha256']==sha(BASE/'PROTOCOL.json')
 for row in pressure['rows']:
  assert row['passed'] and row['expected_top_load_n']==row['actual_cli_top_load_n']==5.
  for name,h in row['source_sha256'].items():assert sha(name)==h
 for row in records:
  ep=BASE/f"case_{row['layout_id']}"/f"layout_{row['layout_id']}_{row['task']}";visual=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert visual['raw_sha256']==sha(ep/'raw.npz');assert visual.get('actual_sampled_visual_review')=='completed' or visual.get('actual_visual_review')=='completed_actual_view_8RGB'
 for group in plan['groups']:
  review=json.loads((BASE/'GROUP_REVIEWS'/(group['group']+'.json')).read_text());assert review['status']=='complete_group_audited' and len(review['rows'])==5
  for name,h in review['evidence_sha256'].items():assert sha(name)==h
  if group['group']=='fresh_diagonal_02':assert review['full_group_checks_passed']
  else:assert group['group']=='fresh_reverse_diagonal_07' and not review['full_group_checks_passed']
 for job in json.loads((BASE/'LAUNCH.json').read_text())['jobs']:
  if live(job['pid'],job['script']):assert Path(job['script']).name=='watch_closed_peak_trial_audits.py','Only original CPU auditor may overlap'
 if (BASE/'RESULT.json').exists():assert close(BASE)['status']=='complete_trial_audited'
 assert shutil.disk_usage(ROOT).free>30*1024**3,'Need at least 30GiB before isolated collection'
 gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True)
 assert not gpu.stdout.strip(),('GPU compute process still active',gpu.stdout.strip())
 return plan

def main(out,check_only):
 plan=preflight()
 if check_only:print(json.dumps(dict(preflight_passed=True,simulation_started=False)));return
 out=Path(out).resolve();assert out.parent==W and not out.exists(),'new immediate child run directory required';out.mkdir()
 frozen=dict(json.loads((BASE/'PROTOCOL.json').read_text())['frozen_files_sha256'])
 for p in [*W.glob('*.py'),*Path(plan['collector']).parent.glob('*.py'),*Path(plan['collector']).parent.glob('*.json'),*PREP.glob('layouts/*.json'),PREP/'PLAN.json',BASE/'STATUS.json',BASE/'COLLECTION_EXECUTION.json',BASE/'PRESSURE_SETTING_BINDING.json',BASE/'GROUP_REVIEWS/fresh_reverse_diagonal_07.json',BASE/'GROUP_REVIEWS/fresh_diagonal_02.json',W/'JOINT_EDGE_PHYSICAL_CONCURRENCY_REVISION.json',W/'JOINT_EDGE_STAGE_REMAINING_AUDITS_PREPARATION.json',W/'JOINT_EDGE_STAGE_LOADED_FIXTURE_CHECK.json',W/'JOINT_EDGE_STAGE_AUDIT_INVENTORY_CHECK.json']:frozen[str(p)]=sha(p)
 protocol=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_result_sha256=sha(BASE/'RESULT.json') if (BASE/'RESULT.json').exists() else None,baseline_complete_collection_sha256=sha(BASE/'COLLECTION_EXECUTION.json'),remaining_baseline_cpu_audits_may_overlap=True,all_original_trial_audits_still_required=True,launch_order_revision_sha256=sha(W/'JOINT_EDGE_PHYSICAL_CONCURRENCY_REVISION.json'),plan=plan,frozen_files_sha256=frozen,scope=__doc__,training_ready=False)
 (out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));records=[]
 def unchanged():
  for p,h in frozen.items():assert sha(p)==h,p
 def save(state,**kw):
  tmp=out/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=state,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(out/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('starting')
  for item in plan['commands']:
   unchanged();assert shutil.disk_usage(ROOT).free>30*1024**3
   args=list(item['args']);ix=args.index('--out-dir');case=out/f"case_{item['layout_id']}";assert not case.exists();args[ix+1]=str(case)
   if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
   with (out/f"case_{item['layout_id']}.log").open('x') as log:
    proc=subprocess.Popen([sys.executable,plan['collector'],*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);save('collecting',collector_pid=proc.pid,layout_id=item['layout_id']);code=proc.wait()
   unchanged();state=json.loads((case/'STATUS.json').read_text());assert code in (0,1)
   assert state['status']=='numeric_pass_visual_review_pending' or (state['status']=='blocked_quality_or_runtime' and state['error'] in ['Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.']),(code,state)
   verify_trial_provenance(case)
   for task in item['tasks']:
    ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text());clear=json.loads((ep/'self_clearance.json').read_text());requested=70 if item['wait'] else 1200
    assert clear['requested_frames']==requested and clear['recorded_frames']<=requested
    if clear['recorded_frames']<requested:assert not quality['passed'] and clear['failure'] is not None
    scripts=primary(item['wait'])+['audit_joint_edge_stage_contacts.py','audit_joint_edge_stage_pressure.py']
    if not item['wait']:
     fp=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts+=controls(fp)+ADDITIONAL
    assert len(scripts)==len(set(scripts));rows=[]
    for script in scripts:
     unchanged();save('auditing',episode=ep.name,auditor=script);rows.append(run_audit(ep,script));print(json.dumps(rows[-1]),flush=True)
     (ep/'AUDIT_EXECUTION.json').write_text(json.dumps(dict(completed=False,rows=rows,training_ready=False),indent=2))
    (ep/'AUDIT_EXECUTION.json').write_text(json.dumps(dict(completed=True,rows=rows,training_ready=False),indent=2))
    records.append(dict(group=item['group'],episode=ep.name,task=task,wait=item['wait'],quality_passed=quality['passed'],executed_frames=clear['recorded_frames'],requested_frames=requested,all_audits_passed=all(x['returncode']==0 for x in rows),failed_audits=[x['script'] for x in rows if x['returncode']],raw_sha256=sha(ep/'raw.npz') if (ep/'raw.npz').exists() else None,training_ready=False))
    (out/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
  assert len(records)==10;save('collection_and_numeric_audits_complete_visual_pending',quality_passed=sum(x['quality_passed'] for x in records),all_audits_passed=sum(x['all_audits_passed'] for x in records),total=10)
 except Exception as e:save('runtime_or_audit_failed',error=repr(e));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(W/'joint_edge_intersection_physical_r1'));parser.add_argument('--check-only',action='store_true');a=parser.parse_args();main(a.out,a.check_only)
