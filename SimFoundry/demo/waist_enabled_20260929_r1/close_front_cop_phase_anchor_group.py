# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Close exactly one full declared swap group+wait; no training promotion."""
from pathlib import Path
import sys,json,hashlib,ast
import numpy as np
w=Path(__file__).resolve().parent;r=Path(sys.argv[1]).resolve();group=sys.argv[2];protocol=json.loads((r/'PROTOCOL.json').read_text());ids=protocol['groups'][group];wi=protocol['wait_layout_ids'][list(protocol['groups']).index(group)];expected={f'layout_{i}_{t}' for i in ids for t in ['push_box_to_bin','nudge_mailer_to_bin']};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bindings={x['episode']:x for x in json.loads((r/'ACTUAL_REVIEW_BINDINGS.json').read_text())['rows']};control=json.loads((r/'CONTROL_EVIDENCE_EXECUTION.json').read_text());specs=ast.literal_eval(next(n.value for n in ast.walk(ast.parse((w/'watch_fresh_pilot_controls.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='report_specs' for t in n.targets)));rows=[];waits=[];needed=set()
base=['audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_terminal_hold_inputs.py','audit_contact_stability_control.py','audit_contact_bout_yaw_live.py','audit_bounded_top_lead_live.py','audit_clearance_feedback_live.py','audit_initial_top_recovery_live.py','audit_initial_near_half_live.py']
for i in [*ids,wi]:
 case=r/f'case_{i}';prov=json.loads((case/'provenance.json').read_text());assert prov['source_sha256']==protocol['source_sha256'];assert prov['args']['front_cop_phase_anchor'] and prov['args']['front_cop_slip_following'] and prov['args']['region_top_approach'] and prov['args']['region_tracking_residual']
 for path,h in protocol['source_sha256'].items():assert sha(case/'source_snapshot'/path)==h
 eps=sorted(case.glob('layout_*'));assert len(eps)==(1 if i==wi else 2)
 for ep in eps:
  with np.load(ep/'raw.npz') as z:
   assert z['q'].shape==z['action'].shape==(70 if i==wi else 1200,23);assert np.max(abs(z['q'][0,12:]))==np.max(abs(z['action'][0,12:]))==0;meta=json.loads(str(z['collect_meta']));assert meta['assist_frames']==0 and meta['push_assist'] is False
  if i==wi:
   a=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text());b=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert a['passed'] and not a['errors'];assert b['actual_visual_review']=='completed_actual_view_8RGB' and b['raw_sha256']==sha(ep/'raw.npz') and b['review_sheet_sha256']==sha(ep/'REVIEW_EVENTS.jpg');assert b['sampled_rgb_frames']==[0,9,19,29,39,49,59,69];waits.append(dict(episode=ep.name,audit=a,binding=b));continue
  assert ep.name in expected;b=bindings[ep.name];assert b['actual_sampled_visual_review']=='completed' and b['raw_sha256']==sha(ep/'raw.npz') and b['review_sheet_sha256']==sha(ep/'REVIEW_EVEN.jpg');assert b['sampled_rgb_frames']==np.linspace(0,1199,8,dtype=int).tolist() and len(b['sampled_viewer_frames'])==4
  a=json.loads((ep/'EARLY_REVIEW.json').read_text());qa=json.loads((ep/'TRACKING_REGION_ACTION_AUDIT.json').read_text());ba=json.loads((ep/'REGION_ACTION_LIVE_AUDIT_R2.json').read_text());assert qa['passed'] and not qa['errors'] and qa['raw_sha256']==sha(ep/'raw.npz') and qa['base_audit_sha256']==sha(ep/'REGION_ACTION_LIVE_AUDIT_R2.json') and qa['auditor_sha256']==protocol['tracking_base_auditor_sha256'];assert ba['passed'] and ba['source_sha256']['raw.npz']==sha(ep/'raw.npz');assert a['quality']==json.loads((ep/'quality.json').read_text()) and a['raw_sha256']==sha(ep/'raw.npz')
  ca=json.loads((ep/'REGION_CONTINUITY_LIVE_AUDIT.json').read_text());assert ca['passed'] and not ca['errors'] and ca['raw_sha256']==sha(ep/'raw.npz') and ca['tracking_audit_sha256']==sha(ep/'TRACKING_REGION_ACTION_AUDIT.json') and ca['auditor_sha256']==protocol['continuity_base_auditor_sha256']
  fa=json.loads((ep/'FRONT_COP_LIVE_AUDIT.json').read_text());assert fa['passed'] and not fa['errors'] and fa['auditor_sha256']==protocol['audit_sha256']
  for file,h in fa['source_sha256'].items():assert sha(ep/file)==h
  assert fa['enabled']==bool(json.loads((ep/'frontal_bypass.json').read_text())['plan'].get('front_route_selected',False))
  rows.append(dict(front_cop_audit=fa,episode=ep.name,quality=a['quality'],pose=a['pose'],actual_review=b,tracking_action_audit=qa,continuity_audit=ca))
  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];scripts=list(base)
  if plan.get('initial_top_selected'):scripts+=['audit_y_path_clearance_live.py']
  if plan.get('front_route_selected'):scripts+=['audit_front_recovery_height_live.py','audit_recovery_and_anchor.py']
  if (ep/'contact_center_calibration.json').exists():scripts+=['audit_contact_center_live.py','audit_projected_support_live.py']
  needed.update((ep.name,s) for s in scripts)
cr=[x for x in control['rows'] if x['episode'] in expected];assert len(cr)==len(needed) and {(x['episode'],x['script']) for x in cr}==needed
for x in cr:
 ep=next(r.glob('case_*/'+x['episode']));name,keys=specs[x['script']];assert x['process_returncode']==0 and x['report_passed'] is True and sha(ep/name)==x['report_sha256'] and sha(ep/'raw.npz')==x['raw_sha256'] and sha(w/x['script'])==x['auditor_sha256'];v=json.loads((ep/name).read_text())
 if x.get('region_reference_auditor_sha256'):assert x['region_reference_auditor_sha256']==v['region_reference_auditor_sha256']==sha(w/'audit_region_reference_live.py')
 for k in keys:v=v[k]
 assert v is True
assert {x['episode'] for x in rows}==expected and len(waits)==1
passed=sum(x['quality']['passed'] and x['pose']['search_success'] for x in rows)
result=dict(group=group,push_passed=passed,push_total=len(expected),wait_passed=True,rows=rows,waits=waits,original_control_reports_verified=len(cr),tracking_action_reports_verified=len(rows),source_archives_per_case=len(protocol['source_sha256']),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False,admission='Diagnostic group only; no pilot/data/model approval. Complete original quality and actual sampled visual checks reported independently.')
(r/(group.upper()+'_RESULT.json')).write_text(json.dumps(result,indent=2));lines=[f'# {group}: {passed}/{len(expected)} 推动通过；等待通过','',result['admission'],'','|条件|推进mm|原任务+姿态|','|---|---:|---|']
for x in rows:lines.append(f"|{x['episode']}|{x['quality']['metrics']['target_final_progress_m']*1000:.3f}|{'通过' if x['quality']['passed'] and x['pose']['search_success'] else '失败'}|")
lines+=['',f'{len(cr)}原控制、{len(rows)}残差动作报告和每case {len(protocol["source_sha256"])}源码快照已核验；全部4条8RGB+4external和等待8RGB实际查看并绑定。原首零位、无助推保持。']
(r/(group.upper()+'_RESULT.md')).write_text('\n'.join(lines)+'\n');print({k:v for k,v in result.items() if k not in {'rows','waits'}})
