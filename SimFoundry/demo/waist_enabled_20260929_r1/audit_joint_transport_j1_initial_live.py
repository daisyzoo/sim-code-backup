"""Bind independent initial-front commands/captures to full native observations.
This added check does not replace original quality/pose/control/substep or image
audits and grants no training admission. Aborted horizons cannot pass.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_initial_center_events import EventAudit
from audit_front_initial_center_planning_v2 import SelectionAudit
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unique(rows):
 result={r['step']:r for r in rows};assert len(result)==len(rows);return result

def verify_files(ep, *, verified_recovery_events=None):
 ep=Path(ep)
 if verified_recovery_events is None:
  from audit_joint_transport_front_recovery_stream_v1 import verify_files as verify_recovery_files
  recovery_result=verify_recovery_files(ep)
  verified_recovery_events={r['step']:{k:v for k,v in r.items() if k!='step'} for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r['kind'] in ('command','handover')}
  assert set(verified_recovery_events)=={r['step'] for r in recovery_result['rows']}
 recovery_center=recovery_normal=recovery_anchor=None
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
 n=70 if task=='wait_no_package' else 1200
 assert task in ('wait_no_package','push_box_to_bin','nudge_mailer_to_bin')
 assert q.shape==u.shape==(n,11) and np.isfinite(q).all() and np.isfinite(u).all()
 assert np.max(abs(q[0]))==np.max(abs(u[0]))==0
 front=json.loads((ep/'front_initial_center.json').read_text());events=unique(front['rows'])
 if task=='wait_no_package':
  assert front['selected'] is False and not events
  return dict(passed=True,wait=True,selected=False,verified_commands=0,handovers=0,training_ready=False)
 fr=json.loads((ep/'frontal_bypass.json').read_text());rows=unique(fr['rows']);coords=unique(json.loads((ep/'coordination.json').read_text()));experts=unique(json.loads((ep/'expert_control.json').read_text()))
 assert sorted(rows)==sorted(coords)==list(range(1,n)) and sorted(experts)==list(range(n))
 selected=bool(fr['plan'].get('front_route_selected'));assert front['selected'] is selected
 if not selected:
  assert not events and all(c.get('controller_kind')!='verified_unloaded_front_initial_joint_path' for c in coords.values())
  return dict(passed=True,wait=False,selected=False,verified_commands=0,handovers=0,training_ready=False)
 assert sorted(events)==list(range(1,n))
 clear=json.loads((ep/'self_clearance.json').read_text());assert clear['failure'] is None and clear['recorded_frames']==clear['requested_frames']==n
 side='right' if task=='push_box_to_bin' else 'left';other='left' if side=='right' else 'right';key='box' if side=='right' else 'mailer';other_key='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer'
 with np.load(ep/'trace.npz') as z:target=z[key].astype(float);obstacle=z[other_key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:tq=z[key].astype(float);oq=z[other_key].astype(float)
 declaration=fr['plan']['front_initial_center_landing'];core=declaration['actual_core']['collision_core_size_xyz'];other_size=[.15,.145,.04] if other_key=='mailer' else [.14,.09,.045]
 parameters=json.loads((S/'causal_response_parameters.json').read_text());decay=parameters['tasks'][task]['decay']
 packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];packet_count=len(packets);packets={p['after_action_step']:p for p in packets};assert len(packets)==packet_count and sorted(packets)==list(range(n))
 audit=EventAudit(ROOT,S);selection_audit=SelectionAudit(ROOT,S);filtered=0.;center=None;captured_normal=None;captured_once=False;commands=[];preflights=[];attempted=False;captured_anchor=None
 for t in range(1,n):
  row=rows[t];coordinate=coords[t];raw=events[t];event={k:v for k,v in raw.items() if k!='step'};assert event['kind']!='stop'
  measured=0.
  for contact in packets[t-1]['parcel_contacts']:
   if any(side+'_wrist_roll' in name for name in contact['shapes']) and any('/'+actor+'/' in name for name in contact['shapes']):measured+=abs(float(contact['force_world_N'][2]))
  if 'contact_load' in row:
   filtered=.25*measured+.75*filtered
   near(row['contact_load']['observed_vertical_load_n'],measured,1e-10);near(row['contact_load']['filtered_vertical_load_n'],filtered,1e-10)
  scene=dict(side=side,target_xyz=target[t].tolist(),target_quat=tq[t].tolist(),core_size=core,other_xyz=obstacle[t].tolist(),other_quat=oq[t].tolist(),other_size=other_size)
  planning=event.get('planning')
  if planning is not None:
   assert not attempted and not captured_once and not audit.active,'repeated initial plan'
   attempted=True
   ctx=event['context'];assert ctx['step']==t and ctx['scene']==scene and ctx['selected'] is True
   assert ctx['parent_mode'] in ('top_cross','top_descend') and ctx['recontacts']==row['recontacts']==0
   assert ctx['guard_stop'] is False and not row.get('route_stop_reason') and not row.get('release_reason')
   assert ctx['observed_load_n']==measured==0 and ctx['filtered_load_n']==filtered and 0<=filtered<=.05
   for k,v in [('current',q[t]),('previous_q',q[t-1]),('previous_command',u[t-1]),('decay',decay)]:near(ctx[k],v,1e-7)
   near(ctx['observed_hand_pose'],audit.hand.fk(q[t],side),1e-4);near(ctx['observed_inactive_hand_pose'],audit.hand.fk(q[t],other),1e-4)
   preflights.append(selection_audit.verify_selection(planning,current=q[t],previous_q=q[t-1],previous_command=u[t-1],decay=decay,scene=scene,step=t))
  if event['kind'] in ('command','handover'):
   assert not captured_once and 'contact_load' in row
   assert coordinate['controller_kind']=='verified_unloaded_front_initial_joint_path'
   assert coordinate['front_initial_center_override']==event
   assert coordinate.get('recontact_pose_override') is None and not coordinate.get('terminal_joint_hold')
   ctx=event['context'];assert ctx['parent_mode'] in ('top_cross','top_descend')
   verified=audit.verify(event,step=t,current=q[t],previous_q=q[t-1],previous_command=u[t-1],final_command=u[t],scene=scene,decay=decay,selected=True,parent_mode=ctx['parent_mode'],recontacts=row['recontacts'],guard_stop=bool(row.get('route_stop_reason') or row.get('release_reason')),observed_load_n=measured,filtered_load_n=filtered)
   near(coordinate['upper_q'],q[t],1e-7);assert coordinate['active_side']==side and coordinate['bounded_solver'] is True
   assert coordinate['task_inputs'] is None and coordinate['contact_normal_tracking'] is None and coordinate['contact_bout_yaw_tracking'] is None
   assert not coordinate.get('region_joint_override') and not coordinate.get('joint_edge_refinement',{}).get('override',False)
   assert row['mode']==('top_press' if event['kind']=='handover' else 'top_cross')
   assert row['contact_load']['applied_z_bias_m']==row['contact_load']['stored_z_bias_m']==0
   commands.append(verified)
   if event['kind']=='handover':
    captured_once=True;center=np.array(event['captured_center_local']);captured_normal=event['captured_normal_local_up'];captured_anchor=event['captured_inactive_anchor_world'];near(coordinate['inactive_anchor'],event['captured_inactive_anchor_world'],1e-9)
  else:
   assert not audit.active,'missing event during active initial-front path'
   assert event['kind']=='unchanged' and coordinate.get('controller_kind')!='verified_unloaded_front_initial_joint_path'
   assert coordinate.get('front_initial_center_override') is None
   if planning is not None:
    assert planning['accepted'] is False and event['reason']=='no_verified_initial_plan'
   elif captured_once:assert event['reason']=='initial_handover_already_complete'
   else:
    eligible=row['recontacts']==0 and row['mode'] in ('top_cross','top_descend') and not row.get('route_stop_reason') and not row.get('release_reason')
    if eligible:
     assert attempted or measured!=0 or not 0<=filtered<=.05,'missing required first unloaded plan'
     assert event['reason']=='no_new_unloaded_initial_attempt'
    else:assert event['reason']=='not_initial_front_unloaded_phase'
  recovery_event=verified_recovery_events.get(t)
  if recovery_event is not None:
   assert event['kind']=='unchanged' and recovery_event['kind'] in ('command','handover')
   if recovery_event['kind']=='handover':
    recovery_center=np.array(recovery_event['captured_center_local']);recovery_normal=recovery_event['captured_normal_local_up'];recovery_anchor=recovery_event['captured_inactive_anchor_world']
  if center is not None:
   near(coordinate['inactive_anchor'],recovery_anchor if recovery_anchor is not None else captured_anchor,1e-9)
   near(raw['center_local_after'],center,0)
   near(row['front_initial_captured_center_local'],center,0)
   pose=audit.hand.fk(q[t],side);R=pose[:3,:3];normal=Rotation.from_quat(tq[t]).as_matrix()[:,2];normal_local=R.T@normal;vertices=audit.hand.vertices[side]
   active_center=recovery_center if recovery_center is not None else center
   reference=active_center+normal_local*(np.min(vertices@normal_local)-active_center@normal_local)
   near(row['projected_support_reference']['center_local'],active_center,0)
   near(row['projected_support_reference']['reference_local'],reference,2e-6)
   near(row['control_offset_local'],reference,2e-6)
   if row['mode'] in ('top_lift','top_cross','top_descend','top_press','top_push') and event['kind'] not in ('command','handover') and recovery_event is None:
    assert coordinate['contact_normal_tracking'] is not None
    near(coordinate['contact_normal_tracking']['target_local_up'],recovery_normal if recovery_normal is not None else captured_normal,2e-6)
  near(experts[t]['target_xyz'],row['target_xyz'],2e-6)
  assert experts[t]['mode']==row['mode']
 assert not audit.active,'unfinished initial-front path'
 assert len(preflights)<=1
 return dict(passed=True,wait=False,selected=True,verified_commands=len(commands),handovers=int(captured_once),rows=commands,preflights=preflights,training_ready=False)

def audit(ep):
 from joint_transport_stage_source_binding_v1 import verify_observation_binding
 ep=Path(ep).resolve();source=verify_observation_binding(ep);result=verify_files(ep)
 names=['front_recontact_center.json','raw.npz','front_initial_center.json','frontal_bypass.json','coordination.json','expert_control.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json','self_clearance.json']
 result.update(source_binding=source,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),*[ep/n for n in names if (ep/n).exists()]]})
 return result
if __name__=='__main__':
 ep=Path(sys.argv[1]);result=audit(ep);(ep/'JOINT_TRANSPORT_J1_INITIAL_LIVE_AUDIT.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['rows','preflights','source_binding','source_sha256','scope']});sys.exit(0 if result['passed'] else 1)
