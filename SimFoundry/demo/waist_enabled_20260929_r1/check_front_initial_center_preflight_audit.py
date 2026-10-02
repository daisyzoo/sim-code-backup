"""Independent replay of all8 causal plan-selection records; no candidate imports."""
from pathlib import Path
import sys,json,hashlib,datetime,os
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_preflight import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fixture=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';data=json.loads(fixture.read_text());assert data['status']=='complete'
out=W/'FRONT_INITIAL_CENTER_PREFLIGHT_AUDIT_CHECK.json';assert not out.exists();report=dict(status='running',pid=os.getpid(),scope=__doc__,rows=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),fixture,W/'audit_front_initial_center_preflight.py',W/'audit_front_initial_center_events.py']})
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
try:
 save()
 for original in data['records']:
  p=original['plan'];ctx=p['transport_preflight']['initial_context'];auditor=SelectionAudit(ROOT,S)
  result=auditor.verify_selection(p,current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],decay=ctx['decay'],scene=p['scene'],step=ctx['step'])
  report['rows'].append(dict(episode=original['episode'],**result));save();print(original['episode'],result,flush=True)
 assert not any(n.startswith('front_initial_center_') for n in sys.modules),'Auditor imported candidate'
 report.update(status='complete',passed=True);save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
