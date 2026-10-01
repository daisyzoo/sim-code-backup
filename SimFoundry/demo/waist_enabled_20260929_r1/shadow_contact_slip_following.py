"""Fixed recorded states, counterfactual commands only. Not a dynamics replay."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_contact_slip_following';sys.path.insert(0,str(stage))
from contact_slip_following import CopSlipFollowing
paths=[w/'tracking_region_groups_r1/case_840001/layout_840001_nudge_mailer_to_bin',w/'projected_object_relative_r1/case_62008/layout_62008_push_box_to_bin'];reports=[]
for ep in paths:
 key='box' if 'push_box' in ep.name else 'mailer';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);log=json.loads((ep/'frontal_bypass.json').read_text());assert log['plan']['front_route_selected'];rows=log['rows']
 with np.load(ep/'trace.npz') as z:obj=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 ctl=CopSlipFollowing()
 packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left';records=[];prev=None
 for r in rows:
  if 'parcel_top_xyz' not in r:continue
  t=r['step'];points=[];weights=[];packet=packets.get(t-1)
  if packet:
   assert np.max(abs(np.asarray(packet['post_action_pose'][key])-obj[t]))<1e-6
   for c in packet['parcel_contacts']:
    slots=[i for i,s in enumerate(c['shapes']) if '/'+actor+'/' in s]
    if len(slots)!=1 or not any(side+'_wrist' in s for s in c['shapes']):continue
    force=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@rot[t,:,2])
    if load>.05:points.append(c['position_world']);weights.append(load)
  cop=np.average(points,axis=0,weights=weights) if weights else None
  hold=r.get('clearance_progress');gy=(hold['front_hold_y'] if hold else log['plan']['initial_target_xyz'][1]) if r['route_stage']=='front_x' else log['plan']['front_route_candidates']['goal_y']
  if prev is None:prev=np.asarray(r['target_xyz'][:2])
  output=ctl.update(mode=r['mode'],object_xyz=obj[t],object_rotation=rot[t],object_size=size,goal_xy=[r['route_goal_x'],gy],reference_xy=r['observed_support_xyz'][:2],previous_command_xy=prev,cop_world=cop,normal_load_n=sum(weights))
  if output['override']:
   assert np.max(abs(np.asarray(output['command_xy'])-prev))<=.003000001
   prev=np.asarray(output['command_xy'])
  else:prev=np.asarray(r['target_xyz'][:2])
  records.append(dict(step=t,route_stage=r['route_stage'],**output))
 active=[x for x in records if x['override']];summary=dict(episode=str(ep),frames=len(records),override_frames=len(active),reason_counts=dict(collections.Counter(x['reason'] for x in records)),desired_lead_clipped_frames=sum(x['desired_lead_clipped'] for x in active),retained_slew_lag_frames=sum(x['retained_slew_lag_outside_lead'] for x in active),max_command_step_m=max((max(abs(v) for v in x['command_delta_xy']) for x in active),default=0),max_command_reference_lead_m=max((max(abs(v) for v in x['command_reference_lead_xy']) for x in active),default=0))
 reports.append(dict(summary=summary,records=records,source_sha256={f:hashlib.sha256((ep/f).read_bytes()).hexdigest() for f in ['raw.npz','frontal_bypass.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']}));print(json.dumps(summary),flush=True)
report=dict(rows=reports,helper_sha256=hashlib.sha256((stage/'contact_slip_following.py').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Counterfactual command shadow with actual states/contact packets fixed from two FAILED development episodes, including prior12mm lead stall. No causal prediction of new forces, visibility, object motion, completion time or success. No simulator wiring or data admission.',training_ready=False)
(stage/'RECORDED_SHADOW.json').write_text(json.dumps(report,indent=2))
