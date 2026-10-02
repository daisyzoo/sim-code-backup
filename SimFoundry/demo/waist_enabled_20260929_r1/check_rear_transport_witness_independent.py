"""Independent scene/path verification of all45 planned and45 measured witnesses.
Uses fixed historical observation contexts and saved candidate witnesses only.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime,os
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from audit_rear_transport_witness import EventAudit,verify_witness
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();audit=EventAudit(ROOT,S);source=W/'REAR_TRANSPORT_LIFECYCLE_CHECK.json';history=json.loads(source.read_text());assert history['status']=='complete';dest=W/'REAR_TRANSPORT_WITNESS_INDEPENDENT_CHECK.json';assert not dest.exists();rows=[];negative=[];cache={};sources={};frozen={str(p):sha(p) for p in [Path(__file__),source,W/'audit_rear_transport_witness.py',W/'audit_recontact_pose_events.py',W/'audit_unloaded_wrist_prior_live.py',W/'audit_unloaded_wrist_task_optimality.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',S/'elbow_torso_hulls.json']}
def save(status,**extra):
 tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,pid=os.getpid(),updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,negative_checks=negative,source_sha256=sources,frozen_sha256=frozen,training_ready=False,**extra),indent=2));tmp.replace(dest)
try:
 save('running')
 for item in history['rows']:
  measured=item['case']=='actual_measured_handover';rec=item['measured_witness'] if measured else item['planning_witness']
  if rec is None:assert not measured and item['enabled_kind']=='stop';continue
  path=W/item['episode']/'recontact_pose.json';sources[str(path)]=sha(path)
  if str(path) not in cache:cache[str(path)]={x['step']:x for x in json.loads(path.read_text())['rows']}
  event=cache[str(path)][item['step']];ctx=event['context'];endpoint=ctx['current'] if measured else event['planning']['endpoint'];scene=ctx['scene'];result=verify_witness(audit,rec,endpoint=endpoint,scene=scene);rows.append(dict(episode=item['episode'],step=item['step'],case=item['case'],**result))
  if ('measured' if measured else 'planned') not in negative:
   changes=[('changed_endpoint',lambda r:r['endpoint'].__setitem__(0,r['endpoint'][0]+.001)),('empty_path',lambda r:r.update(path=[])),('tampered_delta',lambda r:r['reference_delta_xyz_m'].__setitem__(1,.001)),('false_geometry',lambda r:r['path'][0]['scene_check'].update(accepted=False)),('wrong_previous',lambda r:r['final_guard']['previous'].__setitem__(0,r['final_guard']['previous'][0]+.001))]
   for label,mutate in changes:
    bad=copy.deepcopy(rec);mutate(bad)
    try:verify_witness(audit,bad,endpoint=endpoint,scene=scene)
    except (AssertionError,ValueError):negative.append(label+('_measured' if measured else '_planned'))
    else:raise AssertionError('Corrupt witness accepted '+label)
   negative.append('measured' if measured else 'planned')
  if len(rows)%15==0:save('running');print('witnesses',len(rows),flush=True)
 assert len(rows)==90 and sum(r['case']=='actual_measured_handover' for r in rows)==45
 for p,h in {**sources,**frozen}.items():assert sha(p)==h,p
 save('complete',passed=True,planned_witnesses=45,measured_witnesses=45,path_points=sum(r['sampled_path_points'] for r in rows))
except BaseException as e:save('check_failed',error=repr(e));raise
