# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Freeze new full diagnostic only after complete reviewed parent evidence."""
from pathlib import Path
import json,hashlib,datetime,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'region_causal_response_groups_r1';stage=w/'staged_region_causal_xy_response';r=Path(sys.argv[1]).resolve();assert not r.exists();xrun=w/'region_causal_response_groups_r1';assert (xrun/'RESULT.json').exists();xs=json.loads((xrun/'STATUS.json').read_text());xr=json.loads((xrun/'RESULT.json').read_text());assert xr['push_total']==8 and xr['waits_passed']==2 and xr['actual_review_complete'];assert not (Path('/proc')/str(xs['pid'])/'cmdline').exists();result=json.loads((parent/'RESULT.json').read_text());assert result['push_total']==8 and result['actual_review_complete'] and result['waits_passed']==2
for file in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json']:
 d=json.loads((parent/file).read_text());assert not (Path('/proc')/str(d['pid'])/'cmdline').exists()
manifest=json.loads((stage/'MANIFEST.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for f,h in manifest['source_sha256'].items():assert sha(stage/f)==h
for f,h in manifest['checks_sha256'].items():assert sha(stage/f)==h
p=json.loads((parent/'PROTOCOL.json').read_text());oldstage=str((w/'staged_region_causal_response').relative_to(repo));newstage=str(stage.relative_to(repo));sources={}
for rel,h in p['source_sha256'].items():
 nr=rel.replace(oldstage,newstage);sources[nr]=sha(repo/nr)
 if nr==rel:assert sources[nr]==h
for name in ['front_cop_route.py','contact_slip_following.py','causal_unloaded_response.py','causal_response_parameters.json']:sources[str((stage/name).relative_to(repo))]=sha(stage/name)
assert len(sources)==53
r.mkdir();(r/'layouts').mkdir()
layouts={}
for old,h in p['layout_sha256'].items():
 src=Path(old);assert sha(src)==h;dst=r/'layouts'/src.name;dst.write_bytes(src.read_bytes());layouts[str(dst)]=h
for item in p['commands']:item['args']=[x.replace(str(parent),str(r)) for x in item['args']]+['--region-causal-xy-response']
p['settings']=p['settings']+['--region-causal-xy-response']
# Run the two diagnosed cases first, retaining every original task and both waits.
p['parent_case_order']=[item['layout_id'] for item in p['commands']]
by_id={item['layout_id']:item for item in p['commands']};order=[840001,840004,840000,841000,840005,841002]
assert set(order)==set(by_id) and len(order)==len(p['commands'])==6
p['commands']=[by_id[i] for i in order]
p['case_order_reason']='Diagnosed swapped lateral and normal diagonal first for earlier feedback; all original8push+2wait retained without task/geometry/seed/step changes.'
p.update(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=str(stage/'collect_paired_sorting.py'),source_sha256=sources,layout_sha256=layouts,auditor_dependency_sha256={n:sha(w/n) for n in ['audit_region_causal_xy_continuity_live.py','audit_region_causal_xy_live.py','audit_region_reference_live.py','audit_terminal_hold_inputs.py','audit_initial_near_half_live.py','audit_tracking_region_action_live.py','audit_region_action_live_r2.py']},runner_sha256=sha(w/'run_region_causal_xy_groups.py'),audit_sha256=sha(w/'audit_front_cop_route_axis_live.py'),continuity_base_auditor_sha256=sha(w/'audit_region_causal_xy_continuity_live.py'),causal_base_auditor_sha256=sha(w/'audit_region_causal_xy_live.py'),parent_result_sha256=sha(parent/'RESULT.json'),parent_protocol_sha256=sha(parent/'PROTOCOL.json'),candidate_manifest_sha256=sha(stage/'MANIFEST.json'),scope='Same original8push2wait causal-response parent. Only new region-causal-xy-response flag: relax measured-space XY displacement and fully compensate affine XY offset when core interior not reached. Original height/inactive-palm objectives, geometry/core10mm, bounds, guards, steps, front paths, cameras and complete groups unchanged. Diagnostic only; no admission',parent_causal_response_result_sha256=sha(xrun/'RESULT.json'),training_ready=False)
# Freeze all invoked checks and watcher implementations as well as control dependencies.
for name in ['audit_contacts.py','review_diagnostics.py','audit_normal_wait.py','render_episode_frames.py','watch_tracking_region_controls.py','watch_region_failures.py','diagnose_region_physics.py','audit_contact_normal_live.py','audit_terminal_hold_live.py','audit_contact_stability_control.py','audit_contact_bout_yaw_live.py','audit_bounded_top_lead_live.py','audit_clearance_feedback_live.py','audit_initial_top_recovery_live.py','audit_y_path_clearance_live.py','audit_front_recovery_height_live.py','audit_recovery_and_anchor.py','audit_contact_center_live.py','audit_projected_support_live.py']:
 p['auditor_dependency_sha256'][name]=sha(w/name)
assert sha(w/'audit_front_cop_route_axis_live.py')==manifest['auditor_sha256']
(r/'PROTOCOL.json').write_text(json.dumps(p,indent=2));print(json.dumps(dict(path=str(r),sources=len(sources),cases=len(p['commands']),protocol_sha256=sha(r/'PROTOCOL.json'))))
