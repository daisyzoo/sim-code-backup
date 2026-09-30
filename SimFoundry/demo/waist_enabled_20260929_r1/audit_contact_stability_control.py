"""Independent recorded orientation/recovery/release checks; no controller imports."""
from pathlib import Path
from collections import deque
import numpy as np,json,hashlib,math,sys
p=Path(sys.argv[1]);d=json.loads((p/'frontal_bypass.json').read_text());plan=d['plan'];rows=d['rows'];errors=[];events=[]
with np.load(p/'raw.npz') as a:task=str(a['task_id'])
key='box' if task=='push_box_to_bin' else 'mailer'
with np.load(p/'parcel_orientation.npz') as a:q=np.array(a[key],dtype=float)
with np.load(p/'trace.npz') as a:xyz=np.array(a[key],dtype=float)
q/=np.linalg.norm(q,axis=1,keepdims=True);tilts=np.arccos(np.clip(1-2*(q[:,0]**2+q[:,1]**2),-1,1))
threshold=plan.get('contact_stability_candidate',{}).get('tilt_recontact_rad',0.)
confirm=plan.get('confirmed_terminal_release',{}).get('enabled',False);direction=plan['direction'];initial_y=plan['initial_target_xyz'][1]
window=deque(maxlen=10);previous=None;release=None;max_tilt_error=0.;count=0
for r in rows:
 step=r['step'];mode=r['mode'];top='observed_parcel_tilt_rad' in r
 if not top:previous=r;continue
 tilt=tilts[step];max_tilt_error=max(max_tilt_error,abs(tilt-r['observed_parcel_tilt_rad']))
 if np.max(np.abs(xyz[step]-r['observed_target']))>2e-6:errors.append(dict(step=step,kind='recorded_pose_alignment'))
 if threshold and r.get('tilt_recontact_threshold_rad')!=threshold:errors.append(dict(step=step,kind='threshold_metadata'))
 if previous is not None and previous['mode'] in ('top_press','top_push') and threshold and tilt>threshold:
  if mode not in ('top_lift','top_cross') or r['recontacts']!=previous.get('recontacts',0)+1:
   errors.append(dict(step=step,kind='missing_tilt_withdrawal'))
 if r['recontacts']>count:
  reason=r['last_recontact_reason'];events.append(dict(step=step,reason=reason,tilt_rad=float(tilt),mode=mode))
  if reason=='incipient_tilt_independent' and not (threshold and tilt>threshold):errors.append(dict(step=step,kind='unjustified_tilt_withdrawal'))
  count=r['recontacts']
 if confirm:
  window.append(xyz[step]);ready=len(window)==10 and direction*(xyz[step,1]-initial_y)>=.15 and all(direction*x[1]>=.20 for x in window) and np.linalg.norm(xyz[step,:2]-window[0][:2])<=.01
  if bool(r['terminal_position_confirmed'])!=bool(ready):errors.append(dict(step=step,kind='position_confirmation_mismatch'))
 if mode=='top_release':
  if release is None:
   release=dict(step=step,reason=r.get('release_reason'),tip=r['observed_support_xyz'])
   if confirm and release['reason']=='confirmed_original_target_position' and not ready:errors.append(dict(step=step,kind='unconfirmed_release'))
  if max(abs(r['target_xyz'][i]-release['tip'][i]) for i in (0,1))>1e-8 or r['target_xyz'][2]<.91:errors.append(dict(step=step,kind='release_pose_changed'))
 if mode not in ('top_press','top_push') and abs(r['contact_load']['applied_z_bias_m'])>1e-12:errors.append(dict(step=step,kind='load_bias_while_unloading'))
 previous=r
if max_tilt_error>1e-5:errors.append(dict(kind='orientation_tilt_mismatch',max_error=max_tilt_error))
sha=lambda f:hashlib.sha256((p/f).read_bytes()).hexdigest()
out=dict(control_checks_passed=not errors,errors=errors,threshold_rad=threshold,recontact_events=events,release=release,max_tilt_rad=float(tilts.max()),max_tilt_deg=float(np.degrees(tilts.max())),peak_frame=int(tilts.argmax()),original_pose_tilt_gate_rad=.20,original_tilt_gate_passed=bool(tilts.max()<=.20),first_original_tilt_violation_frame=int(np.flatnonzero(tilts>.20)[0]) if (tilts>.20).any() else None,max_recorded_tilt_error_rad=max_tilt_error,source_sha256={f:sha(f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']},scope='Pre-action trace and quaternions, independent formulas for configured recovery and confirmation. Checks recorded sampled logic, not all substep forces/collisions, full task gate or training admission.',training_ready=False)
(p/'CONTACT_STABILITY_CONTROL_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('source_sha256','scope')},indent=2))
