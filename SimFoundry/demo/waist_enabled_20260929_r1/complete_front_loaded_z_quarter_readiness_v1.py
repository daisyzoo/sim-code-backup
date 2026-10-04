"""Await the already-running exact full-front checker, then prepare and queue once.
No failed check is retried. Physical queue retains full reviews/GPU/storage gates.
"""
from pathlib import Path
import os,sys,json,hashlib,datetime,time,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'front_loaded_z_quarter_physical_preparation_r1';D=W/'front_loaded_z_quarter_preparation_r1';sys.path[:0]=[str(W),str(ROOT)]
from run_front_loaded_z_quarter_trial1_physical_r1 import identity
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 plan=read(P/'READINESS_CONTINUATION_PLAN.json');fd=os.open(P/'READINESS_CONTINUATION_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 def save(status,**kw):
  p=P/'READINESS_CONTINUATION_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=now(),physics_started=False,training_ready=False,**kw),indent=2));t.replace(p)
 try:
  dep=plan['dependency']
  while True:
   for p,h in plan['source_sha256'].items():assert sha(p)==h,p
   info=identity(dep['pid'])
   if info and info['state']!='Z':
    assert info['start']==dep['start'] and dep['script'].encode() in info['cmd'];save('waiting_for_exact_full_front_checker',dependency=dep);time.sleep(15);continue
   break
  proof=read(dep['report']);assert proof['passed'] is True and proof['frames']==1200 and proof['quarter_enabled'] is False and not proof['training_ready']
  for p,h in proof['source_sha256'].items():assert sha(p)==h,p
  env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',OMNI_KIT_ACCEPT_EULA='yes',EXP_PATH='/home/user/miniconda3/envs/env_isaaclab/lib/python3.12/site-packages/isaacsim/apps',PYTHONUNBUFFERED='1')
  save('checking_complete_configuration')
  with (P/'readiness_configuration.log').open('x') as f:subprocess.run([sys.executable,str(W/'run_front_loaded_z_quarter_trial1_physical_r1.py'),'--configuration-only'],cwd=ROOT.parent,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
  save('preparing_single_physical_queue')
  with (P/'readiness_queue_prepare.log').open('x') as f:subprocess.run([sys.executable,str(W/'queue_front_loaded_z_quarter_trial1_physical_v1.py'),'--prepare'],cwd=ROOT.parent,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
  assert not (W/'front_loaded_z_quarter_physical_r1').exists()
  with (P/'launch_queue.log').open('x') as f:child=subprocess.Popen([sys.executable,str(W/'queue_front_loaded_z_quarter_trial1_physical_v1.py')],cwd=ROOT.parent,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  info=identity(child.pid);assert info is not None
  save('physical_queue_started_once',queue_pid=child.pid,queue_start=info['start'],configuration_sha256=sha(P/'CONFIGURATION_CHECK.json'),full_front_proof_sha256=sha(dep['report']),remaining='Queue must verify preceding full10actual reviews, exact producer termination, GPU and original storage budget. Not model success.')
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':main()
