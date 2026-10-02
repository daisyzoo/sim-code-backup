"""Separate final comparison correction for the omitted causal-audit dependency.
Keeps original reports/failures. Only the three exact missing-dependency errors
can be resolved by the complete name-only five-report supplementary chain.
No task/pose failure or other control error is waived; no training admission.
"""
from pathlib import Path
import sys,json,hashlib,datetime
W=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):
 p=Path(p);sources[str(p)]=sha(p);return json.loads(p.read_text())
def bound(m):
 for p,h in m.items():assert sha(p)==h,p
if not (R/'RESULT.json').exists() or not (R/'REGION_SUPPLEMENT_STATUS.json').exists():
 print(json.dumps(dict(status='pending_original_result_and_supplement',training_ready=False)));sys.exit(0)
base=read(R/'RESULT.json');status=read(R/'REGION_SUPPLEMENT_STATUS.json')
if status['status']!='complete' or len(status['rows'])!=8:
 print(json.dumps(dict(status='pending_complete_eight_push_supplements',training_ready=False)));sys.exit(0)
p=Path('/proc')/str(status['pid']);assert not p.exists() or (p/'stat').read_text().split()[2]=='Z'
assert base['conditions']==10;bound(base['source_sha256']);protocol=read(R/'REGION_SUPPLEMENT_PROTOCOL.json');bound(protocol['frozen_sha256']);bound(read(R/'PROTOCOL.json')['frozen_files_sha256'])
prep=read(W/'FRONT_INITIAL_REGION_SUPPLEMENT_PREPARATION.json')
for row in prep['adapters']:
 assert sha(row['parent'])==row['parent_sha256'] and sha(row['path'])==row['sha256'];s=Path(row['parent']).read_text()
 for a,b in row['replacements']:s=s.replace(a,b)
 assert s==Path(row['path']).read_text()
assert not (W/'audit_front_initial_stage_region_causal.py').exists(),'Original missing dependency was silently filled'
correctable={'audit_front_initial_stage_region_continuity.py','audit_front_initial_stage_region_bounds.py','audit_front_initial_stage_rear_xy.py'}
names=['FRONT_INITIAL_REGION_SUPPLEMENT_'+s+'.json' for s in ['ACTION_AUDIT','CAUSAL_AUDIT','CONTINUITY_V2_AUDIT','BOUNDS_V2_AUDIT','REAR_XY_V2_AUDIT']];rows=[]
for old in base['rows']:
 row=dict(old);remaining=list(old['failed_audits']);resolved=[]
 if not old['wait']:
  ep=next(R.glob('case_*/'+old['episode']));obs=next(r for r in status['rows'] if r['episode']==ep.name);assert obs['original_execution_sha256']==sha(ep/'AUDIT_EXECUTION.json');execution=read(ep/'AUDIT_EXECUTION.json');assert obs['original_failed_audits']==[r['script'] for r in execution['rows'] if r['returncode']]
  if obs['passed']:
   assert set(obs['reports'])==set(names)
   for name in names:
    report=read(ep/name);assert sha(ep/name)==obs['reports'][name] and report['passed'] is True
    if 'source_sha256' in report:bound({str(ep/k):v for k,v in report['source_sha256'].items()})
    if 'raw_sha256' in report:assert report['raw_sha256']==sha(ep/'raw.npz')
   for script in sorted(correctable.intersection(remaining)):
    entry=next(r for r in execution['rows'] if r['script']==script);log=ep/(script+'.log');assert entry['log_sha256']==sha(log);sources[str(log)]=sha(log)
    expected="can't open file '"+str(W/'audit_front_initial_stage_region_causal.py')+"': [Errno 2] No such file or directory"
    assert expected in log.read_text(),('Unexplained original failure cannot be corrected',script)
    remaining.remove(script);resolved.append(script)
  else:remaining.append('front_initial_region_supplement_chain')
 row.update(original_failed_audits=old['failed_audits'],unresolved_audits=remaining,corrected_control_audits_passed=not remaining,resolved_missing_dependency_audits=resolved,training_admitted=False);rows.append(row)
groups=[]
for g in base['groups']:
 rs=[r for r in rows if r['group']==g['group']];assert len(rs)==5
 groups.append(dict(group=g['group'],push_passed=sum(r['original_task_and_pose_passed'] for r in rs if not r['wait']),push_total=4,wait_passed=all(r['original_task_and_pose_passed'] for r in rs if r['wait']),all_task_and_control_passed=all(r['original_task_and_pose_passed'] and r['corrected_control_audits_passed'] for r in rs),training_admitted=False))
parent=read(W/'front_initial_margin_baseline_r1/RESULT_WITH_SUPPLEMENT.json');bound(parent['source_sha256']);assert base['baseline_push_passed']==parent['push_passed']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_complete_original_dependency_failures_retained_with_separate_supplement',scope=__doc__,conditions=10,push_passed=base['push_passed'],push_total=8,wait_passed=base['wait_passed'],wait_total=2,baseline_push_passed=parent['push_passed'],original_audit_invocations=base['audit_invocations'],region_chain_episodes=8,groups=groups,rows=rows,unresolved_audits=[dict(episode=r['episode'],audits=r['unresolved_audits']) for r in rows if r['unresolved_audits']],original_failures_retained=True,source_sha256=sources,closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False)
dest=R/'RESULT_WITH_REGION_SUPPLEMENT.json';assert not dest.exists()
if '--apply' in sys.argv:
 with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','rows','scope']},indent=2))
