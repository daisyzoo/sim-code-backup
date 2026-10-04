"""Wait for the exact original parent closure, then preflight and launch once.
No restart of existing jobs, no shortened trial, no task/admission gate changes.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'inactive_transport_physical_preparation_r1';R=W/'front_box_recenter_physical_r2';OUT=W/'inactive_transport_physical_r1';RUNNER=W/'run_inactive_transport_trial1_physical_r1.py'
AUDIT=dict(pid=4015378,start='90492990',script='watch_front_box_recenter_trial2_physical_audits_r1.py')
CLOSURE=dict(pid=4045036,start='90784360',script='queue_front_box_recenter_trial2_physical_r1_closure.py')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(state=a[0],start=a[19],cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except (FileNotFoundError,ProcessLookupError):return None
def exact_live(expected):
 got=identity(expected['pid'])
 return bool(got and got['state']!='Z' and got['start']==expected['start'] and expected['script'] in got['cmd'])
def decision(status,rows,audit_live,closure_live,result_exists,gpu_busy):
 if audit_live:return 'wait_exact_original_audit'
 if status!='complete' or rows!=214:return 'stop_original_audit_not_complete'
 if closure_live:return 'wait_exact_original_closure'
 if not result_exists:return 'stop_original_closure_missing'
 if gpu_busy:return 'wait_gpu'
 return 'preflight'
def check():
 checks=[('running',100,True,True,False,False,'wait_exact_original_audit'),('complete',214,True,True,True,False,'wait_exact_original_audit'),('running',100,False,True,False,False,'stop_original_audit_not_complete'),('auditor_failed',100,False,False,False,False,'stop_original_audit_not_complete'),('complete',213,False,False,True,False,'stop_original_audit_not_complete'),('complete',214,False,True,True,False,'wait_exact_original_closure'),('complete',214,False,False,False,False,'stop_original_closure_missing'),('complete',214,False,False,True,True,'wait_gpu'),('complete',214,False,False,True,False,'preflight')]
 for *args,want in checks:assert decision(*args)==want
 required=[P/'PLAN.json',P/'PHYSICAL_PREPARATION.json',P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json',P/'CONFIGURATION_CHECK.json',P/'AUDIT_DEPENDENCIES.json']
 assert read(P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json')['passed'] and read(P/'CONFIGURATION_SOURCE_AUDIT_CHECK.json')['expected_audits']==224
 assert read(P/'CONFIGURATION_CHECK.json')['passed'] and read(P/'CONFIGURATION_CHECK.json')['total_audits']==224
 sources={str(p):sha(p) for p in [Path(__file__),RUNNER,*required] if p.name!='CONFIGURATION_CHECK.json'}
 for manifest in [read(P/'PHYSICAL_PREPARATION.json'),read(W/'staged_inactive_transport_v2/AUDIT_FAMILY_V3_PREPARATION.json')]:
  for r in manifest.get('files',[])+manifest.get('adapters',[]):sources[r['path']]=r['sha256']
 sources.update(read(P/'AUDIT_DEPENDENCIES.json')['source_sha256'])
 for p,h in sources.items():assert sha(p)==h,p
 from rear_corridor_storage_budget import require_storage
 storage=require_storage(ROOT,read(P/'PLAN.json')['commands'])
 return dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision_cases=len(checks),audit=AUDIT,closure=CLOSURE,storage=storage,source_sha256=sources,training_ready=False)
def main():
 checked=check();assert not OUT.exists();fd=os.open(P/'LAUNCH_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 (P/'LAUNCH_QUEUE_CHECK.json').write_text(json.dumps(checked,indent=2))
 def save(state,**extra):
  data=dict(status=state,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),training_ready=False,**extra);tmp=P/'LAUNCH_QUEUE_STATUS.tmp';tmp.write_text(json.dumps(data,indent=2));tmp.replace(P/'LAUNCH_QUEUE_STATUS.json')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1')
 try:
  while True:
   for p,h in checked['source_sha256'].items():assert sha(p)==h,p
   status=read(R/'AUDIT_STATUS.json');audit_live=exact_live(AUDIT);closure_live=exact_live(CLOSURE);gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,check=True)
   action=decision(status['status'],len(status['rows']),audit_live,closure_live,(R/'RESULT.json').exists(),bool(gpu.stdout.strip()))
   save(action,parent_audit_rows=len(status['rows']),parent_audit_live=audit_live,parent_closure_live=closure_live,physics_started=False)
   if action.startswith('stop_'):return
   if action=='preflight':
    from rear_corridor_storage_budget import require_storage
    try:storage=require_storage(ROOT,read(P/'PLAN.json')['commands'])
    except AssertionError as e:save('wait_original_storage_gate',reason=str(e),physics_started=False);time.sleep(20);continue
    with (P/'queued_preflight.log').open('x') as log:p=subprocess.run([sys.executable,str(RUNNER),'--check-only'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if p.returncode:save('preflight_failed_no_launch',returncode=p.returncode,physics_started=False);return
    assert not OUT.exists()
    with (P/'producer.log').open('x') as log:producer=subprocess.Popen([sys.executable,str(RUNNER)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    got=identity(producer.pid);assert got is not None
    launch=dict(launched_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=producer.pid,start_ticks=got['start'],script=str(RUNNER),runner_sha256=sha(RUNNER),run=str(OUT),conditions=10,audits=224,preflight_sha256=sha(P/'LAUNCH_PREFLIGHT.json'),training_ready=False)
    with (P/'LAUNCH.json').open('x') as f:json.dump(launch,f,indent=2)
    save('producer_launched_after_full_preflight',launch=launch,physics_success=False);return
   time.sleep(20)
 except Exception as e:save('queue_failed_no_retry',error=repr(e));raise
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--check-only',action='store_true');a=ap.parse_args()
 if a.check_only:print(json.dumps({k:v for k,v in check().items() if k!='source_sha256'}))
 else:main()
