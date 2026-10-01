"""Compare complete diagnostics with exact previous geometry/task, no admission."""
from pathlib import Path
import json,hashlib
w=Path(__file__).resolve().parent;run=w/'y_path_nearhalf_groups_r1'
pairs={897002:('initial_near_contact_depth_r1',890002),897003:('initial_near_contact_depth_r1',890003),897000:('current_lateral_profile_r1',895000),897001:('current_lateral_profile_r1',895001)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def summarize(ep):
 q=json.loads((ep/'quality.json').read_text());assert q['frames']==1200
 f=json.loads((ep/'frontal_bypass.json').read_text());rows=f['rows'];review=ep/'EARLY_REVIEW.json'
 a=json.loads(review.read_text()) if review.exists() else None
 target='box' if 'push_box' in ep.name else 'mailer';other='mailer' if target=='box' else 'box'
 guards=[r for r in rows if 'guard' in r['mode'] or r.get('route_stop_reason') or r.get('stop_reason')]
 result=dict(episode=ep.name,task_passed=q['passed'],progress_m=q['metrics']['target_final_progress_m'],non_target_max_xy_m=q['metrics'][other+'_max_xy_m'],max_recontacts=max(r.get('recontacts',0) for r in rows),first_guard_step=guards[0]['step'] if guards else None,first_guard=guards[0] if guards else None,first_release_step=next((r['step'] for r in rows if 'release' in r['mode']),None),final_mode=rows[-1]['mode'],quality_sha256=sha(ep/'quality.json'),frontal_sha256=sha(ep/'frontal_bypass.json'),pose=None,actual_sampled_visual_review='pending')
 if a:
  assert a['raw_sha256']==sha(ep/'raw.npz')
  result.update(pose=a['pose'],actual_sampled_visual_review=a['actual_sampled_visual_review'],review_sheet_sha256=a['review_sheet_sha256'])
 return result
out=[]
for new_id,(old_run,old_id) in pairs.items():
 for task in ['push_box_to_bin','nudge_mailer_to_bin']:
  ep=run/f'case_{new_id}/layout_{new_id}_{task}';old=w/old_run/f'case_{old_id}/layout_{old_id}_{task}'
  if not (ep/'quality.json').exists():continue
  new_layout=json.loads((ep.parent/'explicit_layout.json').read_text());old_layout=json.loads((old.parent/'explicit_layout.json').read_text())
  for field in ['box_xyz','mailer_xyz','box_yaw','mailer_yaw','assignment']:assert new_layout[field]==old_layout[field],field
  new=summarize(ep);prior=summarize(old);out.append(dict(current=new,prior=prior,progress_delta_m=new['progress_m']-prior['progress_m']))
report=dict(complete_episodes=len(out),expected_episodes=8,rows=out,scope='Two explicit changes, NOT single-variable attribution: remaining-Y clearance logic and near fraction.5. Quality/pose/actual image bindings reported separately. Incomplete rows omitted, never counted as success. Raw SHA rechecked for completed visual reports. No data admission.',training_ready=False)
(run/'PARENT_COMPARISON.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(complete_episodes=len(out),rows=[dict(episode=r['current']['episode'],task_passed=r['current']['task_passed'],progress_m=r['current']['progress_m'],delta_m=r['progress_delta_m'],first_guard=r['current']['first_guard_step']) for r in out]),indent=2))
