"""Matched descriptive comparison; not a deterministic causal claim or admission."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;run=root/'normal_contact_groups_r1';parent=root/'terminal_hold_front09_groups_r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 old=parent/ep.parent.name/ep.name
 def summary(p):
  q=json.loads((p/'quality.json').read_text());c=json.loads((p/'CONTACT_STABILITY_CONTROL_AUDIT.json').read_text());pose=json.loads((p.parent/'POSE_AND_MOTION_REVIEW.json').read_text())
  hold=json.loads((p/'TERMINAL_HOLD_LIVE_AUDIT.json').read_text())
  return dict(task_pass=q['passed'],reasons=q['reasons'],progress_m=q['metrics']['target_final_progress_m'],other_max_xy_m=q['metrics']['mailer_max_xy_m' if 'push_box' in p.name else 'box_max_xy_m'],recontacts=len(c['recontact_events']),max_tilt_deg=c['max_tilt_deg'],release=c['release'],raw_sha256=sha(p/'raw.npz'))
 if not (ep/'CONTACT_STABILITY_CONTROL_AUDIT.json').exists() or not (ep.parent/'POSE_AND_MOTION_REVIEW.json').exists():continue
 a=summary(old);b=summary(ep);rows.append(dict(episode=ep.name,parent=a,current=b,progress_change_m=b['progress_m']-a['progress_m'],pass_changed=a['task_pass']!=b['task_pass']))
report=dict(completed_conditions=len(rows),planned_conditions=12,parent_task_pass_on_completed=sum(x['parent']['task_pass'] for x in rows),current_task_pass_on_completed=sum(x['current']['task_pass'] for x in rows),rows=rows,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),current_protocol_sha256=sha(run/'PROTOCOL.json'),scope='Matched layout/task seed0 original task decisions and observed control metrics. Original full pose/visual/group checks separate. Simulation can diverge despite identical initial states; single-seed comparison is not proof of isolated causal benefit or repeatability. No training admission.',training_ready=False)
(run/'PARENT_COMPARISON.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
