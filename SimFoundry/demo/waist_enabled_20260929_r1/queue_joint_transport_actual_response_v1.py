"""Wait for the exact current physical producer, then diagnose actual transitions once.
No new collection, no retries, no image-review claims, no training admission.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;R=W/'joint_transport_physical_r1';PLAN=R/'ACTUAL_RESPONSE_QUEUE_PLAN.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(pid):
 p=Path('/proc')/str(pid)
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(start=st[19],state=st[0],cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 except FileNotFoundError:return None
plan=json.loads(PLAN.read_text());records=[]
fd=os.open(R/'ACTUAL_RESPONSE_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
def save(status,**more):
 dest=R/'ACTUAL_RESPONSE_QUEUE_STATUS.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=records,training_ready=False,**more),indent=2));tmp.replace(dest)
try:
 save('waiting_for_exact_producer')
 while len(records)<len(plan['episodes']):
  for f,h in plan['source_sha256'].items():assert sha(f)==h,f
  done={x['episode'] for x in records}
  for name in plan['episodes']:
   if name in done:continue
   ep=R/name;ready=ep/'READY_FOR_AUDIT.json'
   if not ready.exists():continue
   output=ep/'ACTUAL_JOINT_RESPONSE_DIAGNOSIS.json';log=ep/'ACTUAL_JOINT_RESPONSE_DIAGNOSIS.log';assert not output.exists() and not log.exists()
   save('diagnosing',episode=name)
   env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
   with log.open('x') as f:result=subprocess.run([sys.executable,str(W/'diagnose_joint_transport_actual_response_v1.py'),'--episode',str(ep),'--output',str(output)],env=env,stdout=f,stderr=subprocess.STDOUT)
   assert result.returncode==0,(name,result.returncode)
   report=json.loads(output.read_text());assert report['physical_recorded_transitions'] and report['training_ready'] is False
   records.append(dict(episode=name,report=str(output),report_sha256=sha(output),log_sha256=sha(log),selected_transitions=report['selected_transitions'],applied_transitions=report['stats']['applied']['frames']));save('waiting_for_remaining_episode')
  if len(records)==len(plan['episodes']):break
  status=json.loads((R/'STATUS.json').read_text());assert status['status']!='runtime_or_audit_failed',status
  info=identity(plan['producer_pid'])
  if info is None or info['state']=='Z':
   assert status['status']=='collection_complete_audits_visual_pending','Producer ended early'
   raise AssertionError('Producer complete but required ready episode missing')
  assert info['start']==plan['producer_identity']['start'] and info['cmd']==plan['producer_identity']['cmd'],'Producer identity changed'
  time.sleep(15)
 save('actual_transition_diagnoses_complete')
except Exception as e:save('failed_without_retry',error=repr(e));raise
