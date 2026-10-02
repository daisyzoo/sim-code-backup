"""Separately audit every new push after original auditing; retain original failures."""
from pathlib import Path
import json,hashlib,datetime,sys,os,time,traceback
from audit_terminal_margin_contact_stability_supplement import audit
W=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
check=json.loads((W/'TERMINAL_MARGIN_STABILITY_SUPPLEMENT_CHECK.json').read_text());assert check['passed'] and len(check['negative_checks'])==4
frozen=dict(check['source_sha256']);frozen[str(Path(__file__))]=sha(__file__);frozen[str(R/'PROTOCOL.json')]=sha(R/'PROTOCOL.json');plan=json.loads((R/'PROTOCOL.json').read_text())['plan'];records=[]
with (R/'STABILITY_SUPPLEMENT_PROTOCOL.json').open('x') as f:json.dump(dict(frozen_sha256=frozen,check_sha256=sha(W/'TERMINAL_MARGIN_STABILITY_SUPPLEMENT_CHECK.json'),pid=os.getpid(),scope=__doc__,training_ready=False),f,indent=2)
def save(status,**kwargs):
 p=R/'STABILITY_SUPPLEMENT_STATUS.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=records,training_ready=False,**kwargs),indent=2));tmp.replace(p)
try:
 save('running')
 while True:
  for p,h in frozen.items():assert sha(p)==h,p
  for item in plan['commands']:
   if item['wait']:continue
   for task in item['tasks']:
    ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";execution=ep/'AUDIT_EXECUTION.json'
    if any(r['episode']==ep.name for r in records) or not execution.exists():continue
    original=json.loads(execution.read_text())
    if not original['completed']:continue
    row=dict(episode=ep.name,original_execution_sha256=sha(execution),original_failed_audits=[r['script'] for r in original['rows'] if r['returncode']],training_ready=False)
    try:
     result=audit(ep);dest=ep/'TERMINAL_MARGIN_CONTACT_STABILITY_SUPPLEMENT.json'
     if dest.exists():assert json.loads(dest.read_text())==result
     else:
      with dest.open('x') as f:json.dump(result,f,indent=2)
     row.update(passed=result['control_checks_passed'],report_sha256=sha(dest),error=None)
    except Exception as e:row.update(passed=False,error=repr(e));(ep/'STABILITY_SUPPLEMENT_FAILURE.log').write_text(traceback.format_exc())
    records.append(row);save('running');print(json.dumps(row),flush=True)
  if len(records)==8:save('complete');break
  state=json.loads((R/'STATUS.json').read_text());audit_state=json.loads((R/'AUDIT_STATUS.json').read_text())
  if state['status']=='runtime_or_audit_failed' or audit_state['status'] in ('auditor_failed','incomplete'):save('incomplete',producer_status=state['status'],original_auditor_status=audit_state['status']);break
  time.sleep(5)
except Exception as e:save('failed',error=repr(e));raise
