"""Close a complete physically collected and actually reviewed v2 trial group.

This never fabricates a visual review or writes a converter approval. All-pass
results remain eligible for the existing full pair/split admission workflow.
"""
from pathlib import Path
import sys,json,hashlib,ast
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.schema import load_episode
from simfoundry.data.waist_pilot_audit import audit_waist_pilot_episode
r=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((r/'PROTOCOL.json').read_text());status=json.loads((r/'STATUS.json').read_text());control=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text())
assert status['stage']=='numeric_complete_actual_visual_review_pending' and control['stage']=='complete'
for pid in [status['pid'],control['pid']]:
 assert not Path('/proc',str(pid),'cmdline').exists(),f'Process{pid} still exists'
assert sha(protocol['contract_path'])==protocol['contract_sha256']
contract=json.loads(Path(protocol['contract_path']).read_text());assert contract['version']==2
assert protocol['layout_ids']==[x['layout_id'] for x in contract['layouts']]
assert protocol['wait_layout_ids']==[x['layout_id'] for x in contract['wait_layouts']]
b=json.loads((r/'ACTUAL_REVIEW_BINDINGS.json').read_text());bindings={x['episode']:x for x in b['rows']};expected_push={f'layout_{i}_{task}' for i in protocol['layout_ids'] for task in ['push_box_to_bin','nudge_mailer_to_bin']};assert set(bindings)==expected_push and len(bindings)==len(b['rows'])
rows=[];expected_controls=set();all_sources=[]
base=['audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_terminal_hold_inputs.py','audit_contact_stability_control.py','audit_contact_bout_yaw_live.py','audit_bounded_top_lead_live.py','audit_clearance_feedback_live.py','audit_initial_top_recovery_live.py','audit_initial_near_half_live.py']
for case in [r/f'case_{i}' for i in protocol['layout_ids']]:
 pose_rows=json.loads((case/'POSE_AND_MOTION_REVIEW.json').read_text())['rows'];assert len(pose_rows)==2
 for row in pose_rows:
  ep=case/row['episode'];bind=bindings[row['episode']];assert bind['actual_sampled_visual_review']=='completed';assert sha(ep/'raw.npz')==bind['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==bind['review_sheet_sha256'];assert bind['sampled_rgb_frames']==np.linspace(0,row['quality']['frames']-1,8,dtype=int).tolist();assert len(bind['sampled_viewer_frames'])==4
  actual=load_episode(ep/'raw.npz');provenance=json.loads((case/'provenance.json').read_text())
  try:fresh=dict(passed=True,report=audit_waist_pilot_episode(ep/'raw.npz',actual,provenance))
  except ValueError as e:fresh=dict(passed=False,error=str(e))
  fresh.update(raw_sha256=sha(ep/'raw.npz'),first_upper_state_max_abs_rad=float(np.max(abs(actual.q[0,12:]))),first_upper_action_max_abs_rad=float(np.max(abs(actual.action[0,12:]))),assist_frames=actual.collect_meta['assist_frames'],training_ready=False)
  all_sources.append(fresh);row.update(bind);row.update(source_audit=fresh,query_phases=json.loads((ep/'EARLY_QUERY_PHASES.json').read_text()));rows.append(row)
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts=list(base)
  if plan.get('initial_top_selected'):scripts+=['audit_y_path_clearance_live.py']
  if plan.get('front_route_selected'):scripts+=['audit_front_recovery_height_live.py','audit_recovery_and_anchor.py']
  if (ep/'contact_center_calibration.json').exists():scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
  expected_controls.update((ep.name,s) for s in scripts)
assert {x['episode'] for x in rows}==expected_push
waits=[]
for i in protocol['wait_layout_ids']:
 ep=r/f'case_{i}/layout_{i}_wait_no_package';a=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());bind=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert bind['actual_visual_review']=='completed_actual_view_8RGB';assert sha(ep/'raw.npz')==a['raw_sha256']==bind['raw_sha256'];assert sha(ep/'REVIEW_EVENTS.jpg')==bind['review_sheet_sha256'];assert a['sampled_rgb_frames']==bind['sampled_rgb_frames']
 actual=load_episode(ep/'raw.npz')
 try:fresh=dict(passed=True,report=audit_waist_pilot_episode(ep/'raw.npz',actual,json.loads((ep.parent/'provenance.json').read_text())))
 except ValueError as e:fresh=dict(passed=False,error=str(e))
 fresh.update(raw_sha256=sha(ep/'raw.npz'),first_upper_state_max_abs_rad=float(np.max(abs(actual.q[0,12:]))),first_upper_action_max_abs_rad=float(np.max(abs(actual.action[0,12:]))),assist_frames=actual.collect_meta['assist_frames'],training_ready=False);all_sources.append(fresh);waits.append(dict(episode=ep.name,audit=a,actual_review=bind,source_audit=fresh));(ep/'FRESH_SOURCE_AUDIT.json').write_text(json.dumps(fresh,indent=2))
assert {(x['episode'],x['script']) for x in control['rows']}==expected_controls and len(control['rows'])==len(expected_controls)
specs=ast.literal_eval(next(n.value for n in ast.walk(ast.parse((w/'watch_fresh_pilot_controls.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
for row in control['rows']:
 ep=next(r.glob('case_*/'+row['episode']));name,keys=specs[row['script']];assert row['returncode']==row['process_returncode']==0 and row['report_passed'] is True;assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/name)==row['report_sha256'] and sha(w/row['script'])==row['auditor_sha256'];value=json.loads((ep/name).read_text())
 for key in keys:value=value[key]
 assert value is True
passed=sum(x['quality']['passed'] and x['pose']['search_success'] for x in rows);wait_pass=all(x['audit']['passed'] and not x['audit']['errors'] for x in waits);sources_pass=all(x['passed'] for x in all_sources);eligible=passed==len(rows) and wait_pass and sources_pass
reason='Complete physical/source/sampled-visual checks passed; existing full pair/split converter admission is next.' if eligible else 'At least one original task/pose/wait/source gate failed; entire registered swap+wait group quarantined.'
result=dict(rows=rows,waits=waits,push_passed=passed,push_total=len(rows),wait_passed=wait_pass,all_source_audits_passed=sources_pass,full_group_checks_passed=eligible,full_group_admitted=False,reason=reason,visual_review='completed_actual_view_each_push8RGB4external_each_wait8RGB',control_reports_verified=len(expected_controls),contract_sha256=protocol['contract_sha256'],training_ready=False)
(r/'RESULT.json').write_text(json.dumps(result,indent=2));(r/'PILOT_ADMISSION_RESULT.json').write_text(json.dumps(dict(admitted=False,status='pending_existing_pair_split_admission' if eligible else 'rejected',reason=reason,result_sha256=sha(r/'RESULT.json'),source_audit_passes=sum(x['passed'] for x in all_sources),source_audit_failures=sum(not x['passed'] for x in all_sources),training_ready=False),indent=2))
lines=[f'# 完整交换组：push{passed}/{len(rows)}，wait{"通过" if wait_pass else "失败"}','',reason,'','|条件|推进mm|原任务+姿态|','|---|---:|---|']
for x in rows:lines.append(f"|{x['episode']}|{1000*x['quality']['metrics']['target_final_progress_m']:.3f}|{'通过' if x['quality']['passed'] and x['pose']['search_success'] else '失败'}|")
lines+=['',f'{len(expected_controls)}份真实控制报告/raw/report/auditor哈希已核；逐条实际图审已绑定，未用数值成功代替画面审核。','没有自动批准review.json、转换或训练。各条图像风险及首零位/无助推/非目标/pose详细记录见RESULT.json。']
(r/'RESULT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','waits')},indent=2))
