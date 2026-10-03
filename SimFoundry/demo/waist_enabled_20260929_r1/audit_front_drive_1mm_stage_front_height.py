"""Actual front-route approach/recontact/guard heights and expert mapping.
Separate from recorded clearance-stage audit, physics, and admission.
"""
from pathlib import Path
import sys,json,hashlib

def audit(log,controls,*,verified_front_events=None):
 verified_front_events={} if verified_front_events is None else verified_front_events
 assert set(verified_front_events)<={r["step"] for r in log["rows"]}
 if not log['plan'].get('front_route_selected'):
  return dict(applicable=False,passed=False,errors=[dict(kind='front_route_not_selected')])
 guards=log['plan']['front_route_live_guards'];initial=guards['initial_travel_z'];recovery=guards['recontact_travel_z']
 errors=[];normal=0;recovered=0;guard_frames=0;previous_count=0;startz=None;guardz=None
 if initial!=.91 or not .84<=recovery<=.91:errors.append(dict(kind='configuration_height'))
 if log['plan']['top_recontact'].get('recovery_clearance_m',0):errors.append(dict(kind='unsupported_dynamic_height'))
 by_step={r['step']:r for r in controls}
 for r in log['rows']:
  t=r['step'];goal=r['target_xyz'];tip=r['observed_support_xyz'];mode=r['mode'];actual=by_step[t]['target_xyz']
  if max(abs(goal[i]-actual[i]) for i in range(3))>2e-6:errors.append(dict(step=t,kind='expert_mapping'))
  if mode=='front_guard_lift':
   if guardz is None:guardz=max(.91,tip[2])
   if abs(goal[2]-guardz)>2e-6:errors.append(dict(step=t,kind='guard_height'))
   guard_frames+=1;continue
  if guardz is not None:errors.append(dict(step=t,kind='latched_guard_exited'))
  count=r['recontacts'];height=recovery if count else initial
  if startz is None or count>previous_count:startz=tip[2]
  if count<previous_count:errors.append(dict(step=t,kind='recontact_count_decreased'))
  previous_count=count
  if abs(r['travel_height_m']-height)>1e-9:errors.append(dict(step=t,kind='recorded_height'))
  if t in verified_front_events:
   event=verified_front_events[t];assert event['kind'] in ('command','handover') and count==0
   assert mode==('top_press' if event['kind']=='handover' else 'top_cross')
   assert r['front_initial_center_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')
  if mode=='top_cross' and t not in verified_front_events and abs(goal[2]-height)>2e-6:errors.append(dict(step=t,kind='cross_height'))
  if mode=='top_lift' and abs(goal[2]-max(height,startz))>2e-6:errors.append(dict(step=t,kind='lift_height'))
  if mode=='top_release' and goal[2]<.91-2e-6:errors.append(dict(step=t,kind='release_height'))
  normal+=1;recovered+=int(count>0)
 if normal+guard_frames==0:errors.append(dict(kind='empty_front_record'))
 return dict(applicable=True,passed=not errors,errors=errors,initial_height_m=initial,recovery_height_m=recovery,normal_rows=normal,recovery_rows=recovered,guard_rows=guard_frames,recontacts=previous_count)

def main():
 ep=Path(sys.argv[1]);from front_drive_1mm_stage_audit_context import verified_front_events
 result=audit(json.loads((ep/'frontal_bypass.json').read_text()),json.loads((ep/'expert_control.json').read_text()),verified_front_events=verified_front_events(ep));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 result.update(raw_sha256=sha(ep/'raw.npz'),frontal_sha256=sha(ep/'frontal_bypass.json'),scope='Actual front route only: initial/recontact/latched guard/release heights and expert waypoint mapping. Clearance-state geometry audited separately. Does not certify physical dynamics, task success, visual quality or training admission.',training_ready=False)
 (ep/'FRONT_DRIVE_1MM_STAGE_FRONT_HEIGHT_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='errors'}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
