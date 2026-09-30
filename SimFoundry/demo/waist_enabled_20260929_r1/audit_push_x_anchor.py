"""Validate the recorded within-push world-X latch and command slew."""
from pathlib import Path
import json,sys
run=Path(sys.argv[1]).resolve();assert json.loads((run/'STATUS.json').read_text())['stage']=='numeric_complete_actual_visual_review_pending';rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
 d=json.loads((ep/'frontal_bypass.json').read_text());assert d['plan']['top_recontact']['hold_push_x'];segments=[]
 for r in d['rows']:
  if r['mode']!='top_push':continue
  if not segments or r['step']!=segments[-1][-1]['step']+1:segments.append([])
  segments[-1].append(r)
 summaries=[]
 for seg in segments:
  first=seg[0];anchor=first['push_x_anchor_m'];expected=first['parcel_top_xyz'][0]+first['approach_xy_bias_m'][0];errors=[]
  for before,after in zip(seg,seg[1:]):
   bias=(after.get('cross_axis_admittance') or {}).get('command_bias_x_m',0.);predicted=before['target_xyz'][0]+max(-.002,min(.002,anchor+bias-before['target_xyz'][0]));errors.append(abs(after['target_xyz'][0]-predicted))
  summaries.append(dict(first_step=first['step'],last_step=seg[-1]['step'],anchor_m=anchor,initial_latch_error_m=abs(anchor-expected),max_anchor_change_m=max(abs(r['push_x_anchor_m']-anchor) for r in seg),max_x_slew_replay_error_m=max(errors,default=0.),object_x_change_m=seg[-1]['observed_target'][0]-first['observed_target'][0]))
 bad_reset=[r['step'] for i,r in enumerate(d['rows']) if i and r.get('recontacts',0)>d['rows'][i-1].get('recontacts',0) and r['push_x_anchor_m'] is not None]
 passed=bool(summaries and not bad_reset and all(max(s['initial_latch_error_m'],s['max_anchor_change_m'],s['max_x_slew_replay_error_m'])<1e-9 for s in summaries));rows.append(dict(episode=ep.name,passed=passed,segments=summaries,uncleared_recontact_steps=bad_reset));print(ep.name,passed,summaries)
(run/'PUSH_X_ANCHOR_AUDIT.json').write_text(json.dumps(dict(rows=rows,passed=len(rows)==2 and all(r['passed'] for r in rows),scope='Recorded command reference latch/slew/reset consistency, including separately logged bounded cross-axis bias when enabled, separate from actual rigid-hand/object tracking and force. Does not prove improved task success or causal attribution.',training_ready=False),indent=2))
if not all(r['passed'] for r in rows):raise SystemExit(1)
