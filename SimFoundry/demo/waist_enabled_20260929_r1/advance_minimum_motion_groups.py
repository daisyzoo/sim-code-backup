"""Continue already-authorized preflight, then freeze/launch one full diagnostic.
Waits only for the existing confirmed lifecycle checker. Any failed preflight,
changed source,existing run or another collector stops this chain. Never trains.
"""
from pathlib import Path
import os,sys,json,hashlib,subprocess,time,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';run=w/'minimum_motion_groups_r1';status_path=w/'MINIMUM_MOTION_ADVANCE_STATUS.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();lifecycle_pid=int(sys.argv[1]);env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1',DISPLAY=':1');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH']
def status(phase,**kw):
 d=dict(phase=phase,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw);temp=status_path.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2));temp.replace(status_path);print(json.dumps(d),flush=True)
def validate(p):
 d=json.loads(p.read_text());assert d.get('passed',d.get('complete',False)),p
 for n,h in d.get('source_sha256',{}).items():assert sha(n)==h,(p,n)
 return d
def child(script,log):
 with log.open('w') as stream:
  process=subprocess.Popen([sys.executable,str(w/script)],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT);status('running_preflight',script=script,child_pid=process.pid,log=str(log));code=process.wait()
 assert code==0,(script,code,str(log))
try:
 status('waiting_existing_lifecycle',lifecycle_pid=lifecycle_pid)
 while True:
  p=Path(f'/proc/{lifecycle_pid}/cmdline')
  try:args=p.read_bytes().split(b'\0')
  except FileNotFoundError:break
  if not any(a.endswith(b'/check_minimum_motion_lifecycle.py') for a in args):break
  time.sleep(2)
 life=validate(stage/'LIFECYCLE_CHECK.json');assert len(life['rows'])==16 and all(r['summary']['completed'] for r in life['rows'])
 assert not (stage/'LIVE_FILES_CHECK.json').exists(),'Native reader already has a report; inspect rather than overwrite'
 child('check_minimum_motion_native_files.py',w/'minimum_motion_native_files.log');validate(stage/'LIVE_FILES_CHECK.json')
 for name in ['INTEGRATION_CHECK.json','PRELAUNCH_CHECK.json','AUDIT_VERSION_CHECK.json','RUNTIME_PLANNER_CHECK.json','INDEPENDENT_AUDIT_CHECK.json','LIFECYCLE_CHECK.json','LIVE_FILES_CHECK.json','RUN_PROTOCOL_CHECK.json']:validate(stage/name)
 assert not run.exists()
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:args=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  assert not any(b'SimFoundry/' in a and a.endswith(b'.py') and Path(a.decode(errors='replace')).name.startswith('collect_') for a in args),('existing_collector',p.name)
 child('prepare_minimum_motion_groups.py',w/'minimum_motion_prepare.log');protocol=json.loads((run/'PROTOCOL.json').read_text());assert len(protocol['commands'])==6
 pids={}
 for key,name,log in [('runner','run_minimum_motion_groups.py','runner.log'),('watcher','watch_minimum_motion_audits.py','audits.log')]:
  with (run/log).open('w') as stream:process=subprocess.Popen([sys.executable,str(w/name),str(run)],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  pids[key]=process.pid
 (run/'LAUNCH.json').write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pids=pids,protocol_sha256=sha(run/'PROTOCOL.json'),training_ready=False),indent=2));status('full_diagnostic_launched',pids=pids,run=str(run),protocol_sha256=sha(run/'PROTOCOL.json'))
except Exception as exc:status('stopped_on_preflight_or_runtime_error',error=repr(exc));raise
