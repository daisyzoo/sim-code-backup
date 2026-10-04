"""Record complete original audit outcome; retain every failure and paired gate."""
from pathlib import Path
import collections,datetime,hashlib,json,os
W=Path(__file__).resolve().parent;R=W/'rear_early_edge_physical_r1'
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=read(R/'AUDIT_STATUS_V2.json');n=read(R/'NUMERIC_VISUAL_SUMMARY.json');closed=read(R/'RESULT.json')
assert a['status']=='complete' and len(a['rows'])==224 and not Path(f"/proc/{a['pid']}").exists()
assert closed['status']=='diagnostic_complete_failures_retained' and closed['audit_invocations']==224
assert (n['push_passed'],n['push_total'],n['wait_passed'],n['wait_total'],n['actual_reviews'])==(5,8,2,2,10)
fail=[r for r in a['rows'] if r['returncode']];assert len(fail)==4
sources={str(p):sha(p) for p in [Path(__file__),R/'AUDIT_STATUS_V2.json',R/'RESULT.json',R/'NUMERIC_VISUAL_SUMMARY.json',R/'COMPLETE_NUMERIC_VISUAL_COMPARISON_PENDING_AUDITS.json']};failures=[]
for row in fail:
 ep=next(R.glob('case_*/'+row['episode']));p=ep/(row['script']+'.log');assert sha(p)==row['log_sha256'];log=p.read_text()
 sources[str(p)]=sha(p);sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');assert sources[str(ep/'raw.npz')]==row['raw_sha256']
 if row['episode']=='layout_840023_push_box_to_bin':assert 'early_edge.candidate_result.reason' in log;reason='step902_early_candidate_reason_mismatch'
 elif 'self_clearance' in row['script']:assert '3.1916309808462814e-06' in log;reason='step655_original_stationarity_exceeds_1e-6'
 else:
  assert 'FileNotFoundError' in log and 'REAR_EARLY_EDGE_R1_V3_STAGE_SELF_CLEARANCE_V2_AUDIT.json' in log
  assert not (ep/'REAR_EARLY_EDGE_R1_V3_STAGE_SELF_CLEARANCE_V2_AUDIT.json').exists()
  reason='dependent_pose_audit_missing_failed_self_clearance_report'
 failures.append(dict(**row,diagnosis=reason))
groups=collections.defaultdict(list)
for row in n['rows']:groups[row['group']].append(row)
paired={key:dict(push_passed=sum(r['original_task_and_pose_passed'] for r in rs if not r['wait']),push_total=sum(not r['wait'] for r in rs),wait_passed=sum(r['original_task_and_pose_passed'] for r in rs if r['wait']),qualified=False) for key,rs in groups.items()}
assert all(g['push_total']==4 and g['push_passed']<4 for g in paired.values())
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='closed_original_audits_failures_retained',audit_invocations=224,audit_failures=failures,root_failure_families=2,fourth_failure_is_dependency_propagation=True,watcher_terminal_verified=True,watcher_pid=a['pid'],push_passed=5,push_total=8,wait_passed=2,wait_total=2,actual_visual_reviews=10,paired_groups=paired,qualified_groups=0,new_training_admissions=0,training_ready=False,model_goal_achieved=False,source_sha256=sources)
p=R/'CLOSED_ORIGINAL_AUDITS_AND_TASK_DECISION_V1.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['audit_failures','source_sha256']},indent=2))
