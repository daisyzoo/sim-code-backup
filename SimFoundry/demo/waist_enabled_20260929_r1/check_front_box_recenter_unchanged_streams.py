"""Read-only regression of original left, rear and wait streams; no new-source admission."""
from pathlib import Path
import sys,json,datetime,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path[:0]=[str(W),str(ROOT)]
from audit_front_box_recenter_stream import verify_files
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();base=W/'front_recontact_headroom_physical_r1';rows=[];sources={str(Path(__file__)):sha(__file__),str(W/'audit_front_box_recenter_stream.py'):sha(W/'audit_front_box_recenter_stream.py')}
for case,name in [(840023,'nudge_mailer_to_bin'),(840023,'push_box_to_bin'),(841010,'wait_no_package')]:
 ep=base/f'case_{case}'/f'layout_{case}_{name}';before=sha(ep/'raw.npz');r=verify_files(ep);assert r['passed'];assert sha(ep/'raw.npz')==before
 rows.append(dict(episode=ep.name,selected=r['selected'],wait=r['wait'],verified_commands=r['verified_commands'],handovers=r['handovers'],original_raw_unchanged=True));print(json.dumps(rows[-1]),flush=True)
 for p in ep.glob('*'):
  if p.name in ['raw.npz','front_recontact_center.json','frontal_bypass.json','coordination.json','expert_control.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','self_clearance.json']:sources[str(p)]=sha(p)
# Original right-front episode has no new recovery declaration; must not silently
# count as a new right-controller stream after enabling that controller.
ep=base/'case_840020/layout_840020_push_box_to_bin'
try:verify_files(ep)
except AssertionError:right_rejected=True
else:raise AssertionError('old right-front stream accepted as new-controller stream')
result=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,old_right_front_rejected=True,source_sha256=sources,native_provenance_not_rewritten=True,new_physics=False,training_ready=False)
with (W/'staged_front_box_recenter_v3/UNCHANGED_STREAMS_CHECK.json').open('x') as f:json.dump(result,f,indent=2)
