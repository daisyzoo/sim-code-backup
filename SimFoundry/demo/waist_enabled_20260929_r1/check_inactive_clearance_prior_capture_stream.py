"""Actual old episode prefix followed by explicitly hypothetical preparation/recovery.
Tests previous measured capture retention across a later preparation. This hybrid
is a stream fixture, not a newly executed policy or an admissible trajectory.
"""
from pathlib import Path
import copy,json,hashlib,datetime,sys
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_inactive_clearance';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_inactive_clearance_stream import RecoveryStreamAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ep=W/'front_recontact_headroom_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';bound=W/'inactive_hand_headroom_draft_r1/FULL_HYPOTHESIS_CHECK.json';base=json.loads(bound.read_text());assert base['passed']
for p,h in base['source_sha256'].items():assert sha(p)==h,p
fixture=next(r for r in base['results'] if r['original_actual_step']==405);events=fixture['hypothetical_events'];start=events[0]['context']['step'];assert start==405
log=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in log['rows']};coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};old={r['step']:r for r in json.loads((ep/'front_recontact_center.json').read_text())['rows']};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
with np.load(ep/'trace.npz') as z:target=z['mailer'];other=z['box']
with np.load(ep/'parcel_orientation.npz') as z:tq=z['mailer'];oq=z['box']
core=log['plan']['front_initial_center_landing']['actual_core']['collision_core_size_xyz'];decay=json.loads((S/'causal_response_parameters.json').read_text())['tasks']['nudge_mailer_to_bin']['decay'];checker=RecoveryStreamAudit(ROOT,S);filtered=0.
for t in range(1,start):
 row=rows[t];e={k:v for k,v in old[t].items() if k!='step'};measured=sum(abs(float(x['force_world_N'][2])) for x in packets[t-1]['parcel_contacts'] if any('left_wrist_roll' in n for n in x['shapes']) and any('/mailer/' in n for n in x['shapes']))
 if 'contact_load' in row:
  filtered=.25*measured+.75*filtered;assert abs(filtered-row['contact_load']['filtered_vertical_load_n'])<1e-10
 scene=dict(side='left',target_xyz=target[t].tolist(),target_quat=tq[t].tolist(),core_size=core,other_xyz=other[t].tolist(),other_quat=oq[t].tolist(),other_size=[.14,.09,.045])
 checker.observe(e,row,coords[t],step=t,current=q[t],previous_q=q[t-1],previous_command=u[t-1],final_command=u[t],scene=scene,decay=decay,observed_load_n=measured,filtered_load_n=filtered)
assert checker.handovers==[dict(step=299,recontacts=1)] and checker.center is not None
previous_center=list(checker.center);previous_anchor=list(checker.anchor);negative=[]
for index,original in enumerate(events):
 e=copy.deepcopy(original);c=e['context'];t=c['step'];scene=c['scene'];e['real_recontact_index']=c['recontacts']
 if e.get('phase')=='inactive_clearance_preparation':
  p=e['proposal'];p.update(candidate_command=p['command'],command_check=p['original_command_check'],nominal_scene=p['nominal'],predicted_scene=p['predicted'])
 center=e['captured_center_local'] if e['kind']=='handover' else checker.center;anchor=e['captured_inactive_anchor_world'] if e['kind']=='handover' else checker.anchor;e['center_local_after']=center
 pose=np.asarray(c['observed_hand_pose']);normal=Rotation.from_quat(scene['target_quat']).as_matrix()[:,2];nl=pose[:3,:3].T@normal;verts=checker.selection.hand.vertices['left'];cv=np.asarray(center);ref=cv+nl*(min(verts@nl)-cv@nl)
 row=dict(step=t,mode='top_press' if e['kind']=='handover' else 'top_cross',recontacts=c['recontacts'],front_recontact_center_phase='measured_handover' if e['kind']=='handover' else 'tracking',contact_load=dict(observed_vertical_load_n=c['observed_load_n'],filtered_vertical_load_n=c['filtered_load_n'],applied_z_bias_m=0.,stored_z_bias_m=0.),front_recontact_captured_center_local=center,projected_support_reference=dict(center_local=center,reference_local=ref.tolist()),control_offset_local=ref.tolist())
 co=dict(step=t,controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=e,active_side='left',bounded_solver=True,upper_q=c['current'],task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None,inactive_anchor=anchor)
 kw={k:c[k] for k in ['step','current','previous_q','previous_command','scene','decay','observed_load_n','filtered_load_n']};kw['final_command']=e['command']
 if index==0:
  for label in ['discard_prior_center','recapture_anchor_during_preparation','wrong_prior_reference']:
   ch=copy.deepcopy(checker);bad,rr,cc=copy.deepcopy((e,row,co))
   if label=='discard_prior_center':bad['center_local_after']=None
   elif label=='recapture_anchor_during_preparation':cc['inactive_anchor'][2]+=.002
   else:rr['projected_support_reference']['reference_local'][0]+=.002
   try:ch.observe(bad,rr,cc,**kw)
   except (AssertionError,ValueError,KeyError):negative.append(label)
   else:raise AssertionError(('lost prior capture accepted',label))
 checker.observe(e,row,co,**kw)
 if index==0:assert checker.center==previous_center and checker.anchor==previous_anchor
result=checker.finish();assert result['handovers']==2 and result['recovery_handovers']==[dict(step=299,recontacts=1),dict(step=422,recontacts=2)]
files=[Path(__file__),bound,W/'audit_front_inactive_clearance_stream.py',W/'audit_inactive_clearance_events.py',*[ep/n for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','coordination.json','front_recontact_center.json','solved_contact_forces.json']]]
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_prefix_frames=404,actual_prior_handover_step=299,hypothetical_following_events=len(events),hybrid_stream_result=result,negative_cases=negative,source_sha256={str(p):sha(p) for p in files},physical_candidate_success=False,training_ready=False)
with (S/'PRIOR_CAPTURE_STREAM_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_prefix=404,hypothetical_following_events=len(events),negative=len(negative))))
