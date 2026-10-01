"""Join recorded rear-box recovery selections to actual loaded push bouts.
Observational, final-substep force evidence. Selection is geometry dependent;
preferred/fallback differences are not randomized causal effects. No admission.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=w/'recontact_interior_groups_r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ex=json.loads((r/'CONTACT_EXIT_COMPARISON.json').read_text())
mom=json.loads((r/'INTERIOR_CONTACT_MOMENTS.json').read_text())
reports=[]
for episode in ex['episodes']:
 if 'push_box' not in episode['episode']:continue
 run=episode['run'];ep=w/run/'case_840001'/episode['episode']
 events=json.loads((ep/'recontact_pose.json').read_text())['rows']
 plans=[e for e in events if e.get('planning')];captures=[e for e in events if e['kind']=='handover']
 rows=json.loads((ep/'frontal_bypass.json').read_text())['rows'];by_step={x['step']:x for x in rows}
 moments=next(x['records'] for x in mom['episodes'] if x['run']==run)
 bouts=[]
 for bout in episode['bouts']:
  preceding=[e for e in captures if e['step']<bout['start']]
  cap=preceding[-1] if preceding else None
  plan=next((e for e in reversed(plans) if cap and e['step']<=cap['step']),None)
  selected=plan['planning'].get('interior_preference',{}).get('selected','original_parent') if plan else 'initial_region'
  recs=[x for x in moments if bout['start']<=x['step']<=bout['end']]
  b={k:bout[k] for k in ['start','end','exit_step','exit_reason','push_steps','loaded_steps','object_signed_y_progress_mm']}
  b.update(selection=selected,recovery_start_step=plan['step'] if plan else None,recovery_handover_step=cap['step'] if cap else None,recovery_ticks=cap['ticks'] if cap else None)
  b['actual_exit_observation']={k:by_step[bout['exit_step']].get(k) for k in ['observed_parcel_tilt_rad','contact_load','last_recontact_reason']}
  b['last_loaded']=bout['last_loaded']
  b['last_eight_loaded_force_samples']=recs[-8:]
  if recs:b.update(normal_load_median_n=float(np.median([x['hand_normal_load_n'] for x in recs])),normal_load_max_n=max(x['hand_normal_load_n'] for x in recs),normal_point_moment_median_abs_xy_nm=np.median(np.abs([x['normal_point_moment_local_nm'][:2] for x in recs]),axis=0).tolist())
  bouts.append(b)
 reports.append(dict(run=run,episode=episode['episode'],bouts=bouts,unfinished_push_steps=episode['unfinished_push_steps'],source_sha256={n:sha(ep/n) for n in ['recontact_pose.json','frontal_bypass.json']}))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=reports,source_sha256={n:sha(r/n) for n in ['CONTACT_EXIT_COMPARISON.json','INTERIOR_CONTACT_MOMENTS.json']},script_sha256=sha(Path(__file__)),training_ready=False)
(r/'INTERIOR_BOUT_PRESSURE.json').write_text(json.dumps(out,indent=2))
for e in reports:
 print(e['run'])
 for b in e['bouts']:print({k:b.get(k) for k in ['start','selection','recovery_ticks','push_steps','object_signed_y_progress_mm','exit_reason','normal_load_median_n','normal_load_max_n']})
