"""Explicit synthetic native-file fixtures, not physical episodes or training data.
Test full 1200-frame accepted bag/box, budget fallback, disabled route, 70-frame wait,
independent normal math and forged-file rejection. Other task/control gates remain required.
"""
from pathlib import Path
import sys,json,hashlib,datetime,os,copy,tempfile
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_initial_center_lifecycle_v3 import FrontInitialCenterLifecycle
from audit_front_initial_center_live_v2 import verify_files
from audit_front_initial_center_events import EventAudit
from audit_front_initial_center_normal import verify_normal_rows
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(ROOT,S);independent=EventAudit(ROOT,S)
source=W/'FRONT_INITIAL_CENTER_SELECTION_CHECK.json';data=json.loads(source.read_text())
out=W/'FRONT_INITIAL_CENTER_NATIVE_V2_CHECK.json';assert not out.exists()
report=dict(status='running',pid=os.getpid(),scope=__doc__,positive_cases=[],negative_cases=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),source,W/'audit_front_initial_center_live_v2.py',W/'audit_front_initial_center_planning_v2.py',W/'audit_front_initial_center_normal.py']})
def save():
 report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=out.with_suffix('.tmp');p.write_text(json.dumps(report,indent=2));p.replace(out)
def put(ep,name,obj): (ep/name).write_text(json.dumps(obj))
def normal_record(q,side,anchor):
 current=independent.hand.fk(q,side)[2,:3];J=np.empty((3,11));h=1e-6
 for i in range(11):
  v=np.zeros(11);v[i]=h;J[:,i]=.15*(independent.hand.fk(q+v,side)[2,:3]-independent.hand.fk(q-v,side)[2,:3])/(2*h)
 return dict(current_local_up=current.tolist(),target_local_up=list(anchor),error=(.15*np.clip(.72*(np.asarray(anchor)-current),-.1,.1)).tolist(),angle_error_rad=float(np.arccos(np.clip(current@anchor,-1,1))),weight_m=.15,jacobian=J.tolist())
def make(ep,original):
 ep.mkdir();p=copy.deepcopy(original['plan']);z=p['scene'];ctx=original['live_first_event']['context'];q=np.array(ctx['current']);qp=np.array(ctx['previous_q']);prev=np.array(ctx['previous_command']);decay=np.array(ctx['decay']);start=ctx['step'];task='push_box_to_bin' if z['side']=='right' else 'nudge_mailer_to_bin';side=z['side'];other='left' if side=='right' else 'right'
 scene=RecontactScene(guard,side,z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);life=FrontInitialCenterLifecycle(enabled=True)
 qs=np.zeros((1200,23));us=qs.copy();front=[];fr=[];coords=[];experts=[dict(step=0,mode='fixture_initial',target_xyz=[0.,0.,0.])];packets=[];verified={};captured=None;anchor=None
 for t in range(1,1200):
  if t<start:
   qs[t,12:23]=qp*(t/(start-1));us[t,12:23]=prev*(t/(start-1));event=dict(kind='unchanged',reason='not_initial_front_unloaded_phase');mode='top_lift'
  else:
   qs[t,12:23]=q
   inp=dict(step=t,selected=True,parent_mode='top_cross',recontacts=0,guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=decay,observed_hand_pose=guard.model.fk(side,q)[0],observed_inactive_hand_pose=guard.model.fk(other,q)[0])
   with patch('front_initial_center_lifecycle_v3.plan',return_value=p):event=life.update(**inp)
   assert event['kind']!='stop',event.get('reason')
   us[t,12:23]=event.get('command',prev);mode='top_press' if event['kind']=='handover' or captured else 'top_cross'
   if event['kind'] in ('command','handover'):verified[t]=event
   if event['kind']=='handover':captured=event;anchor=event['captured_inactive_anchor_world']
  load=dict(observed_vertical_load_n=0.,filtered_vertical_load_n=0.,applied_z_bias_m=0.,stored_z_bias_m=0.)
  row=dict(step=t,mode=mode,recontacts=0,contact_load=load,target_xyz=z['target_xyz'])
  coord=dict(step=t,controller_kind='fixture_parent_task',inactive_anchor=anchor,contact_normal_tracking=None,task_inputs=None,contact_bout_yaw_tracking=None,upper_q=qs[t,12:23].tolist(),active_side=side,bounded_solver=True)
  if captured:
   center=np.array(captured['captured_center_local']);pose=independent.hand.fk(qs[t,12:23],side);R=pose[:3,:3];normal=scene.rotation[:,2];local=R.T@normal;verts=independent.hand.vertices[side];ref=center+local*(min(verts@local)-center@local)
   event['center_local_after']=center.tolist();row.update(front_initial_captured_center_local=center.tolist(),projected_support_reference=dict(center_local=center.tolist(),reference_local=ref.tolist()),control_offset_local=ref.tolist())
   if event['kind'] not in ('command','handover'):
    if t==max(verified)+1:norm=normal_record(qs[t,12:23],side,captured['captured_normal_local_up'])
    coord['contact_normal_tracking']=norm
  if event['kind'] in ('command','handover'):coord.update(controller_kind='verified_unloaded_front_initial_joint_path',front_initial_center_override=event)
  front.append(dict(step=t,**event));fr.append(row);coords.append(coord);experts.append(dict(step=t,mode=mode,target_xyz=row['target_xyz']))
  if t>=start and not captured and p['accepted']:
   command=us[t,12:23];bias=q-prev-decay*(qp-prev);nq=(1-decay)*command+decay*q+bias;qp,q,prev=q,nq,command.copy()
  elif t>=start:qp=q.copy();prev=us[t,12:23].copy()
 for t in range(1200):packets.append(dict(after_action_step=t,parcel_contacts=[]))
 np.savez_compressed(ep/'raw.npz',q=qs,action=us,task_id=task,fixture_only=True)
 key='box' if side=='right' else 'mailer';other_key='mailer' if key=='box' else 'box'
 np.savez_compressed(ep/'trace.npz',**{key:np.tile(z['target_xyz'],(1200,1)),other_key:np.tile(z['other_xyz'],(1200,1))})
 np.savez_compressed(ep/'parcel_orientation.npz',**{key:np.tile(z['target_quat'],(1200,1)),other_key:np.tile(z['other_quat'],(1200,1))})
 put(ep,'front_initial_center.json',dict(selected=True,rows=front,training_ready=False))
 put(ep,'frontal_bypass.json',dict(plan=dict(front_route_selected=True,front_initial_center_landing=dict(actual_core=dict(collision_core_size_xyz=z['core_size']))),rows=fr))
 put(ep,'coordination.json',coords);put(ep,'expert_control.json',experts);put(ep,'solved_contact_forces.json',dict(rows=packets));put(ep,'self_clearance.json',dict(failure=None,recorded_frames=1200,requested_frames=1200))
 return dict(q=qs[:,12:23],coords=coords,experts={r['step']:r for r in experts},verified=verified,side=side,first=start,handover=next((t for t,e in verified.items() if e['kind']=='handover'),None))
try:
 save()
 with tempfile.TemporaryDirectory(prefix='front-native-synthetic-') as tmp:
  base=Path(tmp);chosen=[r for r in data['records'] if any(n in r['episode'] for n in ['840004','840016','840023'])];instances=[]
  for r in chosen:
   ep=base/r['episode'];obj=make(ep,r);result=verify_files(ep);normal=verify_normal_rows(obj['q'],obj['coords'],obj['experts'],set(range(1,1200)),{},independent.hand,obj['side'],verified_front_events=obj['verified'])
   assert result['handovers']==int(r['plan']['accepted']);instances.append((ep,obj))
   report['positive_cases'].append(dict(episode=r['episode'],frames=1200,commands=result['verified_commands'],handover=result['handovers'],normal_frames=normal['normal_frames'],jacobian_samples=normal['jacobian_samples'],independent_file_check=True));save();print(r['episode'],result['verified_commands'],result['handovers'],flush=True)
  ep,obj=instances[-1]
  cases=['duplicate_force_packet','missing_force_packet','missing_front_row','wrong_action','wrong_actual_q','missing_command_event','unfinished_path','changed_capture','changed_post_capture_anchor','changed_post_capture_reference','second_plan','erased_required_plan']
  for label in cases:
   original_files={n:(ep/n).read_bytes() for n in ['raw.npz','front_initial_center.json','coordination.json','solved_contact_forces.json','frontal_bypass.json']}
   first=obj['first'];handover=obj['handover']
   if label in ('duplicate_force_packet','missing_force_packet'):
    x=json.loads((ep/'solved_contact_forces.json').read_text());x['rows'].append(x['rows'][0]) if label.startswith('duplicate') else x['rows'].pop();put(ep,'solved_contact_forces.json',x)
   elif label in ('wrong_action','wrong_actual_q'):
    with np.load(ep/'raw.npz') as z:a={k:z[k] for k in z.files}
    a['action' if label=='wrong_action' else 'q'][first,12]+=.001;np.savez_compressed(ep/'raw.npz',**a)
   elif label in ('changed_post_capture_anchor','changed_post_capture_reference'):
    name='coordination.json' if label.endswith('anchor') else 'frontal_bypass.json';x=json.loads((ep/name).read_text());rows=x if isinstance(x,list) else x['rows'];row=next(r for r in rows if r['step']==handover+1)
    if label.endswith('anchor'):row['inactive_anchor'][0]+=.001
    else:row['projected_support_reference']['reference_local'][0]+=.001
    put(ep,name,x)
   else:
    x=json.loads((ep/'front_initial_center.json').read_text());rows=x['rows']
    if label=='missing_front_row':rows.pop(first)
    elif label=='changed_capture':rows[handover-1]['captured_center_local'][0]+=.001
    elif label=='second_plan':rows[first]['planning']=copy.deepcopy(rows[first-1]['planning'])
    elif label=='unfinished_path':
     # Relabel every row after the first command unchanged: a missing active-path
     # interval must be rejected even with a nominal full horizon.
     for i in range(first,len(rows)):rows[i]=dict(step=i+1,kind='unchanged',reason='no_new_unloaded_initial_attempt')
    else:
     i=first if label=='missing_command_event' else first-1;rows[i]=dict(step=i+1,kind='unchanged',reason='no_new_unloaded_initial_attempt')
     cs=json.loads((ep/'coordination.json').read_text());cs[i].pop('front_initial_center_override',None);cs[i]['controller_kind']='fixture_parent_task';put(ep,'coordination.json',cs)
    put(ep,'front_initial_center.json',x)
   rejected=False
   try:verify_files(ep)
   except (AssertionError,ValueError,KeyError,StopIteration):rejected=True
   finally:
    for n,b in original_files.items():(ep/n).write_bytes(b)
   assert rejected,label;report['negative_cases'].append(dict(case=label,rejected=True));save();print(label,'rejected',flush=True)
  # Pure schema branches: empty wait and nonselected route, no physical claim.
  wait=base/'synthetic_wait';wait.mkdir();np.savez_compressed(wait/'raw.npz',q=np.zeros((70,23)),action=np.zeros((70,23)),task_id='wait_no_package',fixture_only=True);put(wait,'front_initial_center.json',dict(selected=False,rows=[],training_ready=False));assert verify_files(wait)['passed'];report['positive_cases'].append(dict(case='wait',frames=70,passed=True))
  plain=base/'synthetic_parent';plain.mkdir();n=1200;np.savez_compressed(plain/'raw.npz',q=np.zeros((n,23)),action=np.zeros((n,23)),task_id='push_box_to_bin',fixture_only=True)
  put(plain,'front_initial_center.json',dict(selected=False,rows=[],training_ready=False));put(plain,'frontal_bypass.json',dict(plan=dict(front_route_selected=False),rows=[dict(step=t) for t in range(1,n)]));put(plain,'coordination.json',[dict(step=t) for t in range(1,n)]);put(plain,'expert_control.json',[dict(step=t) for t in range(n)]);assert verify_files(plain)['passed'];report['positive_cases'].append(dict(case='nonselected_parent',frames=1200,passed=True))
  for label in ['unverified_front_event','wrong_normal_gain','wrong_normal_jacobian','conflicting_rear_event']:
   args=copy.deepcopy(obj);coords=args['coords'];verified=args['verified'];rear={};t=args['handover']+1
   if label=='unverified_front_event':verified={}
   if label=='conflicting_rear_event':rear=copy.deepcopy(verified)
   if label=='wrong_normal_gain':coords[t-1]['contact_normal_tracking']['weight_m']=.16
   if label=='wrong_normal_jacobian':next(r for r in coords if r['step']>t and r['step']%20==0)['contact_normal_tracking']['jacobian'][0][0]+=.001
   rejected=False
   try:verify_normal_rows(args['q'],coords,args['experts'],set(range(1,1200)),rear,independent.hand,args['side'],verified_front_events=verified)
   except (AssertionError,ValueError):rejected=True
   assert rejected,label;report['negative_cases'].append(dict(case=label,rejected=True));save()
 report.update(status='complete',passed=True);save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
