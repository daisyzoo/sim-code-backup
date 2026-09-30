"""Reconcile independently corrected audit reports only after watcher terminal."""
from pathlib import Path
import json,hashlib,sys,datetime
root=Path(__file__).resolve().parent;run=Path(sys.argv[1]).resolve();p=run/'CONTROL_EVIDENCE_EXECUTION.json';d=json.loads(p.read_text());assert d['stage']!='running','Never race live writer'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
corrections=json.loads((run/'CONTROL_EVIDENCE_CORRECTIONS.json').read_text())['rows'];keys={(r['episode'],r['script']):r for r in d['rows']};assert len(keys)==len(d['rows'])
for c in corrections:
 r=keys[c['episode'],c['script']];assert r['returncode']==c['original_returncode'];ep=run/('case_'+c['episode'].split('_')[1])/c['episode']
 assert sha(ep/'raw.npz')==c['raw_sha256']==r['raw_sha256'];assert sha(root/c['script'])==c['auditor_sha256']
 assert c['script']=='audit_contact_normal_live.py';report=ep/'CONTACT_NORMAL_LIVE_AUDIT.json';assert sha(report)==c['report_sha256'];a=json.loads(report.read_text());assert a['summary']['recording_and_mapping_passed'] and not a['errors'] and a['auditor_sha256']==c['auditor_sha256']
 r.update(original_returncode=r['returncode'],returncode=c['corrected_returncode'],correction_report_sha256=c['report_sha256'],correction_auditor_sha256=c['auditor_sha256'],correction_reason=c['reason'])
expected=set()
for ep in run.glob('case_*/layout_*'):
 if not (ep/'quality.json').exists():continue
 scripts=['audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_terminal_hold_inputs.py','audit_contact_stability_control.py']
 if (ep/'contact_center_calibration.json').exists():scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
 expected|={(ep.name,s) for s in scripts}
protocol=json.loads((run/'PROTOCOL.json').read_text());assert len({e for e,s in expected})==len(protocol['layout_ids'])*2 and set(keys)==expected
assert all(r['returncode']==0 for r in d['rows'])
backup=run/'CONTROL_EVIDENCE_EXECUTION.before_reconciliation.json';assert not backup.exists();backup.write_bytes(p.read_bytes());d.update(stage='complete',reconciled_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),corrections_sha256=sha(run/'CONTROL_EVIDENCE_CORRECTIONS.json'));p.write_text(json.dumps(d,indent=2));print('Reconciled with original failure retained',len(corrections))
