"""Offline continuous-bout measured-row comparison; old trajectories are not candidate rollouts.
V1 did not validate the stored previous command at mode transitions; this version
excludes those contexts and independently reproduces the original Y command first."""
from pathlib import Path
import json,hashlib,datetime,copy,math
from terminal_directional_lead_candidate import propose
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[];count=0;changed=0
for root in ['fresh_closed_peak_trials_r1','terminal_margin_physical_r1']:
 for ep in sorted((W/root).glob('case_*/layout_*')):
  f=ep/'frontal_bypass.json'
  if not f.exists() or not (ep/'quality.json').exists():continue
  data=json.loads(f.read_text());direction=data['plan']['direction'];stats=dict(episode=str(ep),tested=0,changed=0,excluded_transition_rows=0,first_changed_step=None,history_sha256=sha(f))
  for row in data['rows']:
   parent=row.get('clearance_feedback')
   if not parent or not parent.get('eligible'):continue
   previous_row=data['rows'][row['step']-2] if row['step']>1 else None
   if previous_row is None or previous_row['mode']!='top_push' or not previous_row.get('clearance_feedback',{}):stats['excluded_transition_rows']+=1;continue
   assert row['mode']=='top_push';target=row['observed_target'][1];tip=row['observed_support_xyz'][1]
   # Actual previous command is recorded in the preceding controller row.
   previous=data['rows'][row['step']-2]['target_xyz'][1] if row['step']>1 else tip
   step=.003
   original_expected=previous+max(-step,min(step,parent['desired_support_xy'][1]-previous))
   assert abs(original_expected-parent['command_xy'][1])<1e-12,(str(ep),row['step'],'previous command mismatch')
   original=copy.deepcopy(parent)
   assert propose(parent,enabled=False,direction=direction,target_y=target,tip_y=tip,previous_y=previous,step_m=step) is parent
   new=propose(parent,enabled=True,direction=direction,target_y=target,tip_y=tip,previous_y=previous,step_m=step)
   assert parent==original
   gap=direction*(parent['object_goal_xy'][1]-target);should_change=parent['stage']=='lateral_y' and 0<gap<step
   assert ('terminal_directional_lead_floor' in new)==should_change
   if should_change:
    # Independent scalar arithmetic; preserve X, goal and metadata except declared Y fields.
    desired=tip+direction*step;delta=desired-previous;cmd=previous+(-step if delta < -step else step if delta > step else delta)
    assert new['desired_support_xy'][1]==desired and new['command_xy'][1]==cmd
    assert abs(cmd-previous)<=step+1e-15 and abs(desired-tip)<=.012
    restored=copy.deepcopy(new);del restored['terminal_directional_lead_floor'];restored['desired_support_xy'][1]=parent['desired_support_xy'][1];restored['command_xy'][1]=parent['command_xy'][1];assert restored==parent
    stats['changed']+=1;stats['first_changed_step']=stats['first_changed_step'] or row['step'];changed+=1
   else:assert new==parent
   count+=1;stats['tested']+=1
  if stats['tested']:rows.append(stats)
assert count>1000 and changed>0
# Exact threshold and route boundaries, both instruction directions.
boundaries=0
for direction in [-1,1]:
 for gap in [-.001,0.,.001,.003,.004]:
  for stage in ['lateral_y','clearance_x']:
   p=dict(eligible=True,stage=stage,object_goal_xy=[.5,0.],desired_support_xy=[.5,direction*gap],command_xy=[.5,0.]);n=propose(p,enabled=True,direction=direction,target_y=-direction*gap,tip_y=0.,previous_y=0.,step_m=.003)
   assert ('terminal_directional_lead_floor' in n)==(stage=='lateral_y' and 0<gap<.003);boundaries+=1
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,tested_rows=count,changed_history_rows=changed,rows=rows,boundary_cases=boundaries,default_off_identical=True,simulation_started=False,collector_integrated=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'terminal_directional_lead_candidate.py']})
p=W/'TERMINAL_DIRECTIONAL_LEAD_CANDIDATE_CHECK_V2.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('passed',count,'historical rows;',changed,'changed;',boundaries,'boundaries; no physics')
