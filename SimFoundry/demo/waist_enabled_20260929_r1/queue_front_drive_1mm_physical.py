"""Wait for exact original midpoint audit+closure, then launch one full1mm trial.
No retry, no overlap with parent physics, no quality change or data admission.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;P=W/'front_drive_1mm_preparation_r2';C=W/'front_corridor_midpoint_physical_r1';R=W/'front_drive_1mm_physical_r1';S=W/'staged_front_drive_1mm';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=(p/'cmdline').read_bytes().split(b'\0')[:-1]
 except FileNotFoundError:return None
 return dict(start_ticks=st[19],state=st[0],cmd=[c.decode() for c in cmd])
def save(status,**kw):
 p=P/'LAUNCH_QUEUE_STATUS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));tmp.replace(p)
def main():
 fd=os.open(P/'LAUNCH_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd);assert not R.exists()
 checks=read(P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json');assert checks['passed'] and checks['condition_count']==10 and checks['expected_audits']==204
 assert read(P/'CONFIGURATION_CHECK.json')['passed']
 family=read(W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json');generated=read(W/'FRONT_DRIVE_1MM_PHYSICAL_PREPARATION.json');frozen=dict(family['dependency_sha256'])
 for row in family['adapters']+generated['files']:frozen[row['path']]=row['sha256'];frozen[row['parent']]=row['parent_sha256']
 for name,h in read(S/'COLLECTOR_PREPARATION.json')['stage_sha256'].items():frozen[str(S/name)]=h
 frozen.update(checks['source_sha256'])
 for p in [Path(__file__),P/'PLAN.json',P/'TRIAL_PROFILE.json',P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json',S/'COLLECTOR_PREPARATION.json',S/'CLI_PARAMETER_CHECK.json',C/'PROTOCOL.json',C/'NUMERIC_VISUAL_SUMMARY.json',C/'CLOSURE_LAUNCH.json',W/'FRONT_DRIVE_1MM_V2_AUDIT_FAMILY_PREPARATION.json',W/'FRONT_DRIVE_1MM_PHYSICAL_PREPARATION.json']:frozen[str(p)]=sha(p)
 ids={}
 for pid,script in [(read(C/'AUDIT_STATUS.json')['pid'],'watch_front_corridor_midpoint_physical_audits.py'),(read(C/'CLOSURE_LAUNCH.json')['pid'],'queue_front_corridor_midpoint_physical_closure.py')]:
  state=identity(pid);assert state and state['state']!='Z' and str(W/script) in state['cmd'];ids[pid]=state
 with (P/'LAUNCH_QUEUE_BINDING.json').open('x') as f:json.dump(dict(identities=ids,frozen_sha256=frozen,training_ready=False),f,indent=2)
 started=time.monotonic()
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  audit=read(C/'AUDIT_STATUS.json');closure=read(C/'CLOSURE_QUEUE_STATUS.json');assert audit['status'] in ['running','complete'];assert closure['status'] in ['waiting_for_exact_original_watcher','closing_original_report','closed_original_failures_retained'],closure
  live=[]
  for pid,initial in ids.items():
   current=identity(pid)
   if current and current['state']!='Z':assert current['start_ticks']==initial['start_ticks'] and current['cmd']==initial['cmd'];live.append(pid)
  if not live:
   assert audit['status']=='complete' and closure['status']=='closed_original_failures_retained' and (C/'RESULT.json').exists();break
  assert time.monotonic()-started<21600,'queue deadline reached, no launch or retry'
  save('waiting_for_exact_parent_audit_and_closure',live_parent_pids=live,audit_rows=len(audit['rows']),audit_failures=sum(r['returncode']!=0 for r in audit['rows']),physics_started=False);time.sleep(10)
 result=read(C/'RESULT.json');assert result['audit_invocations']==204 and result['failed_audit_invocations']==[],'parent audit must be fully resolved before new physics'
 save('checking_launch_preflight',physics_started=False)
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1');driver=W/'run_front_drive_1mm_physical.py'
 with (P/'LAUNCH_QUEUE_PREFLIGHT.log').open('x') as log:subprocess.run([sys.executable,str(driver),'--check-only'],cwd=W.parents[1],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for p,h in frozen.items():assert sha(p)==h,p
 assert not R.exists()
 with (P/'PHYSICAL_EXECUTION.log').open('x') as log:proc=subprocess.Popen([sys.executable,str(driver)],cwd=W.parents[1],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 save('driver_started_preflight_still_required',producer_pid=proc.pid,producer_identity=identity(proc.pid),physics_started='verify_new_protocol_and_collector',run=str(R))
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e),physics_started=False);raise
