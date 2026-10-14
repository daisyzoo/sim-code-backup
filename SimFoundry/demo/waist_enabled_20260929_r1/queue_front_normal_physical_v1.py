"""Wait for the exact live geometry check, then run unchanged full physical preflight.
One launch only; no retries, relaxed gates, admissions or synthetic visual claims.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;P=W/'front_normal_physical_preparation_r3';G=W/'front_normal_geometry_files_r2/RESULT.json';R=W/'front_normal_physical_r1';PID=852086
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(start=st[19],state=st[0],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:return None

def main():
 lock=P/'PHYSICAL_QUEUE_LOCK';fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 def save(status,**kw):
  p=P/'PHYSICAL_QUEUE_STATUS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),dependency_pid=PID,dependency_report=str(G),training_ready=False,**kw),indent=2));tmp.replace(p)
 try:
  assert not R.exists(),'Do not adopt or restart an existing physical run'
  imports=json.loads((W/'front_normal_dispatch_imports_r1/RESULT.json').read_text());assert imports['passed']
  frozen={str(p):sha(p) for p in [Path(__file__),P/'PLAN.json',P/'PLAN_CHECK.json',P/'RUNNER_PREPARATION.json',W/'run_front_normal_trial1_physical_v1.py',W/'check_front_normal_push_geometry_files_v1.py',W/'front_normal_dispatch_imports_r1/RESULT.json']};frozen.update(imports['source_sha256'])
  original=identity(PID)
  if not G.exists():assert original and original['state']!='Z' and 'check_front_normal_push_geometry_files_v1.py' in original['command']
  with (P/'PHYSICAL_QUEUE_PROVENANCE.json').open('x') as f:json.dump(dict(queue_pid=os.getpid(),dependency_identity=original,source_sha256=frozen,scope=__doc__),f,indent=2)
  while True:
   for name,h in frozen.items():assert sha(name)==h,name
   live=identity(PID)
   if live and live['state']!='Z':
    assert original and live['start']==original['start'] and live['command']==original['command'];save('waiting_for_exact_geometry_process',dependency_live=live,result_exists=G.exists());time.sleep(15);continue
   assert G.exists(),'Geometry process ended without success report; no launch'
   result=json.loads(G.read_text());assert result['passed'] is True and result['frames']==1200 and result['pose_passed'] and result['body_passed'] and not result['training_ready']
   for name,h in result['source_sha256'].items():assert sha(name)==h,name
   break
  assert not R.exists();save('running_original_preflight',geometry_report_sha256=sha(G))
  env=dict(os.environ,OMNI_KIT_ACCEPT_EULA='yes',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1')
  with (P/'PHYSICAL_PRODUCER.log').open('x') as log:
   child=subprocess.Popen([sys.executable,str(W/'run_front_normal_trial1_physical_v1.py')],cwd=W.parents[2],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   save('producer_started_preflight_must_pass',producer_pid=child.pid,geometry_report_sha256=sha(G));code=child.wait()
  assert code==0,('Original runner failed; preserved without retry',code)
  status=json.loads((R/'STATUS.json').read_text());assert status['status']=='collection_complete_audits_visual_pending' and status['completed_conditions']==10
  save('collection_complete_audits_actual_visual_pending',producer_pid=child.pid,producer_returncode=code,completed_conditions=10)
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':main()
