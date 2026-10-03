"""Separate closure of representation/dependency supplements; never rewrite failures.
Requires the original 204-invocation result first. All original task failures,
group rejections, reports, images and failed logs remain authoritative.
"""
from pathlib import Path
import json,hashlib,datetime,sys
W=Path(__file__).resolve().parent;R=W/'front_z_priority_physical_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
MAPPING={
 'audit_front_z_priority_execution.py':('FRONT_Z_PRIORITY_ROTATION_REPRESENTATION_V2_SUPPLEMENT.json','audit_front_z_priority_rotation_representation_v2.py'),
 'audit_front_z_priority_stage_self_clearance.py':('FRONT_Z_PRIORITY_SELF_CLEARANCE_ROTATION_SUPPLEMENT.json','audit_front_z_priority_self_clearance_rotation_supplement.py'),
 'audit_front_z_priority_stage_pose_loaded_execution.py':('FRONT_Z_PRIORITY_POSE_LOADED_ROTATION_SUPPLEMENT.json','audit_front_z_priority_pose_loaded_rotation_supplement.py')}

def verify_supplements():
 sources={};rows=[]
 def bind(p,h=None):
  p=Path(p);actual=sha(p)
  if h is not None:assert actual==h,p
  sources[str(p)]=actual
 progress=json.loads((R/'ROTATION_SUPPLEMENT_PROGRESS.json').read_text());bind(R/'ROTATION_SUPPLEMENT_PROGRESS.json');known={r['report']:r['sha256'] for r in progress['supplements']}
 for case,task,applied in [(840023,'nudge_mailer_to_bin',7),(840020,'push_box_to_bin',321)]:
  ep=R/f'case_{case}'/f'layout_{case}_{task}'
  for original,(report,auditor) in MAPPING.items():
   p=ep/report;bind(p,known[str(p)]);d=json.loads(p.read_text());assert d['passed'] is True and d['training_ready'] is False;bind(W/auditor)
   for name,h in d.get('source_sha256',{}).items():bind(Path(name) if Path(name).is_absolute() else ep/name,h)
   for name,h in d.get('priority_execution_source_sha256',{}).items():bind(name,h)
   if original=='audit_front_z_priority_execution.py':assert d['frames']==1200 and d['applied']==applied and d['fixture_only'] is False and len(d['records'])==1200
   elif original=='audit_front_z_priority_stage_self_clearance.py':
    assert d['executed_frames']==1200 and d['controller_frames']==1199 and d['episode_clearance_passed'] and d['failure'] is None and d['priority_execution_applied']==applied
    assert d['auditor_sha256']==sha(W/auditor)
   else:
    assert d['selected'] is False and d['parent_full_push_replay_frames']==d['refinement_frames']==0
    bind(ep/'FRONT_Z_PRIORITY_STAGE_POSE_LIVE_V2_AUDIT.json',d['pose_audit_sha256']);bind(W/'audit_front_z_priority_stage_pose_live.py',d['pose_auditor_sha256']);assert d['auditor_sha256']==sha(W/auditor)
   bind(ep/'raw.npz');rows.append(dict(episode=ep.name,original_script=original,supplement=report,supplement_sha256=sha(p),passed=True))
 for name in ['ROTATION_REPRESENTATION_CHECK.json']:bind(R/name);assert json.loads((R/name).read_text())['passed'] is True
 bind(Path(__file__))
 return rows,sources

def inspect():
 rows,sources=verify_supplements();original=R/'RESULT.json';assert original.exists(),'Original full closure still pending'
 d=json.loads(original.read_text());a=json.loads((R/'AUDIT_STATUS.json').read_text())
 assert d['status']=='diagnostic_complete_failures_retained' and d['conditions']==10 and d['audit_invocations']==204 and d['training_ready'] is False
 assert a['status']=='complete' and len(a['rows'])==204 and len(a['completed_episodes'])==10
 expected={(r['episode'],r['original_script']) for r in rows};failed={(r['episode'],r['script']) for r in d['failed_audit_invocations']};assert failed==expected and len(d['failed_audit_invocations'])==6
 for name,h in d['source_sha256'].items():assert sha(name)==h,name
 protocol=json.loads((R/'PROTOCOL.json').read_text())
 for name,h in protocol['frozen_files_sha256'].items():assert sha(name)==h,name
 for p in [original,R/'AUDIT_STATUS.json',R/'PROTOCOL.json']:sources[str(p)]=sha(p)
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_complete_original_failures_retained_with_rotation_supplements',conditions=10,original_audit_invocations=204,original_passed_invocations=198,original_failed_invocations=d['failed_audit_invocations'],supplements=rows,unresolved_audits=[],push_passed=d['push_passed'],push_total=d['push_total'],wait_passed=d['wait_passed'],wait_total=d['wait_total'],groups=d['groups'],source_sha256=sources,scope=__doc__,training_ready=False,model_goal_achieved=False)

if __name__=='__main__':
 if '--check-supplements-only' in sys.argv:
  rows,sources=verify_supplements();print(json.dumps(dict(supplements_verified=len(rows),bound_sources=len(sources),original_closure_pending=not (R/'RESULT.json').exists(),training_ready=False)))
 else:
  result=inspect()
  if '--apply' in sys.argv:
   with (R/'RESULT_WITH_ROTATION_SUPPLEMENT.json').open('x') as f:json.dump(result,f,indent=2)
  print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','original_failed_invocations','scope']},indent=2))
