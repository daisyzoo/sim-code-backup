"""Wait for the already-live lifecycle check, then run only native-file checks.
Never prepare, freeze, launch physics, convert data or train a policy.
"""
from pathlib import Path
import sys,json,time,os,hashlib,subprocess,datetime
w=Path(__file__).resolve().parent;stage=w/'staged_box_center_preference';pid=int(sys.argv[1]);status=w/'BOX_CENTER_NATIVE_ADVANCE_STATUS.json'
def save(state,**kw):
 status.write_text(json.dumps(dict(state=state,pid=os.getpid(),lifecycle_pid=pid,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),training_ready=False,**kw),indent=2))
try:
 save('waiting_for_existing_lifecycle')
 while Path(f'/proc/{pid}/cmdline').exists() and Path(f'/proc/{pid}/cmdline').read_bytes():time.sleep(10)
 p=stage/'LIFECYCLE_CHECK.json';d=json.loads(p.read_text());assert d['passed'] and len(d['rows'])==16
 for f,h in d['source_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
 assert not (stage/'NATIVE_CHECK.json').exists()
 with (w/'box_center_native_files.log').open('x') as log:
  child=subprocess.Popen([sys.executable,str(w/'check_box_center_native_files.py')],stdout=log,stderr=subprocess.STDOUT)
  save('native_reader_running',child_pid=child.pid);code=child.wait()
 assert code==0,('native check failed',code)
 report=json.loads((stage/'NATIVE_CHECK.json').read_text());assert report['passed']
 save('native_reader_complete')
except Exception as exc:
 save('check_failed',error=repr(exc));raise
