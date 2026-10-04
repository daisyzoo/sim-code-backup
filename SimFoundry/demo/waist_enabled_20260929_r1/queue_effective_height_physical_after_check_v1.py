"""Continue exact authorized experiment once the live full1200 fixture finishes.
No retries or relaxed checks: any test/configuration/preflight failure stops queue.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_effective_height_physical_preparation_r2';D=W/'front_effective_height_preparation_r1';launcher=W/'run_front_effective_height_trial1_physical_r2.py';test=W/'check_effective_height_native_front_defaultoff_v1.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
def identity(pid):
 try:
  p=Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(pid=pid,start=s[19],state=s[0],cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:return None
pid=int(sys.argv[1]);expected_start=sys.argv[2];initial=identity(pid);assert initial and initial['start']==expected_start and test.name in initial['cmd'] and initial['state']!='Z'
fd=os.open(P/'CONTINUATION_QUEUE_LOCK',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
frozen={str(p):sha(p) for p in [Path(__file__),launcher,test,P/'PLAN.json',P/'LAUNCHER_DERIVATION.json',P/'REVIEW_AND_WATCHER_PREPARATION.json',D/'NATIVE_WAIT_ENABLED_CHECK_V2.json',D/'NATIVE_WAIT_DISABLED_CHECK_V2.json']}
def save(status,**kw):
 dest=P/'CONTINUATION_QUEUE_STATUS.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),expected_test_identity=initial,source_sha256=frozen,training_ready=False,**kw),indent=2));tmp.replace(dest)
def unchanged():
 for p,h in frozen.items():assert sha(p)==h,p
try:
 save('waiting_for_exact_live_full1200_test',simulation_started=False)
 while True:
  unchanged();current=identity(pid)
  if current is None or current['start']!=expected_start or current['state']=='Z':break
  assert current['cmd']==initial['cmd'];time.sleep(10)
 result=read(D/'NATIVE_FRONT_DEFAULTOFF_CHECK.json');assert result['passed'] and result['frames']==1200 and result['raw_and_control_records_unchanged'] and result['temporary_fixture_removed'] and not result['physical_started'] and not result['training_ready']
 for p,h in result['source_sha256'].items():assert sha(p)==h,p
 env=dict(os.environ,OMNI_KIT_ACCEPT_EULA='yes',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps')
 for phase,flag in [('configuration','--configuration-only'),('preflight','--check-only')]:
  save('checking_'+phase,simulation_started=False);unchanged()
  with (P/(phase+'_queue_v1.log')).open('x') as log:
   completed=subprocess.run([sys.executable,str(launcher),flag],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert completed.returncode==0,(phase,completed.returncode)
 unchanged();assert read(P/'LAUNCH_PREFLIGHT.json')['preflight_passed'];assert not (W/'front_effective_height_physical_r1').exists()
 with (P/'physical_producer.log').open('x') as log:child=subprocess.Popen([sys.executable,str(launcher)],cwd=ROOT.parent,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 child_id=identity(child.pid);assert child_id and child_id['state']!='Z' and launcher.name in child_id['cmd']
 with (P/'LAUNCH.json').open('x') as f:json.dump(dict(pid=child.pid,identity=child_id,launcher=str(launcher),launcher_sha256=sha(launcher),preflight_sha256=sha(P/'LAUNCH_PREFLIGHT.json'),training_ready=False),f,indent=2)
 save('producer_started_not_task_success',producer_identity=child_id,simulation_started='producer_will_recheck_preflight_then_start')
except Exception as e:save('stopped_without_retry',error=repr(e),simulation_started=False);raise
