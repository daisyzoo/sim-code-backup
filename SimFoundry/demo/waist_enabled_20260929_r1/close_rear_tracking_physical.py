"""Close fixed ten-condition rear-corridor diagnostic after all evidence exists.
Short episodes remain failed in the original denominator; their incomplete
reviews never substitute for original full-horizon audits. No training admission.
"""
from pathlib import Path
import json,hashlib,datetime,sys
W=Path(__file__).resolve().parent
from rear_tracking_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path(sys.argv[1]).resolve();apply='--apply' in sys.argv;dest=R/'RESULT.json';assert not dest.exists();sources={}
def read(p):
 p=Path(p);sources[str(p)]=sha(p);return json.loads(p.read_text())
def bound(m):
 for p,h in m.items():assert sha(p)==h,p
protocol=read(R/'PROTOCOL.json');status=read(R/'STATUS.json');audit=read(R/'AUDIT_STATUS.json');pending=[]
if status['status']!='collection_complete_audits_visual_pending' or status['completed_conditions']!=10:pending.append('all original10 conditions must finish')
if audit['status']!='complete' or len(audit['completed_episodes'])!=10:pending.append('all original applicable audits must finish')
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
  for name in ['quality.json','AUDIT_EXECUTION.json','ACTUAL_REVIEW_BINDING.json']:
   if not (ep/name).exists():pending.append(ep.name+'/'+name)
if pending:print(json.dumps(dict(status='pending',reasons=pending,training_ready=False),indent=2));sys.exit(0)
for pid in [protocol['producer_pid'],audit['pid']]:
 p=Path('/proc')/str(pid);assert not p.exists() or (p/'stat').read_text().split()[2]=='Z',('process still active',pid)
bound(protocol['frozen_files_sha256']);results=[];all_rows=[];failures=[];groups={g['group']:[] for g in protocol['plan']['groups']}
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";quality=read(ep/'quality.json');short=quality['frames']<(70 if item['wait'] else 1200);actual=read(ep/'ACTUAL_REVIEW_BINDING.json');numeric_name='REAR_TRACKING_INCOMPLETE_REVIEW.json' if short else 'REAR_TRACKING_STAGE_NUMERIC_REVIEW.json';sheet='REAR_TRACKING_INCOMPLETE_REVIEW.jpg' if short else 'REAR_TRACKING_REVIEW.jpg';numeric=read(ep/numeric_name)
  assert actual['raw_sha256']==numeric['raw_sha256']==sha(ep/'raw.npz');assert actual['numeric_review_sha256']==sha(ep/numeric_name);assert actual['review_sheet_sha256']==numeric['review_sheet_sha256']==sha(ep/sheet)
  assert actual['actual_visual_review'].startswith('completed_actual_view');assert actual['sampled_rgb_frames']==numeric['sampled_rgb_frames'];assert actual['sampled_viewer_frames']==numeric['sampled_viewer_frames']
  for name,h in actual['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/name)==h
  if short:assert not quality['passed'] and not numeric['original_task_and_pose_passed'] and numeric['incomplete_episode'] and numeric['short_attempt_cannot_pass']
  else:assert numeric['frames']==(70 if item['wait'] else 1200)
  bound(read(ep/'READY_FOR_AUDIT.json')['source_sha256']);expected=primary(item['wait'])+['audit_rear_tracking_stage_contacts.py','audit_rear_tracking_stage_pressure.py'];fr=None
  if not item['wait']:fr=read(ep/'frontal_bypass.json');expected+=controls(fr['plan'])+ADDITIONAL
  expected=list(dict.fromkeys(expected));execution=read(ep/'AUDIT_EXECUTION.json');assert execution['completed'] and execution['distinct_applicable_audits']==expected and [x['script'] for x in execution['rows']]==expected
  failed=[]
  for x in execution['rows']:
   name,keys=REPORTS[x['script']];assert x['raw_sha256']==sha(ep/'raw.npz') and x['auditor_sha256']==sha(W/x['script']) and x['log_sha256']==sha(ep/(x['script']+'.log'))
   if x['report_sha256'] is not None:assert sha(ep/name)==x['report_sha256']
   if x['report_passed'] and x['returncode']==0:
    value=read(ep/name)
    for k in keys:value=value[k]
    assert value is True
   else:failed.append(x['script']);failures.append(dict(episode=ep.name,script=x['script'],returncode=x['returncode'],incomplete_episode=short,log_sha256=x['log_sha256'],log_tail=(ep/(x['script']+'.log')).read_text().splitlines()[-3:]))
   all_rows.append(x)
  changed=[] if fr is None else [r['step'] for r in fr['rows'] if r.get('rear_corridor_override') is not None]
  baseline=W/'fresh_closed_peak_trials_r1'/ep.parent.name/ep.name;old=read(baseline/'quality.json')
  row=dict(episode=ep.name,group=item['group'],wait=item['wait'],frames=quality['frames'],incomplete_episode=short,original_task_and_pose_passed=numeric['original_task_and_pose_passed'],original_quality_passed=quality['passed'],baseline_original_quality_passed=old['passed'],control_audits_passed=not failed,failed_audits=failed,rear_recovery_changed_steps=changed,numeric_review=numeric_name,training_admitted=False);results.append(row);groups[item['group']].append(row)
assert len(results)==10 and all_rows==audit['rows'];group_rows=[]
for name,rs in groups.items():
 assert len(rs)==5 and sum(x['wait'] for x in rs)==1
 group_rows.append(dict(group=name,push_passed=sum(x['original_task_and_pose_passed'] for x in rs if not x['wait']),push_total=4,wait_passed=all(x['original_task_and_pose_passed'] for x in rs if x['wait']),all_task_and_control_passed=all(x['original_task_and_pose_passed'] and x['control_audits_passed'] for x in rs),training_admitted=False))
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_complete_failures_retained',scope=__doc__,conditions=10,push_passed=sum(x['original_task_and_pose_passed'] for x in results if not x['wait']),push_total=8,wait_passed=sum(x['original_task_and_pose_passed'] for x in results if x['wait']),wait_total=2,baseline_push_passed=sum(x['baseline_original_quality_passed'] for x in results if not x['wait']),groups=group_rows,rows=results,audit_invocations=len(all_rows),failed_audit_invocations=failures,source_sha256=sources,frozen_sources_verified=len(protocol['frozen_files_sha256']),closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False)
if apply:
 with dest.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256','failed_audit_invocations','scope']},indent=2))
