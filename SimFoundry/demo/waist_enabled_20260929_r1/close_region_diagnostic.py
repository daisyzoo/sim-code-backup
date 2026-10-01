"""Exact source/control/full-pair/sampled-view closure; diagnostic never admitted."""
from pathlib import Path
import sys,json,hashlib,ast
import numpy as np
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();p=json.loads((r/'PROTOCOL_R3.json').read_text());status=json.loads((r/'STATUS.json').read_text());control=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert status['stage']=='numeric_complete_actual_visual_review_pending' and control['stage']=='complete'
for pid in [status['pid'],control['pid']]:assert not (Path('/proc')/str(pid)/'cmdline').exists()
expected_push={f'layout_{i}_{t}' for i in p['layout_ids'] for t in ['push_box_to_bin','nudge_mailer_to_bin']};b=json.loads((r/'ACTUAL_REVIEW_BINDINGS.json').read_text())['rows'];bindings={x['episode']:x for x in b};assert set(bindings)==expected_push and len(b)==len(expected_push)
base=['audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_terminal_hold_inputs.py','audit_contact_stability_control.py','audit_contact_bout_yaw_live.py','audit_bounded_top_lead_live.py','audit_clearance_feedback_live.py','audit_initial_top_recovery_live.py','audit_initial_near_half_live.py'];expected_controls=set();rows=[];waits=[]
for case_id in p['layout_ids']+p['wait_layout_ids']:
 case=r/f'case_{case_id}';prov=json.loads((case/'provenance.json').read_text());assert prov['source_sha256']==p['source_sha256']
 for rel,h in p['source_sha256'].items():assert sha(case/'source_snapshot'/rel)==h
 for ep in case.glob('layout_*'):
  with np.load(ep/'raw.npz') as raw:
   assert raw['q'].shape==raw['action'].shape==(70 if case_id in p['wait_layout_ids'] else 1200,23);assert np.max(abs(raw['q'][0,12:]))==np.max(abs(raw['action'][0,12:]))==0;meta=json.loads(str(raw['collect_meta']));assert meta['assist_frames']==0 and meta['push_assist'] is False
  if case_id in p['wait_layout_ids']:
   a=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());bind=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert a['passed'] and not a['errors'] and bind['actual_visual_review']=='completed_actual_view_8RGB';assert bind['raw_sha256']==sha(ep/'raw.npz') and bind['review_sheet_sha256']==sha(ep/'REVIEW_EVENTS.jpg');waits.append(dict(episode=ep.name,audit=a,actual_review=bind));continue
  bind=bindings[ep.name];assert bind['actual_sampled_visual_review']=='completed' and bind['raw_sha256']==sha(ep/'raw.npz') and bind['review_sheet_sha256']==sha(ep/'REVIEW_EVEN.jpg');assert bind['sampled_rgb_frames']==np.linspace(0,1199,8,dtype=int).tolist() and len(bind['sampled_viewer_frames'])==4
  a=json.loads((ep/'EARLY_REVIEW.json').read_text());qa=json.loads((ep/'REGION_ACTION_LIVE_AUDIT_R2.json').read_text());assert qa['passed'] and qa['source_sha256']['raw.npz']==sha(ep/'raw.npz');rows.append(dict(episode=ep.name,quality=a['quality'],pose=a['pose'],actual_review=bind,region_action_audit=qa))
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts=list(base)
  if plan.get('initial_top_selected'):scripts+=['audit_y_path_clearance_live.py']
  if plan.get('front_route_selected'):scripts+=['audit_front_recovery_height_live.py','audit_recovery_and_anchor.py']
  if (ep/'contact_center_calibration.json').exists():scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
  expected_controls.update((ep.name,s) for s in scripts)
assert {(x['episode'],x['script']) for x in control['rows']}==expected_controls and len(control['rows'])==len(expected_controls)
specs=ast.literal_eval(next(n.value for n in ast.walk(ast.parse((w/'watch_fresh_pilot_controls.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)))
for x in control['rows']:
 ep=next(r.glob('case_*/'+x['episode']));name,keys=specs[x['script']];assert x['process_returncode']==0 and x['report_passed'] is True;assert sha(ep/'raw.npz')==x['raw_sha256'] and sha(ep/name)==x['report_sha256'] and sha(w/x['script'])==x['auditor_sha256'];v=json.loads((ep/name).read_text())
 for key in keys:v=v[key]
 assert v is True
assert len(waits)==2 and {x['episode'] for x in rows}==expected_push
result=dict(push_passed=sum(x['quality']['passed'] and x['pose']['search_success'] for x in rows),push_total=8,wait_passed=True,rows=rows,waits=waits,source_archives_per_case=49,original_control_reports_verified=len(expected_controls),region_action_reports_verified=8,full_groups_admitted=0,training_ready=False,reason='Both complete diagnostic swap groups fail original tasks; no pilot admission, conversion or training. Region approach did not improve total5/8. Actual sampled review completed; visibility risks remain.',protocol_sha256=sha(r/'PROTOCOL_R3.json'))
(r/'RESULT.json').write_text(json.dumps(result,indent=2));lines=['# 区域接近完整诊断：分拣5/8，两条等待通过，整组拒绝','',result['reason'],'','|条件|进度mm|原任务+姿态|','|---|---:|---|']
for x in rows:lines.append(f"|{x['episode']}|{1000*x['quality']['metrics']['target_final_progress_m']:.3f}|{'通过' if x['quality']['passed'] and x['pose']['search_success'] else '失败'}|")
lines+=['',f"{len(expected_controls)}原控制报告、8新动作报告和6case各49来源快照已核验；8×8RGB+4external、2×8wait实际图审已绑定。",'两个后绕例分别仅4/2个区域命令后实际最低点越界，没有handover/真实加载。所有失败保留、无转换。']
(r/'RESULT.md').write_text('\n'.join(lines)+'\n');print({k:v for k,v in result.items() if k not in ['rows','waits']})
