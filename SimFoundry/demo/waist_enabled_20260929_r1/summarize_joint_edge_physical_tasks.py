"""Complete10-condition task/pose/visual comparison, not full audit closure.
Keep all original task failures; supplemental control audits remain separate.
"""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;R=W/'joint_edge_intersection_physical_r1';B=W/'fresh_closed_peak_trials_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();protocol=json.loads((R/'PROTOCOL.json').read_text());records=[];sources={str(R/'PROTOCOL.json'):sha(R/'PROTOCOL.json')}
for item in protocol['plan']['commands']:
 for task in item['tasks']:
  ep=R/f"case_{item['layout_id']}"/f"layout_{item['layout_id']}_{task}";baseline=B/f"case_{item['layout_id']}"/ep.name;quality=json.loads((ep/'quality.json').read_text());old=json.loads((baseline/'quality.json').read_text());review=json.loads((ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json').read_text());visual=json.loads((ep/'ACTUAL_REVIEW_BINDING.json').read_text());assert visual['raw_sha256']==review['raw_sha256']==sha(ep/'raw.npz') and visual['numeric_review_sha256']==sha(ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json') and visual['review_sheet_sha256']==sha(ep/'JOINT_EDGE_REVIEW.jpg');assert visual['actual_visual_review'].startswith('completed_actual_view')
  row=dict(group=item['group'],episode=ep.name,wait=item['wait'],baseline_task_passed=old['passed'],baseline_frames=old['frames'],candidate_task_passed=quality['passed'],candidate_frames=quality['frames'],recomputed_task_and_pose_passed=review['original_task_and_pose_passed'],actual_visual_review=visual['actual_visual_review'],training_ready=False)
  if not item['wait']:
   coord=json.loads((ep/'coordination.json').read_text());changed=[c['step'] for c in coord if c.get('joint_edge_clearance_intersection',{}).get('changed')];row.update(progress_mm=review['progress_mm'],final10_signed_y_min_mm=review['final10_signed_y_min_mm'],non_target_max_xy_mm=review['non_target_max_xy_mm'],repair_steps=changed,repair_count=len(changed),baseline_progress_mm=old['metrics']['target_final_progress_m']*1000)
  records.append(row)
  for p in [ep/'quality.json',baseline/'quality.json',ep/'JOINT_EDGE_STAGE_NUMERIC_REVIEW.json',ep/'ACTUAL_REVIEW_BINDING.json']+([] if item['wait'] else [ep/'coordination.json']):sources[str(p)]=sha(p)
assert len(records)==10
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,conditions=10,push_passed=sum(r['candidate_task_passed'] for r in records if not r['wait']),push_total=8,wait_passed=sum(r['candidate_task_passed'] for r in records if r['wait']),wait_total=2,baseline_push_passed=sum(r['baseline_task_passed'] for r in records if not r['wait']),rows=records,source_sha256=sources,summarizer_sha256=sha(__file__),full_control_closure_pending=True,training_ready=False,model_goal_achieved=False)
with (R/'TASK_POSE_VISUAL_COMPARISON.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
