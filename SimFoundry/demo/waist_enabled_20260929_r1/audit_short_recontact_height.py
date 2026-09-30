"""Independent recorded verification of explicit front recovery height only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
p=Path(sys.argv[1]);doc=json.loads((p/'frontal_bypass.json').read_text());plan=doc['plan'];rows=doc['rows']
g=plan['front_route_live_guards'];height=g['recontact_travel_z']
assert g['initial_travel_z']==.91 and .84<=height<=.91
assert not g['object_relative_lead'],'This registered comparison restores original continuous push'
threshold=plan.get('contact_stability_candidate',{}).get('tilt_recontact_rad',0.)
target='mailer' if 'mailer_to' in p.name else 'box'
with np.load(p/'parcel_orientation.npz') as z:
 q=z[target].astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
 tilts=np.arccos(np.clip(1-2*(q[:,0]**2+q[:,1]**2),-1,1))
errors=[];events=[];last_count=0;start=None;checked=0
for r in rows:
 if r['mode']=='front_guard_lift':
  if r['target_xyz'][2]<.91:errors.append(dict(step=r['step'],kind='emergency_lift_too_low'))
  continue
 count=r['recontacts']
 if start is None:start=r['observed_support_xyz']
 if count!=last_count:
  reason=r['last_recontact_reason']
  justified=reason=='lost_contact' or (reason=='incipient_tilt_independent' and threshold>0 and tilts[r['step']]>threshold)
  if count!=last_count+1 or not justified:errors.append(dict(step=r['step'],kind='unexpected_recontact'))
  start=r['observed_support_xyz'];events.append(dict(step=r['step'],mode=r['mode'],reason=reason,reference_xyz=start,travel_z=r['travel_height_m']))
 expected=height if count else .91
 if abs(r['travel_height_m']-expected)>1e-9:errors.append(dict(step=r['step'],kind='wrong_travel_height'))
 if r['mode']=='top_lift' and abs(r['target_xyz'][2]-max(expected,start[2]))>1e-8:errors.append(dict(step=r['step'],kind='wrong_lift_command'))
 if r['mode']=='top_cross' and abs(r['target_xyz'][2]-expected)>1e-8:errors.append(dict(step=r['step'],kind='wrong_cross_command'))
 if r['mode']=='top_release' and r['target_xyz'][2]<.91:errors.append(dict(step=r['step'],kind='release_too_low'))
 last_count=count;checked+=1
out=dict(passed=not errors,errors=errors,checked_frames=checked,recontact_events=events,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),orientation_sha256=hashlib.sha256((p/'parcel_orientation.npz').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),scope='Independent initial/recontact/guard/release height checks using recorded poses and count transitions; no controller helper used, not dynamics/safety or task success proof.',training_ready=False)
(p/'SHORT_RECONTACT_HEIGHT_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
