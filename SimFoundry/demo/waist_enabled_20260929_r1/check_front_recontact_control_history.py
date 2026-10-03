"""Actual staged front-bag recovery pressure/COP/reference transition fixtures.
Uses the real parent _start_recontact transition; positive counter stays intact.
Manufactured measured endpoints and contact packets test interfaces only, not
physical feasibility, full episodes, task quality or training admission.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
from front_recontact_center_adapter import apply
from peak_load_update_trace import TracedPeakLoadControl
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from simfoundry.data.projected_support_reference import projected_support_reference
from audit_front_recontact_v1_stage_pressure import verify_stream
from audit_front_diagonal_entry_live import reconstruct
from audit_front_recontact_v1_stage_front_height import audit as audit_height
from audit_front_recontact_v1_stage_initial_near_half import audit_log
from front_recontact_reference_ledger import verified_reference_lifetimes
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
guard=ClearanceGuard(ROOT,S);probe=json.loads((W/'FRONT_INITIAL_CENTER_LANDING_PROBE.json').read_text())
out=S/'CONTROL_HISTORY_CHECK.json';assert not out.exists();report=dict(status='running',scope=__doc__,records=[],negative=[],simulation_started=False,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',W/'audit_front_recontact_v1_stage_pressure.py',W/'audit_front_diagonal_entry_live.py',W/'audit_front_recontact_v1_stage_front_height.py',W/'audit_front_recontact_v1_stage_initial_near_half.py',W/'front_recontact_reference_ledger.py']})
def save():report['updated_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(report,indent=2))
try:
 save()
 for original in probe['records']:
  if original['scene']['side']!='left':continue
  z=original['scene'];side=z['side'];target=z['target_xyz'];other=z['other_xyz'];quat=z['target_quat'];other_quat=z['other_quat'];size=z['core_size'];other_size=z['other_size'];key='box' if side=='right' else 'mailer';other_key='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer'
  scene=RecontactScene(guard,side,target,quat,size,other,other_quat,other_size);ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+original['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());plan=copy.deepcopy(fr['plan']);first=next(r for r in fr['rows'] if r['step']==original['step'])
  state=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(plan)),side,tuple(size),obstacle_size=tuple(other_size),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,route_clearance_m=.012,recontact_travel_z=.86,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=plan["front_cop_slip_following"]["edge_speed"]["actual_core_size_xyz"])
  state.load=TracedPeakLoadControl(5.,min_bias_m=-.006);state.load.bind_owner(state)
  chosen=min([x for x in original['attempts'] if x['accepted_endpoint'] and x['nominal_path']['independently_accepted']],key=lambda v:v['objective']);q=np.array(chosen['candidate_q']);detail=scene.details(q);pose=detail['hand_pose'];center=detail['vertex_local'];reference=projected_support_reference(guard.model.vertices[side],pose[:3,:3],scene.rotation[:,2],center_local=center);tip=pose[:3,3]+pose[:3,:3]@reference['reference_local'];local=scene.rotation.T@(tip-scene.target)
  handover=dict(kind='handover',context=dict(recontacts=1),real_recontact_index=1,measured_ready_count=3,captured_center_local=center.tolist(),reference={k:reference[k].tolist() for k in ['reference_local','center_local','lowest_vertex_local','world_normal']},observed_support_xyz=tip.tolist(),selected_surface_local_xy=local[:2].tolist())
  rows=[];finals=[];events={};packets={};loads={};captured=False;N=18
  for t in range(1,N):
   load=0. if t<=4 else 5.;loads[t-1]=[load]*24;state.load.observe(action_step=t,after_action_step=t-1,vertical_load_n=loads[t-1])
   measured=first['observed_support_xyz'] if t==1 else tip.tolist()
   if t==2:state._start_recontact(measured,'lost_contact');state.top_mode='top_cross'
   contact_point=(scene.target+scene.rotation@np.r_[local[:2],scene.core[2]/2]).tolist()
   contacts=[] if load==0 else [dict(shapes=['/robot/'+side+'_wrist_roll_link','/scene/'+actor+'/shape'],force_world_N=[0.,0.,-load],position_world=contact_point)]
   packets[t-1]=dict(after_action_step=t-1,parcel_contacts=contacts,post_action_pose={key:target,other_key:other})
   normal=load*float(scene.rotation[2,2]);slip=None if load==0 else dict(valid=True,normal_load_n=normal,weighted_contact_local=np.r_[local[:2],scene.core[2]/2].tolist())
   row=state.update(target,target,other,size[0]/2,other_size[0]/2,tip=measured,quat=quat,obstacle_quat=other_quat,control_offset_local=reference['reference_local'].tolist(),load_n=load,hand_obstacle_gap_m=.1,slip_contact=slip)
   if 2<=t<=4:
    event=copy.deepcopy(handover) if t==4 else dict(kind='command',context=dict(recontacts=1),real_recontact_index=1)
    row,reference=apply(row,state,reference,event,object_xyz=target,object_rotation=scene.rotation);events[t]=event
    if t==4:captured=True
   if captured:row['front_recontact_captured_center_local']=center.tolist()
   rows.append(dict(row,step=t));finals.append(dict(step=t,mode=row['mode'],top_mode=state.top_mode,bias_m=state.load.bias_m,filtered_n=state.load.filtered_n,pressure_update_count=len(state.load.updates)))
  loads[N-1]=[5.]*24
  log=dict(plan=plan,rows=rows);pressure=dict(rows=state.load.updates,final_control_states=finals,executed_action_count=N,wait=False,training_ready=False)
  press=verify_stream(pressure,log,loads,frames=N,wait=False)
  tr={key:np.tile(target,(N,1)),other_key:np.tile(other,(N,1))};ori={key:np.tile(quat,(N,1)),other_key:np.tile(other_quat,(N,1))}
  cop,cop_errors=reconstruct(rows,plan,tr,ori,packets,key);assert not cop_errors,cop_errors
  assert len(cop)>0,'Fixture must exercise loaded COP after capture'
  assert state.recontacts==1 and all(e['context']['recontacts']==1 for e in events.values())
  height=audit_height(log,rows,verified_front_recovery_events=events);assert height['passed'],height['errors']
  ledger=verified_reference_lifetimes(rows,{},events,side=side)
  # Bind constructor size explicitly; this fixture uses actual collision-core dimensions.
  plan['top_recontact']['contact_size_xyz']=list(size)
  surface=audit_log(log,ori[key],.5,ledger['surface_local_by_step']);assert surface['passed'],surface['errors']
  report['records'].append(dict(episode=original['episode'],pressure_updates=press['pressure_updates'],cop_loaded_frames=len(cop),reference_frames=len(ledger['centers']),surface_frames=surface['checked_frames'],height_frames=height['normal_rows'],current_class_history_passed=True));save();print(original['episode'],'pressure/COP/height/surface',len(cop),flush=True)
  if len(report['records'])==1:
   for label in ['pressure_bias_after_capture','pressure_filter_reset','surface_without_capture','unverified_joint_height','cop_previous_command']:
    pp=copy.deepcopy(pressure);ll=copy.deepcopy(log);rejected=False
    if label=='pressure_bias_after_capture':pp['final_control_states'][3]['bias_m']=.001
    elif label=='pressure_filter_reset':pp['final_control_states'][6]['filtered_n']=0.
    elif label=='surface_without_capture':
     rr=audit_log(ll,ori[key],.5,{});rejected=not rr['passed']
    elif label=='unverified_joint_height':
     ll['rows'][1]['target_xyz']=list(ll['rows'][1]['target_xyz']);ll['rows'][1]['target_xyz'][2]=.86;rr=audit_height(ll,ll['rows']);rejected=not rr['passed']
    else:
     rr=next(r for r in ll['rows'] if r['cop_slip_following'].get('override'));rr['cop_slip_following']['previous_command_xy'][0]+=.001;_,err=reconstruct(ll['rows'],plan,tr,ori,packets,key);rejected=bool(err)
    if label.startswith('pressure_'):
     try:verify_stream(pp,ll,loads,frames=N,wait=False)
     except (AssertionError,ValueError):rejected=True
    assert rejected,label;report['negative'].append(dict(case=label,rejected=True));save()
 report.update(status='complete',passed=True);save()
except Exception as e:report.update(status='failed',error=repr(e));save();raise
