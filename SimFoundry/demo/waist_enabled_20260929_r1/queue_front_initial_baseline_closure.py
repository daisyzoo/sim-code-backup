"""Finish matched baseline reports only after exact auditors finish.
Does not label images, waive failed gates, rerun collection, or admit training.
"""
from pathlib import Path
import json,hashlib,os,sys,time,datetime,subprocess
W=Path(__file__).resolve().parent;B=W/'front_initial_margin_baseline_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(status,**kw):
 p=B/'CLOSURE_QUEUE_STATUS.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2));t.replace(p)
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 try:s=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:return None
 return dict(start=s[21],state=s[2],cmd=[x.decode() for x in cmd if x])
def main():
 fd=os.open(B/'CLOSURE_QUEUE_LOCK',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 assert not (B/'RESULT.json').exists() and not (B/'RESULT_WITH_SUPPLEMENT.json').exists()
 numeric=json.loads((B/'NUMERIC_VISUAL_SUMMARY.json').read_text());assert numeric['conditions']==10 and numeric['expected_distinct_audit_invocations']==194
 frozen={**numeric['source_sha256'],str(B/'NUMERIC_VISUAL_SUMMARY.json'):sha(B/'NUMERIC_VISUAL_SUMMARY.json')}
 for p in [Path(__file__),W/'close_front_initial_margin_baseline.py',W/'close_terminal_margin_with_supplement.py']:frozen[str(p)]=sha(p)
 watchers={}
 for name,script in [('AUDIT_STATUS.json','watch_front_initial_margin_baseline.py'),('STABILITY_SUPPLEMENT_STATUS.json','watch_terminal_margin_stability_supplement.py')]:
  state=json.loads((B/name).read_text());info=identity(state['pid']);assert state['status'] in ('running','complete')
  if info is not None and info['state']!='Z':assert str(W/script) in info['cmd']
  else:assert state['status']=='complete'
  watchers[name]=dict(pid=state['pid'],identity=info)
 started=time.monotonic()
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  states={};all_done=True
  for name,watch in watchers.items():
   state=json.loads((B/name).read_text());info=identity(watch['pid']);assert state['pid']==watch['pid'] and state['status'] in ('running','complete'),state.get('error',state['status'])
   if info is not None and info['state']!='Z':
    assert info['start']==watch['identity']['start'] and info['cmd']==watch['identity']['cmd'];all_done=False
   else:assert state['status']=='complete','auditor exited before complete evidence'
   states[name]=state
  if all_done:break
  assert time.monotonic()-started<21600,'closure queue timeout; no restart'
  save('waiting_for_original_auditors',audit_rows=len(states['AUDIT_STATUS.json']['rows']),supplement_rows=len(states['STABILITY_SUPPLEMENT_STATUS.json']['rows']),watchers=watchers)
  time.sleep(10)
 assert len(states['AUDIT_STATUS.json']['rows'])==194 and len(states['AUDIT_STATUS.json']['completed_episodes'])==10
 assert len(states['STABILITY_SUPPLEMENT_STATUS.json']['rows'])==8
 for script in ['close_front_initial_margin_baseline.py','close_terminal_margin_with_supplement.py']:
  save('closing_reports',script=script)
  with (B/(script+'.closure.log')).open('x') as f:subprocess.run([sys.executable,str(W/script),str(B),'--apply'],cwd=W.parents[1],stdout=f,stderr=subprocess.STDOUT,check=True)
 result=json.loads((B/'RESULT_WITH_SUPPLEMENT.json').read_text());assert result['conditions']==10 and result['push_passed']==numeric['push_passed'] and result['wait_passed']==numeric['wait_passed']
 save('closed_original_and_supplement_reports',result_sha256=sha(B/'RESULT.json'),supplement_result_sha256=sha(B/'RESULT_WITH_SUPPLEMENT.json'),unresolved_audits=result['unresolved_audits'])
if __name__=='__main__':
 try:main()
 except Exception as e:save('stopped_without_retry',error=repr(e));raise
