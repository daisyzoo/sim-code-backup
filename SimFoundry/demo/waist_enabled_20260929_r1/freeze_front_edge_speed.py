"""Freeze source-bound edge candidate after CLI, actual wiring and independent audit checks."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;s=w/'staged_front_edge_speed';probe=w/'staged_front_edge_speed_probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert not (s/'MANIFEST.json').exists();prep=json.loads((s/'PREPARATION.json').read_text());parent=Path(prep['parent_stage']);assert sha(parent/'MANIFEST.json')==prep['parent_manifest_sha256']
for n,h in prep['source_sha256'].items():assert sha(s/n)==h
for n in prep['unchanged_parent_helpers']:assert sha(s/n)==sha(parent/n)
checks={'CHECK.json':'check_front_edge_speed_probe.py','EDGE_SPEED_REPLAY_CHECK.json':'check_front_edge_speed_replay.py','EDGE_SPEED_AUDITOR_CHECK.json':'check_front_edge_speed_auditor.py','AUDITOR_ENTRY_CHECK.json':'check_front_edge_auditor_entry.py','FRONT_COLLECTOR_WIRING_CHECK.json':'check_front_edge_collector_wiring.py','REAR_EXCLUSION_CHECK.json':'check_front_edge_rear_exclusion.py','MEASURED_BOUNDS_WIRING_CHECK.json':'check_front_edge_bounds_wiring.py','BOUNDARY_WIRING_CHECK.json':'check_front_edge_boundary_wiring.py'}
for n in ['CHECK.json','EDGE_SPEED_REPLAY_CHECK.json','EDGE_SPEED_AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json']:
 assert not (s/n).exists();(s/n).write_bytes((probe/n).read_bytes())
for n,checker in checks.items():
 d=json.loads((s/n).read_text());assert d['passed'] and d['checker_sha256']==sha(w/checker)
 for key in ['source_sha256','candidate_source_sha256']:
  hashes=d.get(key,{})
  if isinstance(hashes,dict):
   for f,h in hashes.items():
    if f in prep['source_sha256']:assert sha(s/f)==h
front=json.loads((s/'FRONT_COLLECTOR_WIRING_CHECK.json').read_text())
for key,file in [('collector_sha256','collect_paired_sorting.py'),('wrapper_sha256','front_cop_route.py'),('helper_sha256','contact_slip_following.py'),('edge_helper_sha256','front_edge_speed.py')]:assert front[key]==sha(s/file)
for n in ['EDGE_SPEED_AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json']:assert json.loads((s/n).read_text())['auditor_sha256']==sha(w/'audit_front_edge_speed_live.py')
cli=json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text());assert cli['default_off_and_enabled_cli'] and cli['actual_snapshot_writer_files']==56 and len(cli['negative_cli_rejected'])==42 and cli['source_sha256']==prep['source_sha256']
checks['PRELAUNCH_AND_SOURCE_CHECK.json']='check_front_edge_speed_prelaunch.py'
out=dict(source_sha256=prep['source_sha256'],checks_sha256={n:sha(s/n) for n in checks},checker_sha256={c:sha(w/c) for c in checks.values()},parent_manifest_sha256=prep['parent_manifest_sha256'],unchanged_parent_helpers=prep['unchanged_parent_helpers'],auditor_sha256=sha(w/'audit_front_edge_speed_live.py'),rear_auditor_sha256=sha(w/'audit_rear_cop_core_slice_live.py'),collector_wired=True,physical_started=False,training_ready=False,scope='Default-off front edge speed: unchanged nominal2mm, linearly1..2mm within10mm forward core edge. ActualUSD core, prior loadedCOP only. RealCLI42negatives56archive;18selection/218loadedupdates/4inactivehooks;10rearselection34priorcontacts;28domain16negative;3boundary18negative;4796defaultexact1971syntheticoverrides;68corruptionrejects;19actualauditorCLIcases. All offline. Full current parent8+2closure required before run.')
(s/'MANIFEST.json').write_text(json.dumps(out,indent=2));print(sha(s/'MANIFEST.json'))
