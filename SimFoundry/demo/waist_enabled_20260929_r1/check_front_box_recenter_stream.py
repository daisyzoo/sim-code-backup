"""Explicit synthetic native-shape and affine stream fixtures, NOT new physics.
Uses real source-bound affine event proofs with manufactured lift-only prefixes
and held suffixes to test the independent file/stream boundary and exclusions.
These temporary fixtures cannot satisfy the native source/provenance wrapper.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys,tempfile,shutil
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_recenter_v3';D=W/'front_box_recenter_draft_r1';sys.path[:0]=[str(W),str(ROOT)]
from audit_front_box_recenter_stream import RecoveryStreamAudit,verify_files,audit
from audit_front_initial_center_preflight import SelectionAudit
from audit_unloaded_wrist_prior_live import near
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();base=json.loads((D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json').read_text());records=[];negative=[];native=None
for path,h in base['source_sha256'].items():assert sha(path)==h,path
for original_fixture in base['records']:
 if original_fixture['counter'] not in (2,6,12):continue
 fixture=dict(original_fixture,run='front_corridor_midpoint_physical_r1')
 events=copy.deepcopy(fixture['events']);c=events[0]['context'];scene=c['scene'];count=fixture['counter'];checker=RecoveryStreamAudit(ROOT,S,"right");center=None;normal=None;anchor=[.2,-.3,.89];frames=[]
 for t in range(1,c['step']):
  # Real positive counter sequence but explicitly fabricated lift-only prefix.
  counter=max(0,count-(c['step']-1-t));row=dict(step=t,mode='top_lift',recontacts=counter,contact_load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=0.),target_xyz=scene['target_xyz'])
  event=dict(front_box_recenter_version='front_box_recenter_v1',kind='unchanged',reason='first_contact_remains_original' if counter==0 else 'not_initial_front_unloaded_phase',real_recontact_index=counter,center_local_after=None)
  kw=dict(step=t,current=c['current'],previous_q=c['previous_q'],previous_command=c['previous_command'],final_command=c['previous_command'],scene=scene,decay=c['decay'],observed_load_n=0.,filtered_load_n=0.)
  checker.observe(event,row,{},**kw);frames.append((event,row,{},kw))
 for original in events:
  event=copy.deepcopy(original);event['front_box_recenter_version']='front_box_recenter_v1';cc=event['context'];t=cc['step'];event['real_recontact_index']=count
  row=dict(step=t,mode='top_press' if event['kind']=='handover' else 'top_cross',recontacts=count,contact_load=dict(observed_vertical_load_n=cc['observed_load_n'],filtered_vertical_load_n=cc['filtered_load_n'],applied_z_bias_m=0.,stored_z_bias_m=0.),front_recontact_center_phase='measured_handover' if event['kind']=='handover' else 'tracking',target_xyz=scene['target_xyz'])
  if event['kind']=='handover':
   center=event['captured_center_local'];normal=event['captured_normal_local_up'];anchor=event['captured_inactive_anchor_world'];row.update(front_recontact_captured_center_local=center,projected_support_reference=event['reference'],control_offset_local=event['reference']['reference_local'])
  event['center_local_after']=center
  co=dict(step=t,controller_kind='verified_unloaded_front_recontact_joint_path',front_recontact_center_override=event,active_side='right',bounded_solver=True,upper_q=cc['current'],task_inputs=None,contact_normal_tracking=None,contact_bout_yaw_tracking=None,inactive_anchor=anchor)
  kw=dict(step=t,current=cc['current'],previous_q=cc['previous_q'],previous_command=cc['previous_command'],final_command=event['command'],scene=scene,decay=cc['decay'],observed_load_n=cc['observed_load_n'],filtered_load_n=cc['filtered_load_n'])
  if len(records)==0 and original is events[0]:
   baseline=copy.deepcopy(checker)
   for label in ['missing_event','wrong_final_command','false_counter','false_binding','guard_during_command','wrong_controller','competing_initial','modified_current','premature_handover','missing_source_step','loaded_override','context_pose_changed']:
    e,r,coord,k=copy.deepcopy((event,row,co,kw));ch=copy.deepcopy(baseline)
    if label=='missing_event':e=dict(kind='unchanged',reason='no_new_unloaded_initial_attempt',real_recontact_index=count,center_local_after=None);coord={}
    elif label=='wrong_final_command':k['final_command'][0]+=.001
    elif label=='false_counter':r['recontacts']=0
    elif label=='false_binding':e['real_recontact_index']=count+1
    elif label=='guard_during_command':r['route_stop_reason']='original_guard'
    elif label=='wrong_controller':coord['controller_kind']='fake'
    elif label=='competing_initial':coord['front_initial_center_override']={}
    elif label=='modified_current':k['current'][0]+=.001
    elif label=='premature_handover':e['kind']='handover'
    elif label=='missing_source_step':k['step']+=1
    elif label=='loaded_override':k['observed_load_n']=1.
    elif label=='context_pose_changed':e['context']['observed_hand_pose'][0][3]+=.01
    try:ch.observe(e,r,coord,**k)
    except (AssertionError,ValueError,KeyError):negative.append(label)
    else:raise AssertionError('bad frame accepted '+label)
  checker.observe(event,row,co,**kw);frames.append((event,row,co,kw))
  if len(records)==0 and original is events[0]:
   try:checker.finish()
   except AssertionError:negative.append('unfinished_path')
   else:raise AssertionError('unfinished path accepted')
   missing=copy.deepcopy(checker);bad=dict(kind='unchanged',reason='no_new_unloaded_initial_attempt',real_recontact_index=count,center_local_after=None);nk=dict(kw,step=t+1)
   try:missing.observe(bad,row,{},**nk)
   except AssertionError:negative.append('missing_active_event')
   else:raise AssertionError('missing active event accepted')
 result=checker.finish();assert result['verified_commands']==len(events) and result['handovers']==1
 records.append(dict(run=fixture['run'],counter=count,commands=len(events),preflight_trials=result['preflights'][0]['trials'],independent_stream_passed=True))
 if native is None:native=(frames,fixture)
 print('verified affine stream',fixture['run'],count,len(events),flush=True)
# One complete1200 synthetic native file shape binds raw q/action and log coverage.
frames,fixture=native;last=frames[-1];scene=last[3]['scene'];q=np.tile(last[3]['current'],(1200,1));u=np.tile(last[3]['final_command'],(1200,1));q[0]=0;u[0]=0;events=[];rows=[];coords=[];experts=[dict(step=0,mode='init',target_xyz=scene['target_xyz'])];laststep=last[3]['step'];ev=last[0]
for t in range(1,1200):
 if t<=laststep:
  event,row,co,k=copy.deepcopy(frames[t-1]);q[t]=k['current'];u[t]=k['final_command']
  # This full-shape fixture has zero solved-contact packets; normalize only its
  # explicitly hypothetical prefix filter, not the separately audited real prefix.
  if event.get('context') is not None:
   event['context']['filtered_load_n']=0.
   row['contact_load']['filtered_vertical_load_n']=0.
   if co.get('front_recontact_center_override') is not None:co['front_recontact_center_override']=event
  if event['kind'] in ('command','handover'):q[t-1]=k['previous_q'];u[t-1]=k['previous_command']
 else:
  event=dict(front_box_recenter_version='front_box_recenter_v1',kind='unchanged',reason='recovery_handover_already_complete',real_recontact_index=fixture['counter'],center_local_after=ev['captured_center_local'])
  row=dict(step=t,mode='top_press',recontacts=fixture['counter'],target_xyz=scene['target_xyz'],contact_load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=0.),front_recontact_captured_center_local=ev['captured_center_local'],projected_support_reference=ev['reference'],control_offset_local=ev['reference']['reference_local'])
  co=dict(step=t,inactive_anchor=ev['captured_inactive_anchor_world'],contact_normal_tracking=dict(target_local_up=ev['captured_normal_local_up']))
 events.append(dict(step=t,**event));rows.append(row);coords.append(dict(co,step=t));experts.append(dict(step=t,mode=row['mode'],target_xyz=row['target_xyz']))
assert max(abs(q[0]))==max(abs(u[0]))==0
parent=Path(tempfile.mkdtemp(prefix='front_recontact_audit_fixture_',dir='/tmp'));ep=parent/'fixture';ep.mkdir()
def save(name,obj):(ep/name).write_text(json.dumps(obj))
try:
 np.savez(ep/'raw.npz',q=np.c_[np.zeros((1200,12)),q],action=np.c_[np.zeros((1200,12)),u],task_id='push_box_to_bin')
 np.savez(ep/'trace.npz',box=np.tile(scene['target_xyz'],(1200,1)),mailer=np.tile(scene['other_xyz'],(1200,1)))
 np.savez(ep/'parcel_orientation.npz',box=np.tile(scene['target_quat'],(1200,1)),mailer=np.tile(scene['other_quat'],(1200,1)))
 save('FIXTURE_ONLY.json',dict(synthetic=True,training_ready=False));save('front_recontact_center.json',dict(selected=True,rows=events));save('frontal_bypass.json',dict(plan=dict(front_route_selected=True,front_initial_center_landing=dict(actual_core=dict(collision_core_size_xyz=scene['core_size']))),rows=rows));save('coordination.json',coords);save('expert_control.json',experts);save('self_clearance.json',dict(failure=None,recorded_frames=1200,requested_frames=1200));save('solved_contact_forces.json',dict(rows=[dict(after_action_step=t,parcel_contacts=[]) for t in range(1200)]))
 result=verify_files(ep);assert result['passed'] and result['handovers']==1
 try:audit(ep)
 except (FileNotFoundError,AssertionError,KeyError):negative.append('fixture_cannot_pass_provenance_wrapper')
 else:raise AssertionError('synthetic fixture admitted natively')
 # Wrong raw binding and missing frame are rejected without source exceptions.
 np.savez(ep/'raw.npz',q=np.c_[np.zeros((1200,12)),q+.001],action=np.c_[np.zeros((1200,12)),u],task_id='push_box_to_bin')
 try:verify_files(ep)
 except AssertionError:negative.append('raw_not_zero')
 else:raise AssertionError('nonzero accepted')
 np.savez(ep/'raw.npz',q=np.zeros((70,23)),action=np.zeros((70,23)),task_id='wait_no_package');save('front_recontact_center.json',dict(selected=False,rows=[]));wait=verify_files(ep);assert wait['passed'] and wait['wait']
 save('front_recontact_center.json',dict(selected=True,rows=[]))
 try:verify_files(ep)
 except AssertionError:negative.append('wait_selected')
 else:raise AssertionError('wait selected accepted')
finally:shutil.rmtree(parent)
paths=[Path(__file__),W/'audit_front_box_recenter_stream.py',W/'audit_front_recontact_center_events.py',W/'front_box_recenter_stage_source_binding.py',D/'ALL_ELIGIBLE_LIFECYCLE_PROBE.json',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_preflight.py']
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,affine_events=sum(x['commands'] for x in records),negative_cases=negative,native_shape_fixture_frames=1200,native_shape_fixture_verified_commands=result['verified_commands'],wait_shape_fixture_frames=70,temporary_fixtures_removed=True,source_sha256={str(p):sha(p) for p in paths},full_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'INDEPENDENT_STREAM_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,events=out['affine_events'],negative=len(negative))))
