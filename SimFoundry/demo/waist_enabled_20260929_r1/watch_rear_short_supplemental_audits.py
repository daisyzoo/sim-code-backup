"""Supplement the known collector-version mismatch, retaining all original failures.
Read-only physics inputs. No original audit/report replacement or simulation.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,datetime,time,os
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();script=w/'audit_rear_short_unchanged_loaded_execution.py';check=w/'REAR_SHORT_SUPPLEMENTAL_AUDIT_CHECK.json';c=json.loads(check.read_text());assert c['passed'] and c['original_math_ast_exact']
for p,h in c['source_sha256'].items():assert sha(p)==h
frozen={str(p):sha(p) for p in [script,Path(__file__),check,w/'check_rear_short_supplemental_audit.py',r/'PROTOCOL.json']};rows=[];done=set();report='REAR_SHORT_UNCHANGED_LOADED_EXECUTION_AUDIT.json';manifest=r/'SUPPLEMENTAL_AUDIT_PROTOCOL.json';assert not manifest.exists();manifest.write_text(json.dumps(dict(source_sha256=frozen,scope=__doc__,training_ready=False),indent=2))
def save(status):
 p=r/'SUPPLEMENTAL_AUDIT_EXECUTION.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(stage=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,source_sha256=frozen,training_ready=False),indent=2));tmp.replace(p)
save('running')
while True:
 for p,h in frozen.items():assert sha(p)==h
 original=json.loads((r/'ADDITIONAL_AUDIT_EXECUTION.json').read_text())
 for old in original['rows']:
  if old.get('script')!='audit_micro_unchanged_loaded_execution.py' or old['episode'] in done:continue
  ep=next(r.glob('case_*/'+old['episode']));log=ep/'audit_micro_unchanged_loaded_execution.py.log'
  assert old['returncode']==1 and sha(log)==old['log_sha256']
  assert "sha(w/'staged_micro_clearance_return'/name)" in log.read_text() and log.read_text().strip().endswith('AssertionError')
  if (ep/report).exists():
   d=json.loads((ep/report).read_text());assert d['auditor_sha256']==sha(script);code=0 if d['passed'] else 1
  else:
   proc=subprocess.run([sys.executable,str(script),str(ep)],capture_output=True,text=True);(ep/'supplemental_loaded_execution.log').write_text(proc.stdout+'\n'+proc.stderr);code=proc.returncode;d=json.loads((ep/report).read_text()) if (ep/report).exists() else {}
  rows.append(dict(episode=ep.name,returncode=code,passed=d.get('passed',False),original_failure_retained=True,original_log_sha256=sha(log),auditor_sha256=sha(script),report_sha256=sha(ep/report) if (ep/report).exists() else None,raw_sha256=sha(ep/'raw.npz')));done.add(ep.name);save('running');print(json.dumps(rows[-1]),flush=True)
 if len(done)==8:save('complete');break
 if original['stage'] not in ['running'] and len(done)<8:save('incomplete');break
 time.sleep(10)
