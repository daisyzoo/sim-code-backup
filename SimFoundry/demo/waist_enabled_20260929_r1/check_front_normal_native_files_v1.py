"""Marked file fixtures: two unchanged branches and reject stale candidate history.
Original observations and contacts; not collected candidate data or admission.
"""
from pathlib import Path
import copy,datetime,gzip,hashlib,json,shutil,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_native_files_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_native_stream_v1 import inspect
from front_normal_command_ledger_v1 import load_transport_ledger
from front_normal_stage_source_binding_v3 import NORMAL_HELPERS
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,allow_nan=False))
rows=[];sources={}
for cid,task,enabled in [(840022,'push_box_to_bin',False),(841010,'wait_no_package',True),(840020,'push_box_to_bin',True)]:
 name=f'layout_{cid}_{task}';src=W/f'front_normal_observation_binding_checks_r2/case_{cid}';case=D/f'case_{cid}'
 shutil.copytree(src,case,copy_function=shutil.copy2,ignore=lambda directory,names:[n for n in names if n.startswith('layout_') and n!=name])
 ep=case/name;orig=W/f'front_effective_height_physical_r1/case_{cid}'/name;wait=task=='wait_no_package'
 for f in ['trace.npz','parcel_orientation.npz','front_initial_center.json','front_recontact_center.json','front_loaded_z_priority.json','joint_transport_clearance.json']+([] if wait else ['frontal_bypass.json','coordination.json']):
  shutil.copy2(orig/f,ep/f);sources[str(orig/f)]=sha(orig/f)
 with np.load(orig/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy();meta=json.loads(str(z['collect_meta']))
 prov=read(case/'provenance.json');prov['args']['front_normal_nondegradation']=enabled
 if enabled:
  f=W/'front_normal_command_records_r1'/(name+'.json.gz')
  with gzip.open(f,'rt') as z:nr=json.load(z)['rows']
  saved=read(ep/'raw.npz') if False else None
  with np.load(ep/'raw.npz') as z:template=json.loads(str(z['collect_meta']))
  meta['front_normal_nondegradation']=template['front_normal_nondegradation'];meta['front_normal_planning_applied_frames']=sum(r['applied'] for r in nr)
  u[:,12:23]=np.asarray([r['output_command'] for r in nr]);write(ep/'front_normal_nondegradation.json',dict(rows=nr,training_ready=False))
  if not wait:
   coord=read(ep/'coordination.json')
   for c in coord:
    r=nr[c['step']];c['front_normal_nondegradation']=r
    if r['applied']:c['normal_planning_unexecuted_parent_waist_target_rad']=c['waist_target_rad'];c['waist_target_rad']=float(r['output_command'][0])
   write(ep/'coordination.json',coord)
  sources[str(f)]=sha(f)
 else:
  prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if Path(k).name not in set(NORMAL_HELPERS)-{'audit_unloaded_wrist_prior_live.py'}}
  (ep/'front_normal_nondegradation.json').unlink()
 write(case/'provenance.json',prov);np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,collect_meta=json.dumps(meta))
 write(ep/'quality.json',dict(passed=False,training_ready=False,reason='diagnostic_file_fixture_not_physical'))
 try:inspect(ep)
 except AssertionError as e:assert str(e)=='Fixture must never pass physical entry'
 else:raise AssertionError('Fixture accepted as physical')
 if cid==840020:
  # The complete source consumer already requires actual prior emitted actions.
  try:inspect(ep,fixture_only=True)
  except AssertionError:
   tr=read(ep/'joint_transport_clearance.json')['rows'];bad=[t for t in range(1,len(q)) if not np.array_equal(tr[t]['collector_context']['previous_command'],u[t-1,12:23])];assert bad and bad[0]==529
   rows.append(dict(episode=name,enabled=True,stale_original_history_rejected=True,first_stale_step=529,physical_entry_rejected=True,training_ready=False))
  else:raise AssertionError('Candidate historical frames masqueraded as continuous trajectory')
 else:
  result=inspect(ep,fixture_only=True);assert result['passed'] and result['physical_candidate_verified'] is False
  write(ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json',result)
  a,proof=load_transport_ledger(ep,allow_source_fixture=True);assert not a.flags.writeable and len(a)==len(q) and proof['passed']
  try:load_transport_ledger(ep)
  except AssertionError:pass
  else:raise AssertionError('Fixture ledger accepted without explicit flag')
  rows.append(dict(episode=name,enabled=enabled,frames=len(q),native_file_passed=True,ledger_passed=True,physical_entry_rejected=True,training_ready=False))
 for f in ['raw.npz','quality.json','joint_transport_clearance.json']:sources[str(ep/f)]=sha(ep/f)
 print(json.dumps(rows[-1]),flush=True)
for p in [Path(__file__),W/'audit_front_normal_native_stream_v1.py',W/'front_normal_command_ledger_v1.py',W/'front_normal_stage_source_binding_v3.py',W/'audit_front_normal_command_stream_v1.py']:sources[str(p)]=sha(p)
write(D/'RESULT.json',dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,rows=rows,source_sha256=sources,physics_started=False,training_ready=False));print('PASS',flush=True)
