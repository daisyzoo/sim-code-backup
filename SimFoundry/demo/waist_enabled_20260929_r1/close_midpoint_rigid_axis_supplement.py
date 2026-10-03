"""Separate closure of exact near-axis supplement after original full204 closure.
Never erase original failure, alter original task scores, or admit rejected groups.
"""
from pathlib import Path
import json,hashlib,sys
W=Path(__file__).resolve().parent;R=W/'front_corridor_midpoint_physical_r1'
EP='layout_840023_nudge_mailer_to_bin';SCRIPT='audit_front_corridor_midpoint_stage_task_optimality.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_supplement():
 sources={}
 def bind(p,h=None):
  p=Path(p);actual=sha(p)
  if h is not None:assert actual==h,p
  sources[str(p)]=actual
 ep=R/'case_840023'/EP;p=ep/'MIDPOINT_RIGID_AXIS_TASK_OPTIMALITY_SUPPLEMENT.json';d=json.loads(p.read_text());bind(p)
 assert d['passed'] and not d['training_ready'] and not d['physical_task_passed']
 assert d['frames']==1199 and d['overrides']==705 and len(d['records'])==1199 and d['errors']==[]
 assert d['source_contract_and_full_pose_replay_executed'] and d['original_failures_retained'] and d['changed_certificate_steps']==d['original_failed_steps']==[1039]
 for path,h in d['supplement_source_sha256'].items():bind(path,h)
 for path,h in d['source_sha256'].items():bind(ep/path,h)
 bind(W/'audit_midpoint_rigid_axis_supplement.py',d['supplement_auditor_sha256']);bind(W/'support_vertex_stationarity_rigid_segment_v2.py',d['vertex_certificate_source_sha256'])
 bind(ep/'FRONT_CORRIDOR_MIDPOINT_STAGE_POSE_LIVE_V2_AUDIT.json',d['pose_audit_sha256']);bind(W/'audit_front_corridor_midpoint_stage_pose_live.py',d['pose_auditor_sha256'])
 orig=ep/'FRONT_CORRIDOR_MIDPOINT_STAGE_TASK_OPTIMALITY_V2_AUDIT.json';bind(orig,d['original_failed_report_sha256']);old=json.loads(orig.read_text());assert not old['passed'] and [x['step'] for x in old['errors']]==[1039]
 assert old['errors'][0]['vertex_certificate']['reason']=='ambiguous_active_axis'
 checks=R/'RIGID_AXIS_CERTIFICATE_CHECK.json';check=json.loads(checks.read_text());bind(checks);assert check['passed'] and check['historical_rows']==1319 and len(check['negative_checks'])==9
 for path,h in check['source_sha256'].items():bind(path,h)
 bind(Path(__file__))
 return dict(episode=EP,original_script=SCRIPT,supplement=str(p),supplement_sha256=sha(p),passed=True),sources

def inspect_closed():
 supplement,sources=verify_supplement();p=R/'RESULT.json';d=json.loads(p.read_text());a=json.loads((R/'AUDIT_STATUS.json').read_text())
 assert d['status']=='diagnostic_complete_failures_retained' and d['conditions']==10 and d['audit_invocations']==204
 assert a['status']=='complete' and len(a['rows'])==204 and len(a['completed_episodes'])==10
 assert not d['training_ready'] and not d['model_goal_achieved']
 expected={(EP,SCRIPT)};failed=d['failed_audit_invocations'];assert len(failed)==1 and {(x['episode'],x['script']) for x in failed}==expected
 actual_failed=[x for x in a['rows'] if x['returncode']!=0 or not x['report_passed']];assert len(actual_failed)==1 and {(x['episode'],x['script']) for x in actual_failed}==expected
 for path,h in d['source_sha256'].items():assert sha(path)==h,path;sources[path]=h
 protocol=json.loads((R/'PROTOCOL.json').read_text())
 for path,h in protocol['frozen_files_sha256'].items():assert sha(path)==h,path
 for name in ['RESULT.json','AUDIT_STATUS.json','PROTOCOL.json','NUMERIC_VISUAL_SUMMARY.json']:sources[str(R/name)]=sha(R/name)
 return dict(status='diagnostic_complete_original_failure_retained_with_rigid_axis_supplement',conditions=10,original_audit_invocations=204,original_passed_invocations=203,original_failed_invocations=failed,supplements=[supplement],unresolved_audits=[],push_passed=d['push_passed'],push_total=d['push_total'],wait_passed=d['wait_passed'],wait_total=d['wait_total'],groups=d['groups'],source_sha256=sources,scope=__doc__,training_ready=False,model_goal_achieved=False)

def verify_saved_closed():
 p=R/'RESULT_WITH_RIGID_AXIS_SUPPLEMENT.json';saved=json.loads(p.read_text());current=inspect_closed();assert saved==current;return saved
if __name__=='__main__':
 if '--check-supplement-only' in sys.argv:
  row,sources=verify_supplement();print(json.dumps(dict(supplements_verified=1,bound_sources=len(sources),original_closure_pending=not (R/'RESULT.json').exists(),training_ready=False)))
 else:
  d=inspect_closed()
  if '--apply' in sys.argv:
   with (R/'RESULT_WITH_RIGID_AXIS_SUPPLEMENT.json').open('x') as f:json.dump(d,f,indent=2)
  print(json.dumps({k:v for k,v in d.items() if k not in ['source_sha256','original_failed_invocations','scope']},indent=2))
