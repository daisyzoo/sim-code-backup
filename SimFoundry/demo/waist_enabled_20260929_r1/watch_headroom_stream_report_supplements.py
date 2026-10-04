"""Bind new-name stream reports without rewriting frozen original failed rows.
Only successful original native stream processes are eligible. Actual failures
remain failed; no new physical trajectory, gate relaxation or training approval.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
W=Path(__file__).resolve().parent;R=W/'front_recontact_headroom_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 s=(p/'stat').read_text().rsplit(')',1)[1].split();return dict(start=s[19],state=s[0],cmd=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x])
def main():
 lock=R/'STREAM_ROUTING_SUPPLEMENT_LOCK';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 audit=read(R/'AUDIT_STATUS.json');pid=audit['pid'];ident=identity(pid);assert ident and str(W/'watch_front_recontact_headroom_physical_audits_r1.py') in ident['cmd'];completed={};frozen={str(p):sha(p) for p in [Path(__file__),W/'verify_headroom_stream_report_routing.py',W/'front_recontact_headroom_v3_stage_run_contract.py',W/'audit_front_recontact_headroom_stream.py']}
 def save(status,**extra):
  dest=R/'STREAM_ROUTING_SUPPLEMENT_STATUS.json';tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),watcher_pid=pid,watcher_identity=ident,rows=list(completed.values()),training_ready=False,**extra),indent=2));tmp.replace(dest)
 try:
  while True:
   for p,h in frozen.items():assert sha(p)==h,p
   a=read(R/'AUDIT_STATUS.json');assert a['pid']==pid and a['status'] in ('running','complete')
   for row in a['rows']:
    if row['script']!='audit_front_recontact_headroom_stream.py' or row['episode'] in completed:continue
    ep=next(R.glob('case_*/'+row['episode']));dest=ep/'HEADROOM_STREAM_REPORT_ROUTING_SUPPLEMENT.json'
    if row['process_returncode']!=0:
     assert not dest.exists();completed[ep.name]=dict(episode=ep.name,status='original_native_failure_retained',original_row=row);continue
    if not dest.exists():
     save('verifying_original_successful_stream',episode=ep.name)
     with (ep/'HEADROOM_STREAM_ROUTING_VERIFY.log').open('x') as f:subprocess.run([sys.executable,str(W/'verify_headroom_stream_report_routing.py'),str(ep)],stdout=f,stderr=subprocess.STDOUT,check=True)
    d=read(dest);assert d['passed'] and d['original_failure_retained'] and d['original_audit_row']==row
    for p,h in d['source_sha256'].items():assert sha(p)==h,p
    completed[ep.name]=dict(episode=ep.name,status='verified_reporting_mismatch_only',supplement_sha256=sha(dest),verified_commands=d['verified_commands'],handovers=d['handovers'])
   if len(completed)==10:save('complete_original_rows_retained');return
   current=identity(pid)
   if current is None or current['state']=='Z':assert a['status']=='complete';raise AssertionError('original watcher ended before ten stream results')
   assert current['start']==ident['start'] and current['cmd']==ident['cmd'];save('waiting_for_exact_original_auditor');time.sleep(10)
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
if __name__=='__main__':main()
