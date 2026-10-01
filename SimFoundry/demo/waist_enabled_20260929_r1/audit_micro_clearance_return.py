"""Independent current-geometry and force reconstruction for tiny-repair retention.
Never imports the candidate helper/controller. Original geometry/COP/command,
quality, whole-group and actual image audits remain separately required.
"""
from pathlib import Path
import json,math,sys,hashlib
import numpy as np
from scipy.spatial.transform import Rotation

def verify_stream(rows,plan,tr,ori,packets,key,enabled):
 side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';direction=-1 if key=='box' else 1;core=np.array(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']);rot=Rotation.from_quat(ori[key]).as_matrix();previous_stage='front_x';previous_mode='top_lift';count=0;start=None;trajectory=[];latched=False;events=[]
 def near(a,b):
  aa=np.asarray(a,dtype=float);bb=np.asarray(b,dtype=float);assert aa.shape==bb.shape and np.isfinite(aa).all() and np.max(abs(aa-bb))<2e-7,(t,aa.tolist(),bb.tolist(),float(np.max(abs(aa-bb))))
 for row in rows:
  t=row['step'];obj=tr[key][t];packet=packets[t-1];near(packet['post_action_pose'][key],obj)
  if row.get('route_stop_reason'):
   assert row['mode']=='front_guard_lift' and 'direction_change_recontact' not in row;latched=True;continue
  assert not latched
  stage=row['route_stage'];e=row['direction_change_recontact'];changed=previous_stage!=stage
  vertical=sum(abs(float(c['force_world_N'][2])) for c in packet['parcel_contacts'] if any(side+'_wrist_roll' in label for label in c['shapes']) and any('/'+actor+'/' in label for label in c['shapes']))
  terminal=direction*obj[1]>=max(.205,direction*plan['initial_target_xyz'][1]+.16);tilted=math.acos(float(np.clip(rot[t,2,2],-1,1)))>.03
  original=bool(changed and previous_mode=='top_push' and vertical>=.3 and not terminal and not tilted);retain=False;measured=None
  if enabled:
   if changed and previous_stage=='lateral_y' and stage=='front_x':start=t;trajectory=[]
   if start is not None:trajectory.append(np.array(obj[:2]))
   excursion=0. if start is None else float(np.linalg.norm(np.array(trajectory)-tr[key][start,:2],axis=1).max());returning=bool(changed and previous_stage=='front_x' and stage=='lateral_y' and start is not None)
   points=[];weights=[]
   for c in packet['parcel_contacts']:
    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
    if len(slots)!=1 or not any(side+'_wrist_roll' in s for s in c['shapes']):continue
    force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);n=-float(force@rot[t,:,2])
    if n>.05:points.append(c['position_world']);weights.append(n)
   # Shared summary exists for any contact normal>.05; retention separately
   # requires summed normal>=.3. Keep low-load measurements in the evidence.
   normal=float(sum(weights));valid=normal>=.3;margin=None
   if weights:
    cop=np.average(points,axis=0,weights=weights);local=rot[t].T@(cop-obj);margin=float(min(core[:2]/2-abs(local[:2])))
   else:normal=0.
   retain=bool(original and returning and excursion<=.005 and valid and margin>=.01 and not terminal and not tilted)
   m=e['micro_repair_retention'];assert type(m['retained']) is bool and m['retained']==retain and m['known_return']==returning and m['current_cop_valid']==valid
   assert m['maximum_allowed_excursion_m']==.005 and m['minimum_core_margin_m']==.01
   near(m['maximum_excursion_m'],excursion);near(m['normal_load_n'],normal)
   if start is None:assert m['repair_start_xy'] is None
   else:near(m['repair_start_xy'],tr[key][start,:2])
   if margin is None:assert m['current_core_margin_m'] is None
   else:near(m['current_core_margin_m'],margin)
   measured=dict(maximum_excursion_m=excursion,core_margin_m=margin,normal_load_n=normal)
   if changed and stage=='lateral_y':start=None;trajectory=[]
  else:assert 'micro_repair_retention' not in e
  expected=original and not retain
  assert e['previous_stage']==previous_stage and e['current_stage']==stage and e['previous_top_mode']==previous_mode
  near(e['measured_vertical_load_n'],vertical);assert e['stage_changed']==changed and e['terminal_precedence']==bool(terminal) and e['tilt_precedence']==tilted and e['restarted']==expected
  if expected:
   assert row['mode'] in ['top_lift','top_cross'] and row['last_recontact_reason']=='front_route_direction_change' and row['recontacts']==count+1 and row['contact_load']['applied_z_bias_m']==0 and not row['cop_slip_following']['override']
   if row['mode']=='top_lift':near(row['target_xyz'][:2],row['observed_support_xyz'][:2])
  if retain:assert row['mode']=='top_push' and row['recontacts']==count
  if original:events.append(dict(step=t,retained=retain,restarted=expected,measured=measured))
  previous_stage=stage;previous_mode=row['mode'];count=row['recontacts']
 return events
