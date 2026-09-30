"""Contact/load/command progression during top push, no admission decision."""
from pathlib import Path
import json,sys,math
run=Path(sys.argv[1]);assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';actor='parcel_box' if side=='right' else 'mailer';direction=-1 if side=='right' else 1;cmd=json.loads((ep/'frontal_bypass.json').read_text())['rows'];push={r['step']:r for r in cmd if r['mode']=='top_push'};series=[]
 for rr in json.loads((ep/'solved_contact_forces.json').read_text())['rows']:
  t=rr['after_action_step']
  if t not in push:continue
  row=push[t];hand=[c for c in rr['parcel_contacts'] if any(side+'_wrist_roll' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes'])];table=[c for c in rr['parcel_contacts'] if any('/table/' in s for s in c['shapes']) and any('/'+actor+'/' in s for s in c['shapes'])]
  series.append(dict(step=t,hand_abs_y_force_N=sum(abs(c['force_world_N'][1]) for c in hand),hand_abs_z_force_N=sum(abs(c['force_world_N'][2]) for c in hand),table_abs_z_force_N=sum(abs(c['force_world_N'][2]) for c in table),hand_mu=sorted(set(c['friction'][0] for c in hand)),table_mu=sorted(set(c['friction'][0] for c in table)),command_y=row['target_xyz'][1],observed_support_y=row['observed_support_xyz'][1],target_y=row['observed_target'][1]))
 segments=[]
 for sample in series:
  if not segments or sample['step']!=segments[-1][-1]['step']+1:segments.append([])
  segments[-1].append(sample)
 segment_summaries=[dict(first_step=ss[0]['step'],last_step=ss[-1]['step'],frames=len(ss),target_progress_m=direction*(ss[-1]['target_y']-ss[0]['target_y']),command_travel_m=direction*(ss[-1]['command_y']-ss[0]['command_y'])) for ss in segments]
 item=dict(episode=ep.name,push_frames=len(series),continuous_push_segments=segment_summaries,series=series)
 if series:
  first,last=series[0],series[-1];item.update(first_to_last_push_target_change_m=direction*(last['target_y']-first['target_y']),first_to_last_push_command_change_m=direction*(last['command_y']-first['command_y']),last_hand_abs_y_force_N=last['hand_abs_y_force_N'],last_hand_abs_z_force_N=last['hand_abs_z_force_N'])
 rows.append(item);print({k:v for k,v in item.items() if k!='series'})
(run/'TANGENTIAL_DRIVE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Per-sample sum of absolute force components for contacts on specified pair, not signed net forces or impulses; recorded pre-action command and post-action last-tick forces. Mu is actual contact buffer sliding coefficient. First-to-last changes may span lift/reacquire gaps and are not per-contact displacement; use continuous_push_segments. No change to material/physics.',training_ready=False),indent=2))
