"""Close complete diagnostic evidence with separate legacy-formula correction.
Original failed reports remain authoritative historical records. Task failures stay failed.
"""
from pathlib import Path
import json,hashlib,datetime,sys
from audit_terminal_margin_contact_stability_supplement import audit
W=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):
 sources[str(p)]=sha(p);return json.loads(p.read_text())
def bound(m):
 for p,h in m.items():assert sha(p)==h,p
base=read(R/'RESULT.json');status=read(R/'STABILITY_SUPPLEMENT_STATUS.json');protocol=read(R/'STABILITY_SUPPLEMENT_PROTOCOL.json')
assert base['conditions']==10 and status['status']=='complete' and len(status['rows'])==8
p=Path('/proc')/str(status['pid']);assert not p.exists() or (p/'stat').read_text().split()[2]=='Z'
bound(protocol['frozen_sha256']);bound(base['source_sha256']);bound(read(R/'PROTOCOL.json')['frozen_files_sha256'])
results=[]
for item in base['rows']:
 row=dict(item)
 if not row['wait']:
  ep=next(R.glob('case_*/'+row['episode']));old=read(ep/'CONTACT_STABILITY_CONTROL_AUDIT.json');new=read(ep/'TERMINAL_MARGIN_CONTACT_STABILITY_SUPPLEMENT.json');assert audit(ep)==new
  observed=next(x for x in status['rows'] if x['episode']==ep.name);assert observed['report_sha256']==sha(ep/'TERMINAL_MARGIN_CONTACT_STABILITY_SUPPLEMENT.json')
  bound({str(ep/k):v for k,v in old['source_sha256'].items()})
  remaining=list(row['failed_audits']);correctable=all(e['kind']=='position_confirmation_mismatch' for e in old['errors']) and new['control_checks_passed']
  if 'audit_contact_stability_control.py' in remaining and correctable:remaining.remove('audit_contact_stability_control.py')
  if not new['control_checks_passed']:remaining.append('audit_terminal_margin_contact_stability_supplement.py')
  row.update(original_failed_audits=row['failed_audits'],unresolved_audits=remaining,corrected_control_audits_passed=not remaining,legacy_formula_correction_applied=bool(old['errors'] and correctable))
 else:row.update(unresolved_audits=row['failed_audits'],corrected_control_audits_passed=row['control_audits_passed'])
 results.append(row)
groups=[]
for group in base['groups']:
 rows=[r for r in results if r['group']==group['group']];assert len(rows)==5
 groups.append(dict(group=group['group'],push_passed=sum(r['original_task_and_pose_passed'] for r in rows if not r['wait']),push_total=4,wait_passed=all(r['original_task_and_pose_passed'] for r in rows if r['wait']),all_task_and_control_passed=all(r['original_task_and_pose_passed'] and r['corrected_control_audits_passed'] for r in rows),training_admitted=False))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_complete_separate_confirmation_audit_correction',scope=__doc__,conditions=10,push_passed=base['push_passed'],push_total=8,wait_passed=base['wait_passed'],wait_total=2,baseline_push_passed=base['baseline_push_passed'],groups=groups,rows=results,original_audit_invocations=base['audit_invocations'],original_failures_retained=True,supplemental_audits=8,unresolved_audits=[dict(episode=r['episode'],audits=r['unresolved_audits']) for r in results if r['unresolved_audits']],source_sha256=sources,closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False)
dest=R/'RESULT_WITH_SUPPLEMENT.json';assert not dest.exists()
if '--apply' in sys.argv:
 with dest.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','rows','scope']},indent=2))
