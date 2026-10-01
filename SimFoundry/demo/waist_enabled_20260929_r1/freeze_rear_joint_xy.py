"""Bind inspected isolated candidate and actual checks; no physical launch."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;s=w/'staged_rear_joint_xy';p=w/'staged_rear_joint_xy_probe';parent=w/'staged_rear_coupled_progress';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert not (s/'MANIFEST.json').exists();old=json.loads((parent/'MANIFEST.json').read_text());source={n:sha(s/n) for n in [*old['source_sha256'],'rear_joint_xy_progress.py']};assert len(source)==14
unchanged=[n for n in old['source_sha256'] if n not in ['collect_paired_sorting.py','rear_cop_route.py']];assert len(unchanged)==11
for n in unchanged:assert source[n]==old['source_sha256'][n]==sha(parent/n)
for n in ['rear_cop_route.py','rear_joint_xy_progress.py']:assert sha(s/n)==sha(p/n)
pairs=[('HELPER_CHECK.json','check_rear_joint_xy_probe.py'),('LIFECYCLE_CHECK.json','check_rear_joint_xy_lifecycle.py'),('AUDITOR_CHECK.json','check_rear_joint_xy_auditor.py'),('AUDITOR_ENTRY_CHECK.json','check_rear_joint_xy_auditor_entry.py')]
for n,checker in pairs:
 d=json.loads((p/n).read_text());assert d['passed'] and d['checker_sha256']==sha(w/checker);(s/n).write_bytes((p/n).read_bytes())
assert json.loads((s/'HELPER_CHECK.json').read_text())['helper_sha256']==source['rear_joint_xy_progress.py']
for n in ['AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json']:assert json.loads((s/n).read_text())['auditor_sha256']==sha(w/'audit_rear_joint_xy_live.py')
pairs += [('COLLECTOR_WIRING_CHECK.json','check_rear_joint_xy_collector_wiring.py'),('EXECUTION_TRACE_WIRING_CHECK.json','check_rear_joint_xy_execution_trace.py'),('FRONT_COLLECTOR_WIRING_CHECK.json','check_rear_joint_xy_front_exclusion.py'),('MEASURED_BOUNDS_WIRING_CHECK.json','check_rear_joint_xy_bounds_wiring.py'),('BOUNDARY_WIRING_CHECK.json','check_rear_joint_xy_boundary_wiring.py'),('PRELAUNCH_AND_SOURCE_CHECK.json','check_rear_joint_xy_prelaunch.py')]
for n,checker in pairs:
 d=json.loads((s/n).read_text())
 if n=='PRELAUNCH_AND_SOURCE_CHECK.json':assert d['default_off_and_enabled_cli'] and d['actual_snapshot_writer_files']==58 and len(d['negative_cli_rejected'])==50
 else:assert d['passed'] and d['checker_sha256']==sha(w/checker)
for n,h in json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text())['source_sha256'].items():assert source[n]==h
historical=parent/'EXECUTION_REPLAY_CHECK.json';d=json.loads(historical.read_text());assert d['passed'] and d['auditor_sha256']==sha(w/'audit_rear_coupled_execution_live.py');(s/historical.name).write_bytes(historical.read_bytes());pairs.append((historical.name,'check_rear_coupled_execution_replay.py'))
actual={}
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 path=w/f'rear_coupled_progress_groups_r1/case_{cid}/layout_{cid}_{task}/REAR_COUPLED_EXECUTION_LIVE_AUDIT.json';d=json.loads(path.read_text());assert d['passed'] and d['complete_push_coverage'] and d['maximum_action_error_rad']==0 and not d['historical_sampled'] and d['auditor_sha256']==sha(w/'audit_rear_coupled_execution_live.py');actual[str(path.relative_to(w))]=sha(path)
prep=dict(source_sha256=source,unchanged_parent_helpers=unchanged,parent_manifest_sha256=sha(parent/'MANIFEST.json'),training_ready=False);(s/'PREPARATION.json').write_text(json.dumps(prep,indent=2))
out=dict(**prep,checks_sha256={n:sha(s/n) for n,_ in pairs},checker_sha256={c:sha(w/c) for _,c in pairs},auditor_sha256=sha(w/'audit_rear_joint_xy_live.py'),execution_auditor_sha256=sha(w/'audit_rear_coupled_execution_live.py'),front_auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),existing_execution_evidence_sha256=actual,collector_wired=True,expected_archive_sources=58,physical_started=False,scope='JointXY reference governor after valid original rearX; retains parentY fallback, firstload and mode guards, Z and original2mm X slew/30mm lead.14sources11unchanged.1153geometry inputs;7194default frames1133one-step changes;7194raw-input and1129propagated-command changes111negative;17realCLI;50CLI/58archives;14selection34contacts;192trace;240front;28domain16negative;3boundary18negative. Unchanged execution auditor prior48sampled/36negative plus parent928full frames exact. No new physical efficacy; parent8+2 closure required.')
(s/'MANIFEST.json').write_text(json.dumps(out,indent=2));print('MANIFEST',sha(s/'MANIFEST.json'))
