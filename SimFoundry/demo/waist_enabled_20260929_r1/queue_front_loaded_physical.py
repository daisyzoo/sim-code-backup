"""Wait for exact parent closure, then preflight and launch one full diagnostic.
No automatic retry, skipped gate, failed-data admission or model success claim.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;ROOT=W.parents[1];C=W/'front_initial_physical_r1';P=W/'front_loaded_physical_preparation_r1';S=W/'staged_front_loaded_reference';OUT=W/'front_loaded_physical_r1'
from run_front_loaded_physical import CHECKS,MANIFESTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:s=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return None
 return dict(start=s[21],state=s[2],cmd=[x.decode() for x in cmd if x])
def save(status,**kw):
 p=P/'LAUNCH_QUEUE_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));t.replace(p)
def main():
 fd=os.open(P/'LAUNCH_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd);assert not OUT.exists()
 previous=read(C/'CLOSURE_QUEUE_STATUS.json');watch=dict(pid=previous['pid'],identity=identity(previous['pid']))
 if watch['identity'] is not None and watch['identity']['state']!='Z':assert str(W/'queue_front_initial_physical_closure.py') in watch['identity']['cmd']
 else:assert previous['status']=='closed_original_and_separate_supplement_reports'
 prep=read(S/'PREPARATION.json');files=[Path(__file__),W/'run_front_loaded_physical.py',P/'PLAN.json',C/'PROTOCOL.json',S/'PREPARATION.json',*[S/n for n in prep['stage_sha256']],*[W/n for n in CHECKS+MANIFESTS]];frozen={str(p):sha(p) for p in files}
 started=time.monotonic()
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  state=read(C/'CLOSURE_QUEUE_STATUS.json');info=identity(watch['pid']);assert state['pid']==watch['pid']
  assert state['status'] in ('waiting_for_exact_original_and_supplement_watchers','closing_reports','closed_original_and_separate_supplement_reports'),state
  if info is not None and info['state']!='Z':
   assert watch['identity'] is not None and info['start']==watch['identity']['start'] and info['cmd']==watch['identity']['cmd']
  else:
   assert state['status']=='closed_original_and_separate_supplement_reports','parent closure process vanished before completion'
   break
  assert time.monotonic()-started<21600,'queue timeout; no restart'
  save('waiting_for_parent_full_closure',parent_closure=watch,parent_status=state['status'],parent_original_audits=len(read(C/'AUDIT_STATUS.json')['rows']),parent_region_supplements=len(read(C/'REGION_SUPPLEMENT_STATUS.json')['rows']),frozen_sha256=frozen)
  time.sleep(10)
 result=read(C/'RESULT_WITH_REGION_SUPPLEMENT.json');assert result['conditions']==10 and result['unresolved_audits']==[],'parent unresolved control errors require diagnosis'
 env=dict(os.environ,OMNI_KIT_ACCEPT_EULA='yes',OPENBLAS_NUMTHREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1')
 save('complete_preflight_before_launch',parent_result_sha256=sha(C/'RESULT_WITH_REGION_SUPPLEMENT.json'))
 with (P/'QUEUED_PREFLIGHT.log').open('x') as f:subprocess.run([sys.executable,str(W/'run_front_loaded_physical.py'),'--check-only'],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 for p,h in frozen.items():assert sha(p)==h,p
 assert not OUT.exists()
 with (P/'RUNNER.log').open('x') as f:child=subprocess.Popen([sys.executable,str(W/'run_front_loaded_physical.py')],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 receipt=dict(pid=child.pid,script=str(W/'run_front_loaded_physical.py'),out=str(OUT),parent_result_sha256=sha(C/'RESULT_WITH_REGION_SUPPLEMENT.json'),training_ready=False)
 with (P/'LAUNCH.json').open('x') as f:json.dump(receipt,f,indent=2)
 save('launched_once_after_complete_preflight',runner=receipt)
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
