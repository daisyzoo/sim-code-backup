"""Freeze verified isolated front-drive candidate without changing historical artifacts."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;s=w/'staged_front_drive_increment';probe=w/'staged_front_drive_increment_probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (s/'MANIFEST.json').exists()
prep=json.loads((s/'PREPARATION.json').read_text());parent=Path(prep['parent_stage']);assert sha(parent/'MANIFEST.json')==prep['parent_manifest_sha256']
for n,h in prep['source_sha256'].items():assert sha(s/n)==h
for n in prep['unchanged_parent_helpers']:assert sha(s/n)==sha(parent/n)
for n in ['DRIVE_INCREMENT_REPLAY_CHECK.json','DRIVE_INCREMENT_AUDITOR_CHECK.json']:
 assert not (s/n).exists();(s/n).write_bytes((probe/n).read_bytes())
checks=['DRIVE_INCREMENT_REPLAY_CHECK.json','DRIVE_INCREMENT_AUDITOR_CHECK.json','PRELAUNCH_AND_SOURCE_CHECK.json','FRONT_COLLECTOR_WIRING_CHECK.json','REAR_EXCLUSION_CHECK.json','MEASURED_BOUNDS_WIRING_CHECK.json','BOUNDARY_WIRING_CHECK.json','AUDITOR_ENTRY_CHECK.json']
for n in checks:
 d=json.loads((s/n).read_text())
 if n!='PRELAUNCH_AND_SOURCE_CHECK.json':assert d['passed']
 for key in ['source_sha256','candidate_source_sha256']:
  for f,h in d.get(key,{}).items():
   if f in prep['source_sha256']:assert sha(s/f)==h
front=json.loads((s/'FRONT_COLLECTOR_WIRING_CHECK.json').read_text())
for k,n in [('collector_sha256','collect_paired_sorting.py'),('wrapper_sha256','front_cop_route.py'),('helper_sha256','contact_slip_following.py')]:assert front[k]==sha(s/n)
for n in ['DRIVE_INCREMENT_AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json']:assert json.loads((s/n).read_text())['auditor_sha256']==sha(w/'audit_front_drive_increment_live.py')
cli=json.loads((s/'PRELAUNCH_AND_SOURCE_CHECK.json').read_text());assert cli['source_sha256']==prep['source_sha256']
manifest=dict(source_sha256=prep['source_sha256'],checks_sha256={n:sha(s/n) for n in checks},parent_manifest_sha256=prep['parent_manifest_sha256'],unchanged_parent_helpers=prep['unchanged_parent_helpers'],auditor_sha256=sha(w/'audit_front_drive_increment_live.py'),rear_auditor_sha256=sha(w/'audit_rear_cop_core_slice_live.py'),collector_wired=True,physical_started=False,training_ready=False,scope='Only front nominal drive1->2mm; default1mm exact on recorded inputs. Parent rear-core-slice logic unchanged; moving-slice FF absent. RealCLI37negatives55archive;24frontwiring;10rearselection34priorpacket;28domain16negative;3boundary18negative;10recordedstreams11990default5533shadow;120corruptions;11actualauditorCLIcases. All evidence is offline, not physical success.')
(s/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(sha(s/'MANIFEST.json'))
