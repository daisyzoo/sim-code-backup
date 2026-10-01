"""Close actual reviewed failed group; no approved review or conversion."""
from pathlib import Path
import sys,json,hashlib,ast
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path.insert(0,str(repo));import numpy as np
from simfoundry.data.schema import load_episode
from simfoundry.data.waist_pilot_audit import audit_waist_pilot_episode
r=w/'fresh_diagonal_02_trial_v2_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for pid in [577428,577492]:assert not Path('/proc',str(pid),'cmdline').exists()
assert json.loads((r/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
notes={'layout_840005_push_box_to_bin':'Actually viewed8RGB+4external. Box visible0, absent171 onward; bag remains visible, edge-clipped513. External right-hand pressing and raised withdrawal visible. Original numeric+pose pass, but target image loss remains a learning risk.','layout_840005_nudge_mailer_to_bin':'Actually viewed8RGB+4external. Bag visible0/171/342, left-clipped513/685/856/1027/1199; box visible throughout. External left-hand work and raised withdrawal visible. Original numeric+pose pass, but substantial target clipping remains a learning risk.'}
b=json.loads((r/'ACTUAL_REVIEW_BINDINGS.json').read_text())
for name,note in notes.items():
 ep=next(r.glob('case_*/'+name));j=json.loads((ep/'EARLY_REVIEW.json').read_text());j.update(actual_sampled_visual_review='completed',visual_notes=note);(ep/'EARLY_REVIEW.json').write_text(json.dumps(j,indent=2));b['rows']=[x for x in b['rows'] if x['episode']!=name];b['rows'].append({k:j[k] for k in ['episode','raw_sha256','review_sheet_sha256','sampled_rgb_frames','sampled_viewer_frames','actual_sampled_visual_review','visual_notes']})
(r/'ACTUAL_REVIEW_BINDINGS.json').write_text(json.dumps(b,indent=2));bindings={row['episode']:row for row in b['rows']};assert len(bindings)==4
rows=[]
for case in sorted(r.glob('case_*')):
 if not (case/'POSE_AND_MOTION_REVIEW.json').exists():continue
 for row in json.loads((case/'POSE_AND_MOTION_REVIEW.json').read_text())['rows']:
  ep=case/row['episode'];bind=bindings[row['episode']];assert bind['actual_sampled_visual_review']=='completed';assert sha(ep/'raw.npz')==bind['raw_sha256'] and sha(ep/'REVIEW_EVEN.jpg')==bind['review_sheet_sha256'];row.update(bind);row['source_audit']=json.loads((ep/'FRESH_SOURCE_AUDIT.json').read_text());row['query_phases']=json.loads((ep/'EARLY_QUERY_PHASES.json').read_text());rows.append(row)
wait=r/'case_841002/layout_841002_wait_no_package';audit=json.loads((wait/'WAIT_STABILITY_AUDIT.json').read_text());assert audit['passed'] and not audit['errors'];assert sha(wait/'raw.npz')==audit['raw_sha256'];event=json.loads((wait/'EVENT_REVIEW.json').read_text());assert event['frames']==audit['sampled_rgb_frames'] and sha(wait/'REVIEW_EVENTS.jpg')==event['image_sha256']
audit.update(actual_visual_review='completed_actual_view_8RGB',review_sheet_sha256=sha(wait/'REVIEW_EVENTS.jpg'),visual_notes='Actually viewed all8RGB: empty tabletop, both palms steady, no visible instructed movement or package. Numeric palm drift2.098mm and waist3.09e-9rad within unchanged gates.');(wait/'WAIT_STABILITY_AUDIT.json').write_text(json.dumps(audit,indent=2));event['actual_review']='completed';(wait/'EVENT_REVIEW.json').write_text(json.dumps(event,indent=2))
actual=load_episode(wait/'raw.npz');fresh=audit_waist_pilot_episode(wait/'raw.npz',actual,json.loads((wait.parent/'provenance.json').read_text()));assert fresh['original_audit']['passed'];waitsource=dict(passed=True,report=fresh,raw_sha256=sha(wait/'raw.npz'),first_upper_state_max_abs_rad=float(np.max(abs(actual.q[0,12:]))),first_upper_action_max_abs_rad=float(np.max(abs(actual.action[0,12:]))),assist_frames=actual.collect_meta['assist_frames'],training_ready=False);(wait/'FRESH_SOURCE_AUDIT.json').write_text(json.dumps(waitsource,indent=2));(wait/'ACTUAL_REVIEW_BINDING.json').write_text(json.dumps(dict(raw_sha256=sha(wait/'raw.npz'),review_sheet_sha256=sha(wait/'REVIEW_EVENTS.jpg'),sampled_rgb_frames=audit['sampled_rgb_frames'],actual_visual_review='completed_actual_view_8RGB',training_ready=False),indent=2))
control=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());assert control['stage']=='complete' and len(control['rows'])==40
specs=ast.literal_eval(next(n.value for n in ast.walk(ast.parse((w/'watch_fresh_pilot_controls.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
for row in control['rows']:
 ep=next(r.glob('case_*/'+row['episode']));name,keys=specs[row['script']];assert row['returncode']==row['process_returncode']==0 and row['report_passed'] is True;assert sha(ep/'raw.npz')==row['raw_sha256'] and sha(ep/name)==row['report_sha256'];value=json.loads((ep/name).read_text())
 for key in keys:value=value[key]
 assert value is True
passed=sum(row['quality']['passed'] and row['pose']['search_success'] for row in rows);assert passed==3 and len(rows)==4
result=dict(rows=rows,wait=audit,push_passed=passed,push_total=4,wait_passed=True,full_group_admitted=False,reason='840004 nudge_mailer_to_bin failed original task; entire registered swap+wait group quarantined.',visual_review='completed_actual_view4x8RGB4external_plus_wait8RGB',control_reports_verified=40,training_ready=False)
(r/'RESULT.json').write_text(json.dumps(result,indent=2));(r/'PILOT_ADMISSION_RESULT.json').write_text(json.dumps(dict(admitted=False,reason=result['reason'],result_sha256=sha(r/'RESULT.json'),source_audit_passes=4,source_audit_failures=1,source_audit_failure_expected='Pilot failed original task/waist/pose gates',training_ready=False),indent=2))
lines=['# 原斜向完整组：push3/4，wait通过，整组拒绝训练','', '4条push各8RGB+4外部画面、wait8RGB已实际查看绑定；40实际控制报告/原始数据哈希核验。普通等待双掌最大漂移2.098mm、腰3.09e-9rad。全部5条首上半身state/action为0、assist0；3条push与wait生产来源审计过，失败袋被原质量门明确拒绝。','', '|条件|推进mm|原任务+姿态|','|---|---:|---|']
for row in rows:lines.append(f"|{row['episode']}|{1000*row['quality']['metrics']['target_final_progress_m']:.3f}|{'通过' if row['quality']['passed'] and row['pose']['search_success'] else '失败'}|")
lines+=['','**好：**新原斜向组中三推通过，所有非目标maxXY0，等待稳定。','**差：**840004袋后绕后top_descend卡住，载荷0；RGB171起两物均缺失。交换盒通过但RGB171起目标丢失，交换袋后段明显左裁。交换盒/袋推进仅比150mm多.301/.039mm，不能称多seed鲁棒。','未批准成功半组、未写approved review.json、未转换/训练。下一原reverse_diagonal03完整组继续相同profile；全四族12计划和独立测试不缩小。接触区域离线新证据另见CAUSE_REPORT.md，不是已验证物理修复。']
(r/'RESULT.md').write_text('\n'.join(lines)+'\n');print('closed push3/4, wait passed,40controls,actual review done; rejected full group')
