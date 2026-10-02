"""Close all ten diagnostic conditions, keeping original failures plus supplements.
This closes evidence collection only and never admits diagnostic training data.
"""
from pathlib import Path
import json,hashlib,datetime,sys
W=Path(__file__).resolve().parent
from joint_edge_stage_run_contract import primary,controls,ADDITIONAL,REPORTS
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=W/'joint_edge_intersection_physical_r1';dest=R/'RESULT_WITH_SUPPLEMENT.json';assert not dest.exists()
sources={}
def read(p):
 p=Path(p);sources[str(p)]=sha(p);return json.loads(p.read_text())
def bound(mapping):
 for p,h in mapping.items():assert sha(p)==h,p
protocol=read(R/'PROTOCOL.json');resume=read(R/'RESUME_PROTOCOL.json');assert sha(R/'PROTOCOL.json')==resume['original_protocol_sha256'];bound(resume['frozen_files_sha256'])
status=read(R/'STATUS.json');audits=read(R/'AUDIT_STATUS.json');supp=read(R/'COMPACT_V2_AUDIT_STATUS.json');pressure=read(R/'PRESSURE_V2_LAUNCH.json')
assert status['status']=='collection_complete_audits_visual_pending' and status['completed_conditions']==10
assert audits['status']=='complete' and len(audits['completed_episodes'])==10
assert supp['status']=='complete' and supp['all_supplemental_audits_passed'];bound(supp['frozen_supplement_sha256'])
for pid in [status['pid'],audits['pid'],supp['pid'],pressure['pid']]:
 p=Path('/proc')/str(pid)
 assert not p.exists() or (p/'stat').read_text().split()[2]=='Z',('producer/auditor still active',pid)
prep=read(W/'JOINT_EDGE_PRESSURE_V2_PREPARATION.json');assert sha(prep['parent'])==prep['parent_sha256'] and sha(prep['candidate'])==prep['candidate_sha256'];text=Path(prep['candidate']).read_text()
for old,new in reversed(prep['edits']):assert text.count(new)==1;text=text.replace(new,old)
assert text==Path(prep['parent']).read_text()
comparison=read(R/'TASK_POSE_VISUAL_COMPARISON.json');bound(comparison['source_sha256'])
mapping=read(W/'JOINT_EDGE_COMPACT_DEPENDENT_AUDITS_PREPARATION.json');supprows={r['script']:r for r in supp['rows']};rows=[];failures=[];all_original=[]
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}"
  ready=read(ep/'READY_FOR_AUDIT.json');bound(ready['source_sha256'])
  scripts=primary(item['wait'])+['audit_joint_edge_stage_contacts.py','audit_joint_edge_stage_pressure.py']
  if not item['wait']:scripts+=controls(read(ep/'frontal_bypass.json')['plan'])+ADDITIONAL
  expected=list(dict.fromkeys(scripts));execution=read(ep/'AUDIT_EXECUTION.json')
  assert execution['completed'] and execution['distinct_applicable_audits']==expected
  assert [r['script'] for r in execution['rows']]==expected
  corrected=[]
  for r in execution['rows']:
   script=r['script'];name,keys=REPORTS[script]
   assert r['raw_sha256']==sha(ep/'raw.npz') and r['auditor_sha256']==sha(W/script) and r['log_sha256']==sha(ep/(script+'.log'))
   assert r['report']==name
   if r['report_sha256'] is not None:assert sha(ep/name)==r['report_sha256']
   if r['report_passed'] and r['returncode']==0:
    value=read(ep/name)
    for k in keys:value=value[k]
    assert value is True
   else:
    failures.append(dict(episode=ep.name,script=script,original_failure_retained=True));assert ep.name=='layout_840015_push_box_to_bin'
    if script=='audit_joint_edge_stage_pressure.py':
     new='audit_joint_edge_stage_pressure_v2.py';report=ep/'JOINT_EDGE_STAGE_PRESSURE_V2_AUDIT.json';value=read(report);assert value['auditor_sha256']==sha(W/new)==pressure['script_sha256'];assert value['source_sha256']['raw.npz']==sha(ep/'raw.npz')
    else:
     new=mapping['module_mapping'][script[:-3]]+'.py';s=supprows[new];assert s['passed'] and s['process_returncode']==0 and s['auditor_sha256']==sha(W/new);report=ep/s['report'];assert sha(report)==s['report_sha256'];value=read(report)
    for k in keys:value=value[k]
    assert value is True;corrected.append(dict(original_script=script,supplement_script=new,supplement_report=report.name))
   all_original.append(r)
  review=read(ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json');actual=read(ep/'ACTUAL_REVIEW_BINDING.json');quality=read(ep/'quality.json')
  assert actual['raw_sha256']==review['raw_sha256']==sha(ep/'raw.npz')
  assert actual['numeric_review_sha256']==sha(ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json')
  assert actual['review_sheet_sha256']==review['review_sheet_sha256']==sha(ep/'JOINT_EDGE_REVIEW.jpg')
  assert actual['sampled_rgb_frames']==review['sampled_rgb_frames'] and actual['sampled_viewer_frames']==review['sampled_viewer_frames']
  assert actual['actual_visual_review'].startswith('completed_actual_view')
  for name,h in actual['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/name)==h
  assert review['saved_quality_passed']==quality['passed']
  rows.append(dict(episode=ep.name,layout_id=item['layout_id'],wait=item['wait'],original_task_and_pose_passed=review['original_task_and_pose_passed'],all_control_evidence_covered_with_explicit_supplements=True,original_audits=len(expected),supplements=corrected,training_admitted=False))
assert len(rows)==10 and all_original==audits['rows'] and len(failures)==12
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_complete_with_separate_audit_corrections',scope=__doc__,conditions=10,push_passed=sum(r['original_task_and_pose_passed'] for r in rows if not r['wait']),push_total=8,wait_passed=sum(r['original_task_and_pose_passed'] for r in rows if r['wait']),wait_total=2,baseline_push_passed=comparison['baseline_push_passed'],task_gain=0,rows=rows,original_audit_invocations=len(all_original),original_audit_failures=failures,original_failures_not_overwritten=True,supplemental_audits=12,source_sha256=sources,frozen_sources_verified=len(resume['frozen_files_sha256']),closer_sha256=sha(__file__),training_ready=False,model_goal_achieved=False,next_action='Do not expand joint-edge repair as a task-success fix. Finish separate front-interval physical comparison and implement causal rear corridor recovery with original contact/joint/quality gates.')
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256','original_audit_failures','scope']},indent=2))
