"""Resume terminal scheduler failure without recollecting saved conditions.
Preserves original protocol and source hashes. Collection and independent audits
run concurrently; neither role changes or approves original diagnostic samples.
"""
from pathlib import Path
import sys,json,os,datetime,hashlib,subprocess,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'joint_edge_intersection_physical_r1'
from run_joint_edge_intersection_physical import preflight
from joint_edge_stage_source_binding import verify_trial_provenance
from close_closed_peak_trials import live
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=json.loads((R/'STATUS.json').read_text());assert old['status']=='runtime_or_audit_failed' and old['error']=='AssertionError()'
 assert not live(old['pid'],'run_joint_edge_intersection_physical.py')
 plan=preflight();original=json.loads((R/'PROTOCOL.json').read_text());assert original['plan']==plan
 for name,h in original['frozen_files_sha256'].items():assert sha(name)==h,name
 assert not (R/'RESUME_PROTOCOL.json').exists();frozen=dict(original['frozen_files_sha256'])
 for p in [Path(__file__),W/'watch_joint_edge_physical_audits.py',W/'review_joint_edge_stage_episode.py']:frozen[str(p)]=sha(p)
 resume=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_protocol_sha256=sha(R/'PROTOCOL.json'),original_scheduler_failure=old,reason='Original scheduler incorrectly rejected duplicate front-diagonal audit shared by primary and additional lists. Unique applicable audits retained; saved complete case reused after revalidation, never overwritten.',frozen_files_sha256=frozen,producer_pid=os.getpid(),scope=__doc__,training_ready=False)
 (R/'RESUME_PROTOCOL.json').write_text(json.dumps(resume,indent=2));records=[]
 def unchanged():
  for name,h in frozen.items():assert sha(name)==h,name
 def save(status,**kw):
  tmp=R/'STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_conditions=len(records),training_ready=False,**kw),indent=2));tmp.replace(R/'STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',DISPLAY=':1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
 try:
  save('resuming_saved_case')
  with (R/'audit_watcher.log').open('x') as log:
   watcher=subprocess.Popen([sys.executable,str(W/'watch_joint_edge_physical_audits.py'),str(R)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  (R/'AUDIT_LAUNCH.json').write_text(json.dumps(dict(pid=watcher.pid,script=str(W/'watch_joint_edge_physical_audits.py')),indent=2))
  for item in plan['commands']:
   unchanged();case=R/f"case_{item['layout_id']}";reused=case.exists()
   if reused:
    assert item['layout_id']==840014 and not records,'Only original fully saved first case can be reused'
    state=json.loads((case/'STATUS.json').read_text());assert state['status']=='numeric_pass_visual_review_pending'
   else:
    assert shutil.disk_usage(ROOT).free>30*1024**3
    args=list(item['args']);args[args.index('--out-dir')+1]=str(case)
    if not item['wait']:assert sha(args[args.index('--diagnostic-layout-json')+1])==item['layout_sha256']
    with (R/f"case_{item['layout_id']}.log").open('x') as log:
     child=subprocess.Popen([sys.executable,plan['collector'],*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);save('collecting',collector_pid=child.pid,layout_id=item['layout_id']);code=child.wait()
    assert code in (0,1);state=json.loads((case/'STATUS.json').read_text());assert state['status']=='numeric_pass_visual_review_pending' or (state['status']=='blocked_quality_or_runtime' and state['error'] in ['Quality gate failed. Stop; no retries or training export. See manifest.json.','Wait quality gate failed.']),(code,state)
   unchanged();verify_trial_provenance(case)
   for task in item['tasks']:
    ep=case/f"layout_{item['layout_id']}_{task}";quality=json.loads((ep/'quality.json').read_text());clear=json.loads((ep/'self_clearance.json').read_text());requested=70 if item['wait'] else 1200
    assert clear['requested_frames']==requested and clear['recorded_frames']<=requested
    if clear['recorded_frames']<requested:assert not quality['passed'] and clear['failure'] is not None
    marker=dict(episode=ep.name,group=item['group'],task=task,wait=item['wait'],quality_passed=quality['passed'],executed_frames=clear['recorded_frames'],requested_frames=requested,reused_original_saved_case=reused,source_sha256={str(p):sha(p) for p in [case/'provenance.json',ep/'quality.json',ep/'self_clearance.json']+([ep/'raw.npz'] if (ep/'raw.npz').exists() else [])},training_ready=False)
    with (ep/'READY_FOR_AUDIT.json').open('x') as f:json.dump(marker,f,indent=2)
    records.append(marker);tmp=R/'COLLECTION_EXECUTION.tmp';tmp.write_text(json.dumps(records,indent=2));tmp.replace(R/'COLLECTION_EXECUTION.json')
  assert len(records)==10;save('collection_complete_audits_visual_pending',total_conditions=10,original_task_gates_passed=sum(x['quality_passed'] for x in records))
 except Exception as e:save('runtime_or_audit_failed',error=repr(e));raise
if __name__=='__main__':main()
