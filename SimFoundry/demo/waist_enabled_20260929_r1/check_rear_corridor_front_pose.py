"""Whole native front-route regression with unchanged history and empty rear log.
No new physics/provenance admission; actual front q/actions/forces remain untouched.
"""
from pathlib import Path
import json,sys,os,tempfile,hashlib,datetime
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_corridor_stage_pose_live import verify_files
from audit_joint_edge_stage_pose_live_v2 import verify_files as original
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dest=W/'REAR_CORRIDOR_FRONT_POSE_CHECK.json';assert not dest.exists();tmp=Path(tempfile.mkdtemp(prefix='rear_front_history_NO_PHYSICS_'));rows=[];sources={}
def save(status,**extra):
 p=dest.with_suffix('.tmp');p.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_root=str(tmp),rows=rows,source_sha256=sources,training_ready=False,**extra),indent=2));p.replace(dest)
try:
 save('running')
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  src=W/'fresh_closed_peak_trials_r1'/'case_840005'/('layout_840005_'+task);ep=tmp/src.name;ep.mkdir()
  fr=json.loads((src/'frontal_bypass.json').read_text());assert not fr['plan'].get('rear_joint_xy_progress',{}).get('enabled')
  for p in src.iterdir():
   if p.is_file():os.link(p,ep/p.name)
  assert not (ep/'rear_corridor_recovery.json').exists();(ep/'rear_corridor_recovery.json').write_text(json.dumps(dict(rows=[],handovers=[],executed_action_count=1200,pending_recontact=False,training_ready=False)))
  baseline=original(ep,S);actual=verify_files(ep,S);assert {k:v for k,v in actual.items() if k not in ['recovery_boundary','required_transport_steps']}==baseline
  assert actual['passed'] and actual['frames']==1200 and actual['recovery_boundary']['overrides']==0
  for p in src.iterdir():
   if p.is_file() and p.suffix in ['.npz','.json']:sources[str(p)]=sha(p)
  rows.append(dict(task=task,episode=str(src),frames=1200,original_full_pose_equal=True,new_recovery_not_selected=True));save('running');print(task,flush=True)
 for p in [Path(__file__),W/'audit_rear_corridor_stage_pose_live.py',W/'rear_corridor_audit_inputs.py',W/'audit_rear_corridor_transport_events_v2.py']:sources[str(p)]=sha(p)
 save('complete',passed=True)
except BaseException as e:save('check_failed',error=repr(e));raise
