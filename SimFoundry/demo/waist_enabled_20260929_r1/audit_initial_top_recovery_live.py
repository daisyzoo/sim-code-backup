"""Independently check initial/recovery/guard heights on recorded initial-top rows."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('episode',type=Path);p.add_argument('--expected-height',type=float,default=.86);p.add_argument('--out',type=Path);a=p.parse_args();ep=a.episode
assert .84<=a.expected_height<=.91
log=json.loads((ep/'frontal_bypass.json').read_text());controls={x['step']:x for x in json.loads((ep/'expert_control.json').read_text())};errors=[];count=0;startz=None;guardz=None;normal_rows=0;recovery_rows=0
for r in log['rows']:
 if not r.get('initial_top_selected'):continue
 t=r['step'];mode=r['mode'];tip=r['observed_support_xyz'];goal=r['target_xyz'];control=controls[t]
 if max(abs(float(goal[i])-float(control['target_xyz'][i])) for i in range(3))>2e-6:errors.append(dict(step=t,kind='expert_mapping'))
 if mode=='initial_top_guard_lift':
  if guardz is None:guardz=max(.91,tip[2])
  if abs(goal[2]-guardz)>2e-6:errors.append(dict(step=t,kind='guard_lift_height'))
  continue
 rc=r['recontacts'];height=a.expected_height if rc else .91
 if rc>count or startz is None:startz=tip[2]
 if rc<count:errors.append(dict(step=t,kind='recontact_count_decreased'))
 count=rc
 if abs(r['travel_height_m']-height)>1e-9:errors.append(dict(step=t,kind='recovery_height',recorded=r['travel_height_m'],expected=height))
 if mode=='top_lift' and abs(goal[2]-max(height,startz))>2e-6:errors.append(dict(step=t,kind='lift_waypoint_height'))
 if mode=='top_cross' and abs(goal[2]-height)>2e-6:errors.append(dict(step=t,kind='cross_waypoint_height'))
 if mode=='top_release' and goal[2]<.91-2e-6:errors.append(dict(step=t,kind='release_lowered'))
 normal_rows+=1;recovery_rows+=int(rc>0)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=dict(passed=not errors,errors=errors,expected_recovery_height_m=a.expected_height,normal_rows=normal_rows,recovery_rows=recovery_rows,recontacts=count,raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),scope='Actual initial-top recorded initial approach.91/recoveryconfigured/outer guard.91 and mapped expert waypoints. Separate from dynamics, original task/pose and visual admission.',training_ready=False)
(a.out or ep/'INITIAL_TOP_RECOVERY_LIVE_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['errors']}));raise SystemExit(0 if out['passed'] else 1)
