"""Read-only explain frozen micro-return audit failure; no gate/report rewrite."""
from pathlib import Path
import json,hashlib,datetime,math
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;R=W/'tilt05_groups_r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[];sources=[Path(__file__),R/'RESULT.json',W/'audit_micro_clearance_return.py',W/'tilt05_diagnostic_contract.py',W/'staged_box_inward_correction/front_top_route_micro.py',W/'staged_box_inward_correction/micro_clearance_return.py']
for f in R.glob('case_*/*/frontal_bypass.json'):
 data=json.loads(f.read_text());plan=data['plan']
 if not plan.get('front_route_selected'):continue
 ep=f.parent;key='box' if 'push_box' in ep.name else 'mailer';threshold=plan['contact_stability_candidate']['tilt_recontact_rad'];assert threshold==.05
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 mismatch=[]
 for row in data['rows']:
  e=row.get('direction_change_recontact')
  if e is None:continue
  t=row['step'];tilt=math.acos(float(np.clip(rot[t,2,2],-1,1)));old=tilt>.03;actual=tilt>.05
  assert e['tilt_precedence']==actual,(ep.name,t)
  if old!=actual:mismatch.append(dict(step=t,tilt_rad=tilt,auditor_hardcoded_guard=old,executed_configured_guard=actual,stage_changed=e['stage_changed'],previous_top_mode=e['previous_top_mode'],restarted=e['restarted'],micro_retained=e['micro_repair_retention']['retained']))
 rows.append(dict(episode=ep.name,configured_rad=threshold,mismatch_count=len(mismatch),mismatches=mismatch));sources.extend([f,ep/'parcel_orientation.npz'])
assert any(x['mismatch_count'] for x in rows)
text=(W/'staged_box_inward_correction/front_top_route_micro.py').read_text();helper=(W/'staged_box_inward_correction/micro_clearance_return.py').read_text()
assert 'tilt>self.tilt_recontact_rad' in text and 'tilted=tilt_guard' in text and 'not tilted' in helper
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,finding='The front direction-change guard and MicroClearanceReturn receive the same configured tilt_recontact_rad. Changing the runtime setting to0.05 also changes their guard. The frozen verifier still hardcodes0.03. Prior claim that micro-return guard stayed0.03 was incorrect.',audit_failure_retained=True,original_result_unchanged=True,formal_pose_gate_still_rad=.20,training_ready=False,next_decision='Use fully closed box_inward_groups_r1 original0.03 as next observer baseline; do not patch frozen audit to green or adopt0.05 as an improvement.',source_sha256={str(p):sha(p) for p in sources})
p=R/'MICRO_GUARD_SCOPE_CORRECTION.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps(rows,indent=2))
