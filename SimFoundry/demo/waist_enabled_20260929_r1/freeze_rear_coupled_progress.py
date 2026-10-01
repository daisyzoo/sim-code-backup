"""Freeze checked isolated source and evidence; no physical run is started here."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;s=w/'staged_rear_coupled_progress';p=w/'staged_rear_coupled_progress_probe';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();prep=json.loads((s/'PREPARATION.json').read_text());assert not (s/'MANIFEST.json').exists()
for n,h in prep['source_sha256'].items():assert sha(s/n)==h
for n in ['CHECK.json','LIFECYCLE_CHECK.json','AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json','EXECUTION_REPLAY_CHECK.json']:
 d=json.loads((p/n).read_text());assert d['passed'];(s/n).write_bytes((p/n).read_bytes())
assert json.loads((s/'AUDITOR_CHECK.json').read_text())['auditor_sha256']==sha(w/'audit_rear_coupled_progress_live.py')
assert json.loads((s/'AUDITOR_ENTRY_CHECK.json').read_text())['auditor_sha256']==sha(w/'audit_rear_coupled_progress_live.py')
assert json.loads((s/'EXECUTION_REPLAY_CHECK.json').read_text())['auditor_sha256']==sha(w/'audit_rear_coupled_execution_live.py')
assert json.loads((s/'CHECK.json').read_text())['source_sha256']==sha(s/'rear_coupled_progress.py')
for n in ['COLLECTOR_WIRING_CHECK.json','EXECUTION_TRACE_WIRING_CHECK.json','FRONT_COLLECTOR_WIRING_CHECK.json','MEASURED_BOUNDS_WIRING_CHECK.json','BOUNDARY_WIRING_CHECK.json']:assert json.loads((s/n).read_text())['passed']
pre=json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text());assert pre['default_off_and_enabled_cli'] and pre['actual_snapshot_writer_files']==57 and len(pre['negative_cli_rejected'])==49
for n,h in pre['source_sha256'].items():assert sha(s/n)==h
checks=['CHECK.json','LIFECYCLE_CHECK.json','AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json','EXECUTION_REPLAY_CHECK.json','COLLECTOR_WIRING_CHECK.json','EXECUTION_TRACE_WIRING_CHECK.json','FRONT_COLLECTOR_WIRING_CHECK.json','MEASURED_BOUNDS_WIRING_CHECK.json','BOUNDARY_WIRING_CHECK.json','PRELAUNCH_AND_SOURCE_CHECK.json']
checkers=['check_rear_coupled_progress_probe.py','check_rear_coupled_progress_lifecycle.py','check_rear_coupled_progress_auditor.py','check_rear_progress_auditor_entry.py','check_rear_coupled_execution_replay.py','check_rear_progress_collector_wiring.py','check_rear_progress_execution_trace.py','check_rear_progress_front_exclusion.py','check_rear_progress_bounds_wiring.py','check_rear_progress_boundary_wiring.py','check_rear_coupled_progress_prelaunch.py']
for c,t in zip(checks,checkers):
 d=json.loads((s/c).read_text())
 if 'checker_sha256' in d:assert d['checker_sha256']==sha(w/t),(c,t)
parent=w/'staged_front_edge_speed'
for n in prep['unchanged_parent_helpers']:assert sha(s/n)==sha(parent/n)
out=dict(source_sha256=prep['source_sha256'],checks_sha256={n:sha(s/n) for n in checks},checker_sha256={n:sha(w/n) for n in checkers},parent_manifest_sha256=sha(parent/'MANIFEST.json'),unchanged_parent_helpers=prep['unchanged_parent_helpers'],auditor_sha256=sha(w/'audit_rear_coupled_progress_live.py'),execution_auditor_sha256=sha(w/'audit_rear_coupled_execution_live.py'),front_auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),collector_wired=True,expected_archive_sources=57,physical_started=False,training_ready=False,scope='Rear-only current-COP/core geometry scales forwardY0..1 after original rear-X correction, originalXZ/firstload/mode guards unchanged, infeasible keeps parent. Full rear top_push Jacobian logging for exact archivedIK to raw actions. Default7194;526synthetic altered steps105corruptions;12realCLI;48actual historical sampledIK exact36negatives;49CLI57archives;12selection34rawcontacts;192tracecall;240front exclusion;28domain16negative;3boundary18negative. All offline, no physical success or new data claim. Complete parent8+2closure required before launch.')
(s/'MANIFEST.json').write_text(json.dumps(out,indent=2));print(sha(s/'MANIFEST.json'))
