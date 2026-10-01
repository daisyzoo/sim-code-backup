"""Close the full development diagnostic, preserving task and extra audit failures.
A closed report is not data admission. Original source archives and all completed
controls, command geometry, sampled visual bindings and optimality are checked.
The frozen old execution auditor rejected the changed collector source hash.
Retain all eight failures and require separate version-bound replay with exact
original math, independently checked source contracts and negative tests.
"""
from pathlib import Path
import ast,json,sys,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((r/'PROTOCOL.json').read_text());s=json.loads((r/'STATUS.json').read_text());controls=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());extra=json.loads((r/'ADDITIONAL_AUDIT_EXECUTION.json').read_text())
assert s['completed_conditions']==10 and s['status']=='collection_and_geometry_audit_complete_original_audits_visual_pending'
assert controls['stage']=='complete' and len(controls['rows'])==80
for pid in [s['pid'],controls['pid']]:assert not (Path('/proc')/str(pid)/'cmdline').exists()
for name,h in p['frozen_files_sha256'].items():assert sha(name)==h,name
specs=ast.literal_eval(next(n.value for n in ast.walk(ast.parse((w/'watch_fresh_pilot_controls.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
expected={(x['layout_id'],task) for x in p['commands'] for task in x['tasks']};assert len(expected)==10
rows=[];evidence={};optimality=[]
def read_bound(ep,name,require_pass=True):
 d=json.loads((ep/name).read_text());evidence[str((ep/name).relative_to(r))]=sha(ep/name)
 if require_pass:assert d['passed'] and not d.get('errors'),(ep,name)
 for f,h in d.get('source_sha256',{}).items():assert sha(ep/f)==h,(ep,name,f)
 if 'raw_sha256' in d:assert sha(ep/'raw.npz')==d['raw_sha256']
 return d
for command in p['commands']:
 case=r/f"case_{command['layout_id']}";prov=json.loads((case/'provenance.json').read_text())
 for name,h in prov['source_sha256'].items():assert sha(case/'source_snapshot'/name)==h
 for task in command['tasks']:
  ep=case/f"layout_{command['layout_id']}_{task}";wait=command['wait'];quality=json.loads((ep/'quality.json').read_text());n=70 if wait else 1200
  with np.load(ep/'raw.npz') as z:
   assert z['q'].shape==z['action'].shape==(n,23)
   assert np.max(abs(z['q'][0,12:23]))==np.max(abs(z['action'][0,12:23]))==0
   meta=json.loads(str(z['collect_meta']));assert meta['assist_frames']==0 and not meta['push_assist']
  assert quality['frames']==n
  geom=read_bound(ep,'SELF_CLEARANCE_LIVE_AUDIT.json');assert geom['executed_frames']==n and geom['episode_clearance_passed']
  visual=read_bound(ep,'ACTUAL_REVIEW_BINDING.json',False)
  if wait:
   wa=read_bound(ep,'WAIT_STABILITY_AUDIT.json');assert wa['trace_sha256']==sha(ep/'trace.npz') and wa['provenance_sha256']==sha(case/'provenance.json')
   assert visual['actual_visual_review']=='completed_actual_view_8RGB' and visual['sampled_rgb_frames']==[0,9,19,29,39,49,59,69]
   assert visual['review_sheet_sha256']==sha(ep/'REVIEW_EVENTS.jpg');pose_success=quality['passed'];kkt=None
  else:
   pose=read_bound(ep,'EARLY_REVIEW.json',False);assert pose['quality']==quality;pose_success=pose['pose']['search_success'];assert visual['actual_sampled_visual_review']=='completed'
   assert visual['sampled_rgb_frames']==np.linspace(0,1199,8,dtype=int).tolist() and visual['sampled_viewer_frames']==[0,395,795,1195]
   assert visual['review_sheet_sha256']==sha(ep/'REVIEW_EVEN.jpg')
   for name,h in visual['external_source_sha256'].items():assert sha(case/('viewer_'+ep.name)/name)==h
   for name in ['REGION_ACTION_LIVE_AUDIT_R2.json','CAUSAL_REGION_ACTION_AUDIT.json','REGION_CONTINUITY_LIVE_AUDIT.json','MEASURED_BOUNDS_LIVE_AUDIT.json','REAR_JOINT_XY_LIVE_AUDIT.json','FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json','REAR_SHORT_UNCHANGED_LOADED_EXECUTION_AUDIT.json']:read_bound(ep,name)
   direction=read_bound(ep,'MICRO_CLEARANCE_RETURN_LIVE_AUDIT.json');assert direction['selected']==bool(json.loads((ep/'frontal_bypass.json').read_text())['plan'].get('front_route_selected'));assert direction['frames']==1199
   rear_height=read_bound(ep,'REAR_SHORT_RECOVERY_LIVE_AUDIT.json');assert rear_height['frames']==1199
   kkt=read_bound(ep,'SELF_CLEARANCE_TASK_OPTIMALITY_AUDIT.json',False);assert kkt['frames']==1199
   optimality.append(dict(episode=ep.name,passed=kkt['passed'],overrides=kkt['overrides'],failed_frames=len(kkt['errors']),max_kkt_residual=kkt['max_kkt_residual']))
  rows.append(dict(episode=ep.name,layout_id=command['layout_id'],wait=wait,original_task_and_pose_passed=bool(quality['passed'] and pose_success),progress_mm=quality['metrics'].get('target_final_progress_m',0)*1000,reasons=quality['reasons'],minimum_actual_gap_mm=geom['minimum_actual_support_gap_m']*1000,extra_task_optimality_passed=kkt['passed'] if kkt else None))
for row in controls['rows']:
 ep=next(r.glob('case_*/'+row['episode']));name,keys=specs[row['script']];assert row['returncode']==row['process_returncode']==0 and row['report_passed']
 assert sha(ep/name)==row['report_sha256'] and sha(w/row['script'])==row['auditor_sha256'] and sha(ep/'raw.npz')==row['raw_sha256']
 d=json.loads((ep/name).read_text())
 for key in keys:d=d[key]
 assert d is True;evidence[str((ep/name).relative_to(r))]=sha(ep/name)
assert extra['stage']=='complete' and len(extra['rows'])==48
supp=json.loads((r/'SUPPLEMENTAL_AUDIT_EXECUTION.json').read_text());assert supp['stage']=='complete' and len(supp['rows'])==8
assert not Path(f"/proc/{supp['pid']}/cmdline").exists()
for name,h in supp['source_sha256'].items():assert sha(name)==h
supp_rows={x['episode']:x for x in supp['rows']};assert len(supp_rows)==8
for row in supp['rows']:
 ep=next(r.glob('case_*/'+row['episode']));assert row['returncode']==0 and row['passed'] and row['original_failure_retained']
 assert sha(ep/'REAR_SHORT_UNCHANGED_LOADED_EXECUTION_AUDIT.json')==row['report_sha256']
 assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/'audit_micro_unchanged_loaded_execution.py.log')==row['original_log_sha256']
 report=json.loads((ep/'REAR_SHORT_UNCHANGED_LOADED_EXECUTION_AUDIT.json').read_text());assert report['auditor_sha256']==sha(w/'audit_rear_short_unchanged_loaded_execution.py')==row['auditor_sha256']
 binding=report['version_binding'];assert binding['protocol_sha256']==sha(r/'PROTOCOL.json') and binding['height_audit_sha256']==sha(ep/'REAR_SHORT_RECOVERY_LIVE_AUDIT.json')
 assert binding['integration_sha256']==sha(w/'staged_rear_short_recovery/INTEGRATION_CHECK.json') and binding['original_audit_sha256']==sha(w/'audit_micro_unchanged_loaded_execution.py')
 assert binding['original_failed_log_sha256']==row['original_log_sha256']
 assert report['reference_audit_sha256']==sha(ep/'REAR_JOINT_XY_LIVE_AUDIT.json')
source_mismatch_failures=[]
for row in extra['rows']:
 assert sha(w/row['script'])==row['auditor_sha256']
 if row['script']=='audit_self_clearance_task_optimality.py':
  ep=next(r.glob('case_*/'+row['episode']));reported=json.loads((ep/'SELF_CLEARANCE_TASK_OPTIMALITY_AUDIT.json').read_text());assert row['returncode']==(0 if reported['passed'] else 1)
 elif row['script']=='audit_micro_unchanged_loaded_execution.py':
  ep=next(r.glob('case_*/'+row['episode']));log=ep/'audit_micro_unchanged_loaded_execution.py.log';assert row['returncode']==1 and sha(log)==row['log_sha256']==supp_rows[row['episode']]['original_log_sha256']
  assert "sha(w/'staged_micro_clearance_return'/name)" in log.read_text() and log.read_text().strip().endswith('AssertionError')
  source_mismatch_failures.append(dict(episode=ep.name,original_log_sha256=sha(log),supplemental_report_sha256=supp_rows[ep.name]['report_sha256']))
 else:assert row['returncode']==0
 ep=next(r.glob('case_*/'+row['episode']));assert sha(ep/'raw.npz')==row['raw_sha256']
assert len(source_mismatch_failures)==8
assert {(x['layout_id'],x['episode'].split('_',2)[2]) for x in rows}==expected
out=dict(closed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='diagnostic_closed_rejected',push_passed=sum(x['original_task_and_pose_passed'] for x in rows if not x['wait']),push_total=8,waits_passed=sum(x['original_task_and_pose_passed'] for x in rows if x['wait']),groups=[dict(name='lateral',ids=[840000,840001],passed=sum(x['original_task_and_pose_passed'] for x in rows if x['layout_id'] in [840000,840001]),total=4,accepted=False),dict(name='diagonal',ids=[840004,840005],passed=sum(x['original_task_and_pose_passed'] for x in rows if x['layout_id'] in [840004,840005]),total=4,accepted=False)],original_control_reports=80,additional_audit_invocations=48,rear_short_recovery_audits=8,micro_clearance_return_audits=8,diagonal_entry_audits=8,actual_sampled_visual_review_complete=True,geometry_commands_checked=9740,geometry_pre_post_poses_checked=19480,rows=rows,extra_task_optimality=optimality,all_extra_task_optimality_passed=all(x['passed'] for x in optimality),original_execution_source_mismatch_failures=source_mismatch_failures,supplemental_execution_audits=8,supplemental_protocol_sha256=sha(r/'SUPPLEMENTAL_AUDIT_PROTOCOL.json'),supplemental_execution_sha256=sha(r/'SUPPLEMENTAL_AUDIT_EXECUTION.json'),qualified_groups=0,training_ready=False,scope=__doc__,limitations=['Geometry covers bilateral elbow/torso at control ticks, not all bodies or physics substeps.','Extra1e-6 IK optimality results are reported per episode; failed criteria are not waived. Command feasibility is checked separately.','All are expert development conditions, not independent model h10 evaluation.','RGB targets/work hands frequently cropped or outside view; learnability unresolved.'],protocol_sha256=sha(r/'PROTOCOL.json'),evidence_sha256=evidence,closer_sha256=sha(__file__))
(r/'RESULT.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['rows','evidence_sha256','scope','extra_task_optimality']})
