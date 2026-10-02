"""Audit every immutable ready rear-corridor diagnostic condition once per check.
Distinct original audits all retained, identical duplicate scheduling removed.
Every task or audit failure stays recorded. No training approval.
"""
from pathlib import Path
import sys,os,json,time,datetime,hashlib
W=Path(__file__).resolve().parent
from rear_tracking_run_contract import primary,controls,ADDITIONAL,run_audit
from close_closed_peak_trials import live
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path(sys.argv[1]).resolve();protocol=json.loads((R/'PROTOCOL.json').read_text());plan=protocol['plan'];completed=[];all_rows=[]
def unchanged():
 for name,h in protocol['frozen_files_sha256'].items():assert sha(name)==h,name

def save(status,**kw):
 tmp=R/'AUDIT_STATUS.tmp';tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_episodes=completed,rows=all_rows,training_ready=False,**kw),indent=2));tmp.replace(R/'AUDIT_STATUS.json')
try:
 save('running')
 while True:
  unchanged()
  for item in plan['commands']:
   for task in item['tasks']:
    ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";ready=ep/'READY_FOR_AUDIT.json'
    if ep.name in completed or not ready.exists():continue
    marker=json.loads(ready.read_text())
    for name,h in marker['source_sha256'].items():assert sha(name)==h,name
    scripts=primary(item['wait'])+['audit_rear_tracking_stage_contacts.py','audit_rear_tracking_stage_pressure.py']
    if not item['wait']:scripts+=controls(json.loads((ep/'frontal_bypass.json').read_text())['plan'])+ADDITIONAL
    unique=list(dict.fromkeys(scripts));rows=[]
    for script in unique:
     unchanged();save('running',current_episode=ep.name,current_auditor=script);row=run_audit(ep,script);rows.append(row);all_rows.append(row);print(json.dumps(row),flush=True)
     (ep/'AUDIT_EXECUTION.json').write_text(json.dumps(dict(completed=False,requested_audits=scripts,distinct_applicable_audits=unique,rows=rows,training_ready=False),indent=2))
    (ep/'AUDIT_EXECUTION.json').write_text(json.dumps(dict(completed=True,requested_audits=scripts,distinct_applicable_audits=unique,duplicate_invocations_removed=len(scripts)-len(unique),rows=rows,training_ready=False),indent=2));completed.append(ep.name);save('running')
  if len(completed)==10:save('complete');break
  status=json.loads((R/'STATUS.json').read_text())
  if status['status']=='runtime_or_audit_failed' or (not live(protocol['producer_pid'],'run_rear_tracking_physical.py') and status['status']!='collection_complete_audits_visual_pending'):save('incomplete',producer_status=status);break
  time.sleep(5)
except Exception as e:save('auditor_failed',error=repr(e));raise
