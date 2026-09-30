"""Summarize actual last-tick hand contacts, separate from geometric proxies."""
from pathlib import Path
import json,sys,math
run=Path(sys.argv[1]);assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending'
assert '--trace-hand-contact-forces' in json.loads((run/'PROTOCOL.json').read_text())['settings'], 'Hand force collection not enabled'
rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 side='right' if 'push_box' in ep.name else 'left';log=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];modes={r['step']:r['mode'] for r in json.loads((ep/'frontal_bypass.json').read_text())['rows']};pairs={}
 assert all(r['solver_force_buffer_unchanged'] for r in log)
 for rr in log:
  t=rr['after_action_step']
  if 'hand_contacts' not in rr:raise ValueError('Hand contacts were not recorded')
  for c in rr['hand_contacts']:
   if not any(side+'_wrist_roll_rubber_hand' in n for n in c['shapes']):continue
   other=' | '.join(n for n in c['shapes'] if side+'_wrist_roll_rubber_hand' not in n)
   force=math.sqrt(sum(x*x for x in c['force_world_N']));p=pairs.setdefault(other,dict(max_force_N=0.,min_distance_m=0.,samples_above_half_N=[],max_force_sample=None))
   if force>p['max_force_N']:p['max_force_N']=force;p['max_force_sample']=dict(step=t,phase=modes.get(t,'initial'),distance_m=c['distance_m'],world=c['position_world'])
   p['min_distance_m']=min(p['min_distance_m'],c['distance_m'])
   if force>.5:p['samples_above_half_N'].append(dict(step=t,phase=modes.get(t,'initial'),force_N=force,distance_m=c['distance_m']))
 for p in pairs.values():
  samples=p['samples_above_half_N'];p['frames_above_half_N']=len(set(c['step'] for c in samples));p['phases_above_half_N']=sorted(set(c['phase'] for c in samples))
 rows.append(dict(episode=ep.name,active_hand=side,pairs=pairs));print(ep.name,[(k,round(v['max_force_N'],4),v['frames_above_half_N'],v['phases_above_half_N']) for k,v in pairs.items()])
(run/'HAND_FORCE_AUDIT.json').write_text(json.dumps(dict(rows=rows,scope='Actual solver last physics tick after each action, active-hand contacts only. Force peak and sampled contact distance are not integrated impulse/full-substep collision certification. Observer verified solver force buffer unchanged.',training_ready=False),indent=2))
