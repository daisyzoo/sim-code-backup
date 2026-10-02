"""Close all10 diagnostic attempts, retaining every short or failed condition.
Requires current frozen sources, all completed audit invocations and actual
image bindings. Expert development closure is never training admission/h10.
"""
from pathlib import Path
import sys,json,datetime
import numpy as np
from box_entry_run_contract import controls,ADDITIONAL,REPORTS,primary,sha
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();assert not (r/'RESULT.json').exists();p=json.loads((r/'PROTOCOL.json').read_text());status=json.loads((r/'STATUS.json').read_text());ctrl=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());extra=json.loads((r/'ADDITIONAL_AUDIT_EXECUTION.json').read_text())
assert status['status']=='collection_complete_audits_visual_pending' and status['completed_conditions']==10
assert ctrl['stage']==extra['stage']=='complete'
for pid in {status['pid'],ctrl['pid'],extra['pid']}:assert not Path(f'/proc/{pid}/cmdline').exists()
for name,h in p['frozen_files_sha256'].items():assert sha(name)==h,name
expected={(c['layout_id'],t) for c in p['commands'] for t in c['tasks']};assert len(expected)==10
results=[];evidence={};seen=set()
def read(ep,name):
 path=ep/name;d=json.loads(path.read_text());evidence[str(path.relative_to(r))]=sha(path)
 for n,h in d.get('source_sha256',{}).items():assert sha(ep/n)==h,(ep,name,n)
 return d

def verify_invocation(ep,row):
 script=row['script'];assert row['auditor_sha256']==sha(w/script) and row['raw_sha256']==sha(ep/'raw.npz') and row['log_sha256']==sha(ep/(script+'.log'))
 name,keys=REPORTS[script];assert row['report']==name;path=ep/name
 if row['report_sha256'] is None:assert not path.exists() and row['returncode']!=0;return False
 assert row['report_sha256']==sha(path);d=read(ep,name);value=d
 for k in keys:value=value[k]
 assert row['report_passed']==(value is True)
 assert row['returncode']==(row['process_returncode'] if row['process_returncode'] else (0 if value is True else 1))
 return row['returncode']==0
for command in p['commands']:
 case=r/f"case_{command['layout_id']}";prov=json.loads((case/'provenance.json').read_text());assert prov['args']['rear_box_entry_lift'] is True and prov['args']['rear_box_center_preference'] is True and prov['args']['rear_slow_drag'] is True and prov['args']['minimum_motion_recontact'] is True and prov['args']['rear_joint_edge_parent_seed_retry'] is True and prov['args']['precise_clearance_task_ik'] is True and prov['args']['recontact_interior_preference'] is True and prov['args']['unloaded_recontact_pose'] is True
 for name,h in prov['source_sha256'].items():assert sha(case/'source_snapshot'/name)==h==p['frozen_files_sha256'][str(w.parents[1]/name)]
 for task in command['tasks']:
  ep=case/f"layout_{command['layout_id']}_{task}";wait=command['wait'];quality=read(ep,'quality.json');clear=read(ep,'self_clearance.json');n=clear['recorded_frames'];requested=70 if wait else 1200
  assert n==quality['frames'] and clear['requested_frames']==requested and 0<n<=requested
  with np.load(ep/'raw.npz') as z:
   assert z['q'].shape==z['action'].shape==(n,23);assert np.max(abs(z['q'][0,12:23]))<1e-4 and np.max(abs(z['action'][0,12:23]))==0
   meta=json.loads(str(z['collect_meta']));assert meta['task_ik_optimizer_ftol']==1e-13;assert meta['rear_box_entry_lift'] is True and meta['rear_box_center_preference'] is True and meta['rear_slow_drag'] is True and meta['minimum_motion_recontact'] is True and meta['rear_joint_edge_parent_seed_retry'] is True;assert meta['assist_frames']==0 and not meta['push_assist'] and meta['unloaded_recontact_pose'] is True
  if n<requested:assert not quality['passed'] and clear['failure'] is not None
  main=read(ep,'PRIMARY_AUDIT_EXECUTION.json');assert main['completed'] and [x['script'] for x in main['rows']]==primary(wait)
  invocations=list(main['rows'])
  if not wait:
   plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];crows=[x for x in ctrl['rows'] if x['episode']==ep.name];erows=[x for x in extra['rows'] if x['episode']==ep.name]
   assert [x['script'] for x in crows]==controls(plan) and [x['script'] for x in erows]==ADDITIONAL
   invocations+=crows+erows
  passed=[verify_invocation(ep,x) for x in invocations]
  # Visual proof remains human/model actual-image review, not an automatic flag.
  visual=read(ep,'ACTUAL_REVIEW_BINDING.json');samples=np.linspace(0,n-1,8,dtype=int).tolist();assert visual['sampled_rgb_frames']==samples
  if wait:
   assert visual['actual_visual_review']=='completed_actual_view_8RGB';assert visual['review_sheet_sha256']==sha(ep/'REVIEW_EVENTS.jpg');pose=quality['passed']
  else:
   assert visual['actual_sampled_visual_review']=='completed' and visual['review_sheet_sha256']==sha(ep/'REVIEW_EVEN.jpg')
   for name,h in visual['external_source_sha256'].items():assert sha(case/('viewer_'+ep.name)/name)==h
   if n==1200:assert visual['sampled_viewer_frames']==[0,395,795,1195]
   early=read(ep,'EARLY_REVIEW.json');assert early['quality']==quality;pose=early['pose']['search_success']
  seen.add((command['layout_id'],task))
  results.append(dict(episode=ep.name,layout_id=command['layout_id'],wait=wait,executed_frames=n,requested_frames=requested,full_length=n==requested,original_task_and_pose_passed=bool(quality['passed'] and pose and n==requested),all_audits_passed=all(passed),failed_audits=[x['script'] for x,ok in zip(invocations,passed) if not ok],progress_mm=quality['metrics'].get('target_final_progress_m',0)*1000,reasons=quality['reasons'],clearance_failure=clear['failure']))
assert seen==expected and len(ctrl['rows'])==80 and len(extra['rows'])==56
groups=[]
for name,ids in [('lateral',[840000,840001]),('diagonal',[840004,840005])]:
 group=[x for x in results if x['layout_id'] in ids];assert len(group)==4
 groups.append(dict(name=name,ids=ids,task_passed=sum(x['original_task_and_pose_passed'] for x in group),total=4,all_task_and_audits_passed=all(x['original_task_and_pose_passed'] and x['all_audits_passed'] for x in group),training_admitted=False))
out=dict(closed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_closed_not_training_admission',push_passed=sum(x['original_task_and_pose_passed'] for x in results if not x['wait']),push_total=8,waits_passed=sum(x['original_task_and_pose_passed'] for x in results if x['wait']),rows=results,groups=groups,original_control_invocations=80,additional_invocations=56,actual_sampled_visual_review_complete=True,qualified_training_groups=0,training_ready=False,scope=__doc__,protocol_sha256=sha(r/'PROTOCOL.json'),closer_sha256=sha(__file__),evidence_sha256=evidence,limitations=['Sampled hand/parcel and bilateral elbow geometry is not whole-body/substep certification.','Expert development results are not held-out modelh10 evidence.','Failures and shortened trajectories remain in denominator and cannot enter training.'])
(r/'RESULT.json').write_text(json.dumps(out,indent=2));(r/'RESULT.md').write_text('# 无载重接触完整诊断\n\n'+f"推任务 {out['push_passed']}/8；等待 {out['waits_passed']}/2。合格新训练组仍为0。\n\n"+'\n'.join(f"- {x['episode']}: task={x['original_task_and_pose_passed']}, audits={x['all_audits_passed']}, frames={x['executed_frames']}/{x['requested_frames']}, progress={x['progress_mm']:.3f}mm" for x in results)+'\n');print(out['push_passed'],out['waits_passed'],groups)
