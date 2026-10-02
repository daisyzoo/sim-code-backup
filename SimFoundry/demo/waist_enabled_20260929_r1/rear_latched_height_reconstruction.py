"""Independent original height audit outside declared unloaded joint paths.
Declared paths use independent measured/nominal/predicted geometry and actual
commands; their old Cartesian target is metadata, not an executed height.
Does not import the controller. Existing load/tilt, contact, geometry, quality,
RGB and exact loaded-command audits remain separately required. Not admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify_rows(rows,controls,plan,enabled,verified_events=None,recovery_records=None):
 recovery_records={} if recovery_records is None else recovery_records
 verified_events={} if verified_events is None else verified_events
 selected=bool(plan.get('region_approach',{}).get('enabled') and not plan.get('front_route_selected') and not plan.get('initial_top_selected'))
 cfg=plan.get('rear_short_recovery');assert bool(cfg)==bool(enabled and selected)
 if cfg:
  for key,val in dict(enabled=True,initial_travel_z=.91,recontact_travel_z=.86,release_min_z=.91,original_guard_priority=True,selected_rear_region_only=True,loaded_control_unchanged=True).items():assert type(cfg[key]) is type(val) and cfg[key]==val,key
 assert [r['step'] for r in rows]==list(range(1,len(rows)+1))
 count=0;start=None;checked=0;recoveries=[];last_mode=None
 for final_row in rows:
  t=final_row['step'];recovery=recovery_records.get(t);row=final_row if recovery is None else recovery['parent_row']
  control=controls[t]
  if recovery is not None:
   assert recovery['kind'] in ('loaded_recovery','unload') and row['mode']=='top_push' and row['step']==t
   assert final_row['rear_corridor_override']==dict(kind=recovery['kind'],step=t,parent_evidence='rear_corridor_recovery.json')
   assert control['mode']==final_row['mode'] and np.max(abs(np.asarray(control['target_xyz'])-np.asarray(final_row['target_xyz'])))<=2e-6
   control=dict(control,mode=row['mode'],target_xyz=row['target_xyz'])
  target=np.asarray(row['target_xyz'],float);tip=np.asarray(row['observed_support_xyz'],float);assert target.shape==tip.shape==(3,) and np.isfinite(target).all() and np.isfinite(tip).all()
  assert np.max(abs(target-np.asarray(control['target_xyz'])))<=2e-6,(t,'expert mapping')
  if not selected:continue
  if 'travel_height_m' not in row:
   assert row['mode'] in ['rear_lift','rear_cross','rear_press','rear_push'],(t,'missing top trace')
   continue
  n=row['recontacts'];assert type(n) is int and n in [count,count+1],(t,'counter')
  if start is None or n>count:start=tip.copy()
  if n>count:
   assert row['last_recontact_reason'] in ['lost_contact','incipient_tilt_independent']
   assert row['mode'] in ['top_lift','top_cross'],(t,'restart bypass')
   recoveries.append(dict(step=t,reason=row['last_recontact_reason']))
  height=.86 if enabled and n else .91
  assert abs(row['travel_height_m']-height)<=1e-9,(t,'height',row['travel_height_m'],height)
  mode=row['mode']
  if mode=='top_lift':assert np.max(abs(target-np.r_[start[:2],max(height,start[2])]))<=2e-6,(t,'lift target')
  if t in verified_events:
   event=verified_events[t];assert event['kind'] in ('command','handover')
   assert mode==('top_press' if event['kind']=='handover' else 'top_cross')
   assert row['recontact_pose_phase']==('measured_handover' if event['kind']=='handover' else 'tracking')
  if mode=='top_cross' and t not in verified_events:
   assert abs(target[2]-height)<=2e-6,(t,'cross height')
   if last_mode!='top_cross':assert tip[2]>=height-.02-2e-6,(t,'cross entry measured height')
  if mode=='top_release':assert target[2]>=.91-2e-6,(t,'release lowered')
  if mode not in ['top_press','top_push']:assert row['contact_load']['applied_z_bias_m']==0,(t,'unloaded force bias')
  checked+=1;count=n;last_mode=mode
  if recovery is not None and recovery['kind']=='unload':
   assert final_row['mode']=='top_lift' and final_row['recontacts']==n+1
   assert final_row['last_recontact_reason']=='rear_corridor_no_verified_loaded_step'
   assert final_row['contact_load']['applied_z_bias_m']==final_row['contact_load']['stored_z_bias_m']==0.
   assert recovery['commit']['kind']=='started_original_recontact_lift'
   assert np.max(abs(np.asarray(final_row['target_xyz'])-recovery['commit']['verified_first_lift_reference']))<=2e-6
   start=tip.copy();count=n+1;last_mode='top_lift'
   recoveries.append(dict(step=t,reason=final_row['last_recontact_reason'],verified_first_lift=True))
 return dict(selected=selected,enabled=bool(enabled and selected),frames=len(rows),height_rows=checked,recontact_events=recoveries)
