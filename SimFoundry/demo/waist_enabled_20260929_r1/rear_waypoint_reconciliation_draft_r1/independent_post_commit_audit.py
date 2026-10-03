"""Independent applied-state-event verifier. Does not import candidate helpers.
Reads actual raw commands, guard records, prior forces and URDF. All original
full episode/source/pose/contact audits are still required before admission.
"""
from pathlib import Path
import json,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from simfoundry.calibration.sorting_station import SORTING_ROBOT_POS,SORTING_ROBOT_ROT_XYZW

def load_context(ep,urdf):
 ep=Path(ep);tree=ET.parse(urdf).getroot();bychild={j.find('child').get('link'):j for j in tree.findall('joint')};names=['waist_yaw_joint']+[f'{s}_{j}_joint' for s in ['left','right'] for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll']];chain=[];link='right_wrist_roll_rubber_hand';visited=set()
 while link in bychild:
  assert link not in visited;visited.add(link);node=bychild[link];chain.append(node);link=node.find('parent').get('link')
 def reference(q,offset):
  T=np.eye(4);T[:3,3]=SORTING_ROBOT_POS;T[:3,:3]=Rotation.from_quat(SORTING_ROBOT_ROT_XYZW).as_matrix()
  for node in reversed(chain):
   O=np.eye(4);o=node.find('origin')
   if o is not None:O[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');O[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
   T=T@O
   if node.get('type') in ['revolute','continuous']:
    name=node.get('name');assert name in names+['waist_pitch_joint','waist_roll_joint'];angle=q[names.index(name)] if name in names else 0.;R=np.eye(4);R[:3,:3]=Rotation.from_rotvec(np.fromstring(node.find('axis').get('xyz'),sep=' ')*angle).as_matrix();T=T@R
  return T[:3,3]+T[:3,:3]@offset
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z['box']).as_matrix()
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
 fr=json.loads((ep/'frontal_bypass.json').read_text());cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};clear=json.loads((ep/'self_clearance.json').read_text());fg={x['step']:x for x in clear['rows'] if x['phase']=='final_command'};pg={x['step']:x for x in clear['rows'] if x['phase']=='post'};packets={x['after_action_step']:x for x in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
 return dict(ep=ep,q=q,u=u,reference=reference,rot=rot,xyz=xyz,fr=fr,cs=cs,fg=fg,pg=pg,packets=packets)

def verify(context,events):
 c=context;q,u=c['q'],c['u'];reported={x['step']:x for x in events};assert len(reported)==len(events),'duplicate event';expected={};records=[]
 def near(a,b,tol):
  a,b=np.asarray(a,float),np.asarray(b,float);assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all() and np.max(abs(a-b),initial=0)<=tol
 for f in c['fr']['rows']:
  t=f['step'];coordinate=c['cs'][t];edge=coordinate.get('joint_edge_refinement');eligible=(c['fr']['plan']['rear_cop_centering']['enabled'] and f['mode']=='top_push' and isinstance(edge,dict) and edge.get('input_selected') is True and edge.get('override') is True and not coordinate.get('region_joint_override') and not coordinate.get('terminal_joint_hold'))
  if not eligible:continue
  assert coordinate['active_side']=='right' and f['rear_cop_centering']['override'] is True
  assert c['fg'][t]['accepted'] is True and c['pg'][t]['accepted'] is True
  near(c['fg'][t]['command'],u[t],0);near(c['fg'][t]['current'],q[t],1e-7);near(c['fg'][t]['previous'],u[t-1],0)
  if not np.array_equal(u[t],np.asarray(edge['final_upper_command'])):continue
  packet=c['packets'][t-1];near(packet['post_action_pose']['box'],c['xyz'][t],2e-6);weights=[]
  for contact in packet['parcel_contacts']:
   slots=[i for i,label in enumerate(contact['shapes']) if '/parcel_box/' in label]
   if len(slots)!=1 or not any('right_wrist' in label for label in contact['shapes']):continue
   force=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@c['rot'][t,:,2])
   if load>.05:weights.append(load)
  load=sum(weights)
  if load<.3:continue
  offset=np.asarray(f['control_offset_local']);point=c['reference'](u[t],offset);requested=np.asarray(f['target_xyz'],float)
  near(c['reference'](q[t],offset),f['observed_support_xyz'],2e-6)
  if point[1]<=requested[1]:continue
  after=requested.copy();after[1]=point[1];expected[t]=after.tolist();assert t in reported,('missing eligible event',t);e=reported[t]
  assert e['applied'] is True and e['current_action_changed'] is False and e['training_ready'] is False
  assert e['version']=='rear_box_post_commit_adapter_draft_v1' and e['reason']=='reconcile_future_cursor_to_nominal_committed_reference'
  near(e['committed_upper_command'],u[t],0);near(e['current_upper_q'],q[t],1e-7);near(e['previous_upper_command'],u[t-1],0);near(e['reference_offset_local'],offset,0);near(e['observed_normal_load_n'],load,2e-6)
  near(e['state_before']['command'],requested,0);near(e['state_before']['last_waypoint_xy'],requested[:2],0);near(e['state_after']['command'],after,2e-10);near(e['state_after']['last_waypoint_xy'],after[:2],2e-10)
  s=e['suggestion'];assert s['override'] is True and s['version']=='rear_box_post_commit_y_reconciliation_draft_v1' and s['reason']==e['reason'] and s['current_action_changed'] is False and s['physical_motion_prediction'] is False
  near(s['requested_before_xyz'],requested,0);near(s['nominal_committed_reference_xyz'],point,2e-10);near(s['next_state_command_xyz'],after,2e-10);near(s['next_state_last_waypoint_xy'],after[:2],2e-10);near(s['removed_unrealized_forward_y_m'],point[1]-requested[1],2e-10)
  records.append(dict(step=t,independent_nominal_committed_reference_xyz=point.tolist(),verified_next_command_xyz=after.tolist()))
 assert set(reported)==set(expected),'unexpected applied event'
 return dict(passed=True,applied_events=len(records),records=records,verified_post_commit=expected,training_ready=False)
