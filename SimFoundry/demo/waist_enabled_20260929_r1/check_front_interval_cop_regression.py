"""Verify isolated COP auditor preserves original results with interval off.
Actual old input streams are used; this does not certify enabled future dynamics.
"""
from pathlib import Path
import json,sys,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from audit_front_diagonal_entry_live import reconstruct as old
from audit_front_interval_diagonal_live import reconstruct as new
from front_interval_stage_source_binding import verify_trial_provenance
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
check=json.loads((W/'FRONT_INTERVAL_INDEPENDENT_ENABLED_CHECK.json').read_text());rows=[];bindings={}
for item in check['episodes']:
 ep=W/item['episode'];f=json.loads((ep/'frontal_bypass.json').read_text())
 with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};args=(f['rows'],f['plan'],tr,ori,packets,'box' if 'push_box' in ep.name else 'mailer');a=old(*args);b=new(*args);assert a==b;assert not a[1],(ep.name,a[1][:3]);rows.append(dict(episode=item['episode'],frames=len(f['rows']),loaded_steps=len(a[0]),identical=True));print(json.dumps(rows[-1]),flush=True)
 for name in ['frontal_bypass.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:bindings[str(ep/name)]=sha(ep/name)
try:verify_trial_provenance(W/'joint_edge_intersection_physical_r1/case_840014')
except (AssertionError,KeyError):wrong_stage_rejected=True
else:raise AssertionError('edge source admitted as front interval')
for name in ['audit_front_diagonal_entry_live.py','audit_front_interval_diagonal_live.py','front_interval_stage_source_binding.py','audit_front_interval_goal_records.py']:bindings[str(W/name)]=sha(W/name)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,episodes=rows,wrong_stage_rejected=wrong_stage_rejected,source_sha256=bindings,checker_sha256=sha(__file__),enabled_physics_verified=False,training_ready=False)
with (W/'FRONT_INTERVAL_COP_REGRESSION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('PASS')
