"""Wait for the exact matched producer, then launch one fully checked candidate.
Never restart a producer, ignore a failed state, or equate timeout with success.
"""
from pathlib import Path
import os,sys,json,time,datetime,subprocess,hashlib
W=Path(__file__).resolve().parent; ROOT=W.parents[1]; B=W/'front_initial_margin_baseline_r1'; P=W/'front_initial_physical_preparation_r1'; C=W/'front_initial_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(status,**kw):
 p=P/'QUEUE_STATUS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));tmp.replace(p)
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 try:
  stat=(p/'stat').read_text();cmd=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return None
 return dict(starttime=stat.split()[21],zombie=stat.split()[2]=='Z',cmd=[s.decode() for s in cmd if s])
def main():
 lock=P/'QUEUE_LOCK';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 protocol=json.loads((B/'PROTOCOL.json').read_text());pid=protocol['producer_pid'];initial=identity(pid)
 assert initial is not None and not initial['zombie'] and str(W/'run_front_initial_margin_baseline.py') in initial['cmd'],'exact matched baseline must be live when queued'
 assert not C.exists()
 bound={str(p):sha(p) for p in [B/'PROTOCOL.json',P/'PLAN.json',W/'run_front_initial_physical.py',W/'watch_front_initial_physical_audits.py',Path(__file__)]}
 started=time.monotonic()
 while True:
  for p,h in bound.items():assert sha(p)==h,p
  state=json.loads((B/'STATUS.json').read_text());audit=json.loads((B/'AUDIT_STATUS.json').read_text());current=identity(pid)
  if current is not None and not current['zombie']:assert current==initial,'parent process identity changed'
  assert state['status'] in ('starting','collecting','collection_complete_audits_visual_pending'),state
  assert audit['status'] in ('running','complete'),audit.get('error',audit['status'])
  if state['status']=='collection_complete_audits_visual_pending' and (current is None or current['zombie']):
   assert state['completed_conditions']==10;break
  assert current is not None and not current['zombie'],'matched baseline exited without terminal collection evidence'
  assert time.monotonic()-started<21600,'queue timed out without launch; parent is never restarted'
  save('waiting_for_matched_parent',parent_pid=pid,parent_starttime=initial['starttime'],completed_conditions=state['completed_conditions'],frozen_queue_inputs=bound)
  time.sleep(10)
 assert not C.exists();save('checking_candidate_preflight',parent_pid=pid,frozen_queue_inputs=bound)
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',PYTHONUNBUFFERED='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 cmd=[sys.executable,str(W/'run_front_initial_physical.py'),'--out',str(C)]
 with (P/'QUEUE_PREFLIGHT.log').open('x') as log:subprocess.run(cmd+['--check-only'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 for p,h in bound.items():assert sha(p)==h,p
 with (P/'PHYSICAL_RUNNER.log').open('x') as log:child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 launch=dict(pid=child.pid,command=cmd,launched_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(W/'run_front_initial_physical.py'),preflight_sha256=sha(P/'LAUNCH_PREFLIGHT.json'),training_ready=False)
 with (P/'LAUNCH.json').open('x') as f:json.dump(launch,f,indent=2)
 save('launched_once',launch=launch)
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
