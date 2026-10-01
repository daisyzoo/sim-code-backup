"""Run unchanged native-file mathematics against original four SYNTHETIC fixtures.
These are padded/remapped bookkeeping streams, not physical trajectories. This
checks the new module paths and stage geometry only; precision source binding
has separate metadata fixtures. No precision physical or training validation.
"""
from pathlib import Path
import json,sys,hashlib,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)];stage=w/'staged_precise_parent_seed';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
from audit_parent_seed_pose_live import verify_files
fixture_report=w/'staged_recontact_interior/LIVE_FILES_CHECK.json';original=json.loads(fixture_report.read_text());assert original['passed'];rows=[];sources={str(fixture_report):sha(fixture_report)}
for fixture in original['fixtures']:
 ep=Path(fixture['fixture']);assert ep.name=='SYNTHETIC_NOT_PHYSICS' and ep.exists();out=verify_files(ep,stage);assert out['passed'] and out['command_events']==fixture['events'];rows.append(dict(fixture=str(ep),frames=out['frames'],command_events=out['command_events'],handovers=out['handovers'],passed=True));print(rows[-1],flush=True)
 for p in ep.iterdir():
  if p.is_file():sources[str(p)]=sha(p)
assert len(rows)==4 and sum(x['command_events'] for x in rows)==258
for p in [Path(__file__),w/'audit_parent_seed_pose_live.py',w/'audit_parent_seed_source_contract.py',w/'audit_recontact_interior_events.py',stage/'AUDIT_VERSION_CHECK.json',stage/'INTEGRATION_CHECK.json']:sources[str(p)]=sha(p)
(stage/'NATIVE_READER_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,source_sha256=sources,physical_validation=False,training_ready=False),indent=2));print('PASS4 synthetic fixtures258events')
