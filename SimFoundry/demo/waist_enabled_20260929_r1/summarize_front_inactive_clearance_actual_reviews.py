"""Bind complete numeric results only after ten actual human/model image reviews.
Does not generate a visual judgment, replace control audits, or admit training.
"""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;R=W/'front_inactive_clearance_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((R/'PROTOCOL.json').read_text());status=json.loads((R/'STATUS.json').read_text());assert status['completed_conditions']==10 and status['status']=='collection_complete_audits_visual_pending'
rows=[];sources={str(R/'PROTOCOL.json'):sha(R/'PROTOCOL.json'),str(Path(__file__)):sha(__file__)}
for c in protocol['plan']['commands']:
 for task in c['tasks']:
  ep=R/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}";ready=json.loads((ep/'READY_FOR_AUDIT.json').read_text());short=ready['executed_frames']<ready['requested_frames'];p=ep/('FRONT_INACTIVE_CLEARANCE_INCOMPLETE_REVIEW.json' if short else 'FRONT_INACTIVE_CLEARANCE_V1_STAGE_NUMERIC_REVIEW.json');v=ep/'ACTUAL_REVIEW_BINDING.json';n=json.loads(p.read_text());a=json.loads(v.read_text());ready=json.loads((ep/'READY_FOR_AUDIT.json').read_text())
  assert n['frames']==ready['executed_frames'] and a['actual_visual_review'].startswith('completed_actual_view')
  if short:assert n['short_attempt_cannot_pass'] and not n['original_task_and_pose_passed']
  assert a['numeric_review_sha256']==sha(p) and a['raw_sha256']==n['raw_sha256']==sha(ep/'raw.npz')
  assert a['review_sheet_sha256']==n['review_sheet_sha256']==sha(ep/('FRONT_INACTIVE_CLEARANCE_INCOMPLETE_REVIEW.jpg' if short else 'FRONT_INACTIVE_CLEARANCE_REVIEW.jpg'))
  for k in ['sampled_rgb_frames','sampled_viewer_frames','external_source_sha256']:assert a[k]==n[k]
  for f,h in ready['source_sha256'].items():assert sha(f)==h
  for f,h in a['external_source_sha256'].items():assert sha(ep.parent/('viewer_'+ep.name)/f)==h
  rows.append(dict(episode=ep.name,group=c['group'],wait=c['wait'],frames=n['frames'],original_task_and_pose_passed=n['original_task_and_pose_passed'],metrics=n['recomputed_quality']['metrics'],actual_visual_review=a['actual_visual_review'],training_ready=False))
  for f in [p,v,ep/'raw.npz',ep/'READY_FOR_AUDIT.json',ep/('FRONT_INACTIVE_CLEARANCE_INCOMPLETE_REVIEW.jpg' if short else 'FRONT_INACTIVE_CLEARANCE_REVIEW.jpg')]:sources[str(f)]=sha(f)
assert len(rows)==10 and sum(x['wait'] for x in rows)==2
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,actual_reviews=len(rows),push_passed=sum(x['original_task_and_pose_passed'] for x in rows if not x['wait']),push_total=8,wait_passed=sum(x['original_task_and_pose_passed'] for x in rows if x['wait']),wait_total=2,source_sha256=sources,training_ready=False,model_goal_achieved=False)
with (R/'NUMERIC_VISUAL_SUMMARY.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['rows','source_sha256','scope']},indent=2))
