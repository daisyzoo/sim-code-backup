"""Independent recorded hold state machine and command/physical drift audit."""
from pathlib import Path
from collections import deque
import json,sys,hashlib
import numpy as np
p=Path(sys.argv[1]);sha=lambda f:hashlib.sha256((p/f).read_bytes()).hexdigest()
rows=json.loads((p/'terminal_joint_hold.json').read_text())['rows']
with np.load(p/'raw.npz') as z:q=z['q'];a=z['action']
with np.load(p/'trace.npz') as z:tr={k:z[k] for k in z.files}
control={x['step']:x for x in json.loads((p/'expert_control.json').read_text())}
coord={x['step']:x for x in json.loads((p/'coordination.json').read_text())}
from rear_tracking_inputs import verify_inputs
w=Path(__file__).resolve().parent;recovery=verify_inputs(p,w.parents[1],w/'staged_rear_recovery_tracking')
control={t:recovery.parent_expert(t,x) for t,x in control.items()}
key='box' if 'push_box' in p.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
errors=[];count=0;command=None;held=[];releases=[];other_max=np.maximum.accumulate(np.linalg.norm(tr[other][:,:2]-tr[other][0,:2],axis=1))
assert [x['step'] for x in rows]==list(range(1,len(q))), 'Missing/duplicate hold observations'
for r in rows:
 t=r['step'];window=tr[key][max(0,t-9):t+1]
 confirmed=(len(window)==10 and direction*(tr[key][t,1]-tr[key][0,1])>=.15 and (direction*window[:,1]>=.20).all() and np.linalg.norm(window[-1,:2]-window[0,:2])<=.01)
 if bool(confirmed)!=r['target_confirmed']:errors.append([t,'original_target_confirmation'])
 if r['mode']!=control[t]['mode']:errors.append([t,'mode'])
 if abs(other_max[t]-r['other_max_xy_m'])>1e-7:errors.append([t,'other_max'])
 if np.max(abs(q[t,12:23]-r['current_upper_q']))>1e-7 or np.max(abs(a[t-1,12:23]-r['previous_upper_command']))>1e-7:errors.append([t,'measured_q_previous_action'])
 tracking=command if command is not None else a[t-1,12:23]
 valid=(r['mode'] in ('goal_release','top_release','bypass_release') and confirmed and r['hand_clearance_m']>=.02 and abs(r['load_n'])<.2 and r['active_error_m']<=.012 and r['inactive_error_m']<=.015 and 0<=other_max[t]<=.015 and np.max(abs(q[t,12:23]-tracking))<=.015)
 if command is not None:
  if not valid:command=None;count=0;releases.append(t)
 else:
  count=count+1 if valid else 0
  if count>=5:command=a[t-1,12:23].copy()
 expected=command is not None
 if r['held']!=expected or r['consecutive_ready']!=count or coord[t]['terminal_joint_hold']!=expected:errors.append([t,'hold_state_or_counter'])
 if expected:
  held.append(t)
  if np.max(abs(a[t,12:23]-command))>1e-7 or np.max(abs(np.asarray(r['output_upper_command'])-command))>1e-7:errors.append([t,'held_output_changed'])
segments=[]
for chunk in np.split(np.array(held,dtype=int),np.flatnonzero(np.diff(held)>1)+1):
 if not len(chunk):continue
 start,end=int(chunk[0]),int(chunk[-1]);sl=slice(start,end+1)
 segments.append(dict(start=start,end=end,frames=len(chunk),max_action_range_rad=float(np.ptp(a[sl,12:23],axis=0).max()),max_q_range_rad=float(np.ptp(q[sl,12:23],axis=0).max()),waist_q_range_rad=float(np.ptp(q[sl,12])),left_palm_max_axis_range_m=float(np.ptp(tr['palm_left'][sl],axis=0).max()),right_palm_max_axis_range_m=float(np.ptp(tr['palm_right'][sl],axis=0).max()),target_max_xy_from_hold_m=float(np.linalg.norm(tr[key][sl,:2]-tr[key][start,:2],axis=1).max())))
out=dict(recorded_hold_checks_passed=not errors,errors=errors,held_frames=len(held),segments=segments,revocation_frames=releases,source_sha256={f:sha(f) for f in ('raw.npz','trace.npz','terminal_joint_hold.json','expert_control.json','coordination.json')},scope='Independent original target/other motion, q/action binding, readiness counters, revocation and exact held output; reports physically measured joint/palm/target variation. Clearance/load/error inputs here are recorded readings, not independent full geometry/force certification. Separate original quality/pose, force, mesh and actual visual audits remain required. Does not add original task gates.',training_ready=False)
recovery.assert_unchanged()
(p/'REAR_TRACKING_TERMINAL_HOLD_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
