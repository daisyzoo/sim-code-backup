"""Close the complete ten-condition joint-transport comparison after its exact audit exits.
Preserve short failures and every original audit result. No retries/admission.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;C=W/'front_box_trailing_physical_r2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 try:s=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return None
 return dict(start=s[21],state=s[2],cmd=[x.decode() for x in cmd if x])
def save(status,**kw):
 p=C/'CLOSURE_QUEUE_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));t.replace(p)
def main():
 fd=os.open(C/'CLOSURE_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd);assert not (C/'RESULT.json').exists()
 summary=read(C/'NUMERIC_VISUAL_SUMMARY.json');assert len(summary['rows'])==summary['actual_reviews']==10
 state=read(C/'STATUS.json');assert state['completed_conditions']==10 and state['status']=='collection_complete_audits_visual_pending'
 frozen=dict(summary['source_sha256'])
 for p in [Path(__file__),C/'NUMERIC_VISUAL_SUMMARY.json',W/'close_front_box_trailing_trial2_physical_v1.py',C/'PROTOCOL.json']:frozen[str(p)]=sha(p)
 audit=read(C/'AUDIT_STATUS.json');pid=audit['pid'];ident=identity(pid)
 if ident and ident['state']!='Z':assert str(W/'watch_front_box_trailing_trial2_physical_audits_r1.py') in ident['cmd'] and str(C) in ident['cmd']
 else:assert audit['status']=='complete'
 started=time.monotonic()
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  audit=read(C/'AUDIT_STATUS.json');assert audit['pid']==pid and audit['status'] in ('running','complete'),audit['status'];current=identity(pid)
  if current and current['state']!='Z':assert ident and current['start']==ident['start'] and current['cmd']==ident['cmd']
  else:assert audit['status']=='complete';break
  # A live original watcher is not terminal merely because wall-clock time elapsed.
  save('waiting_for_exact_original_watcher',watcher_pid=pid,watcher_identity=ident,audit_rows=len(audit['rows']),frozen_sha256=frozen);time.sleep(10)
 assert len(audit['rows'])==224 and len(audit['completed_episodes'])==10
 # Final comparison requires the direct parent's complete original report.
 parent=W/'joint_transport_reserve_physical_r1';parent_queue=read(parent/'CLOSURE_QUEUE_STATUS.json');parent_pid=parent_queue['pid'];parent_identity=identity(parent_pid)
 while not (parent/'RESULT.json').exists():
  current=identity(parent_pid);assert current and current['state']!='Z' and parent_identity and current['start']==parent_identity['start'] and current['cmd']==parent_identity['cmd'],'parent closure ended without result'
  assert str(W/'queue_joint_transport_reserve_trial1_physical_r1_closure_v1.py') in current['cmd']
  for p,h in frozen.items():assert sha(p)==h,p
  save('waiting_for_direct_parent_complete_result',parent_closure_pid=parent_pid,audit_rows=224);time.sleep(10)
 save('closing_original_report',audit_rows=224)
 with (C/'close_front_box_trailing_trial2_physical_v1.py.closure.log').open('x') as f:subprocess.run([sys.executable,str(W/'close_front_box_trailing_trial2_physical_v1.py'),str(C),'--apply'],cwd=W.parents[2],stdout=f,stderr=subprocess.STDOUT,check=True)
 result=read(C/'RESULT.json');assert result['conditions']==10 and result['push_passed']==summary['push_passed'] and result['wait_passed']==summary['wait_passed']
 save('closed_original_failures_retained',result_sha256=sha(C/'RESULT.json'),audit_invocations=result['audit_invocations'],failed_audit_invocations=len(result['failed_audit_invocations']),push_passed=result['push_passed'],wait_passed=result['wait_passed'])
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
