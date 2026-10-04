"""Native parent-math entry on isolated full front-box off and wait on fixtures.
Exact historical observations/actions; no candidate closed-loop trajectory.
"""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_parent_math_files_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_native_stream_v1 import inspect as inspect_stream
from audit_front_normal_execution_v1 import inspect as inspect_execution
from front_normal_stage_source_binding_v3 import NORMAL_HELPERS
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,allow_nan=False))
results=[];sources={}
for cid,task,enabled in [(841010,'wait_no_package',True),(840020,'push_box_to_bin',False)]:
 name=f'layout_{cid}_{task}';src=W/f'front_normal_native_files_r1/case_{cid}';case=D/f'case_{cid}';shutil.copytree(src,case,copy_function=shutil.copy2)
 ep=case/name;orig=W/f'front_effective_height_physical_r1/case_{cid}'/name
 for f in ['solved_contact_forces.json','self_clearance.json','expert_control.json','front_loaded_z_priority.json']+([] if task=='wait_no_package' else ['coordination.json']):shutil.copy2(orig/f,ep/f);sources[str(orig/f)]=sha(orig/f)
 with np.load(orig/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy();meta=json.loads(str(z['collect_meta']));intrinsics=z['intrinsics'].copy()
 if enabled:
  with np.load(ep/'raw.npz') as z:template=json.loads(str(z['collect_meta']))
  for k in ['front_normal_nondegradation','front_normal_planning_applied_frames']:meta[k]=template[k]
 prov=read(case/'provenance.json');prov['args']['front_normal_nondegradation']=enabled
 if not enabled:
  prov['source_sha256']={k:v for k,v in prov['source_sha256'].items() if Path(k).name not in set(NORMAL_HELPERS)-{'audit_unloaded_wrist_prior_live.py'}}
  (ep/'front_normal_nondegradation.json').unlink()
 write(case/'provenance.json',prov);np.savez_compressed(ep/'raw.npz',q=q,action=u,task_id=task,intrinsics=intrinsics,collect_meta=json.dumps(meta))
 print(json.dumps(dict(status='stream',episode=name)),flush=True)
 stream=inspect_stream(ep,fixture_only=True);assert stream['passed'];write(ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json',stream)
 print(json.dumps(dict(status='parent_math',episode=name)),flush=True)
 result=inspect_execution(ep,allow_source_fixture=True);assert result['passed'] and result['fixture_only'] is True and result['physical_execution_evidence'] is False
 write(ep/'FRONT_NORMAL_EXECUTION_V1_AUDIT.json',result)
 try:inspect_execution(ep)
 except AssertionError:pass
 else:raise AssertionError('fixture treated as physical evidence')
 rows=dict(episode=name,enabled=enabled,frames=len(q),passed=True,loaded_z_applied=result['loaded_z_applied'],actual_history_preserved=True,fixture_only=True,training_ready=False);results.append(rows)
 for p in [ep/'raw.npz',ep/'FRONT_NORMAL_NATIVE_STREAM_V1_AUDIT.json',ep/'FRONT_NORMAL_EXECUTION_V1_AUDIT.json']:sources[str(p)]=sha(p)
 (D/'STATUS.json').write_text(json.dumps(dict(status='running',results=results),indent=2));print(json.dumps(rows),flush=True)
for p in [Path(__file__),W/'audit_front_normal_execution_v1.py',W/'audit_front_normal_z_execution_v1.py',W/'front_normal_loaded_episode_inputs_v1.py',W/'front_normal_parent_coordinate_v1.py',W/'audit_front_normal_recovery_stream_v1.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,results=results,source_sha256=sources,training_ready=False,physics_started=False)
write(D/'RESULT.json',out);write(D/'STATUS.json',dict(status='complete',passed=True));print('PASS',flush=True)
