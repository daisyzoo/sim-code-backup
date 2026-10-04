"""Reconstruct real controller history, then fixed-observation recovery forks.
Recorded adapter events and pressure observation summaries are replay inputs;
this does not revalidate their physical measurements or predict new dynamics.
"""
from pathlib import Path
import sys,copy,json,hashlib,datetime,traceback,ast
from types import SimpleNamespace as NS
import numpy as np
W=Path(__file__).resolve().parent; ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';D=W/'front_normal_prefix_recovery_r4';D.mkdir(exist_ok=False)
sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
from simfoundry.data.top_contact_bypass import rotation_xyzw,support_mesh
from simfoundry.data.projected_support_reference import projected_support_reference
from front_initial_center_adapter import apply as apply_initial
from front_recontact_center_adapter import apply as apply_recovery
from peak_load_update_trace import TracedPeakLoadControl
from margin_confirmed_position_release import ConfirmedPositionRelease
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_normal_nondegradation_runtime_candidate_v1 import FrontNormalNondegradation,commit_original_recovery
from front_box_recenter_runtime import FrontRecontactCenterRuntime
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840020/layout_840020_push_box_to_bin'
f=read(ep/'frontal_bypass.json');p=f['plan'];fr={r['step']:r for r in f['rows']};cs={r['step']:r for r in read(ep/'coordination.json')};pr={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']};pf={r['step']:r for r in read(ep/'peak_load_updates.json')['final_control_states']}
ie={r['step']:r for r in read(ep/'front_initial_center.json')['rows']};re={r['step']:r for r in read(ep/'front_recontact_center.json')['rows']};packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']}
with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
size=tuple(p['top_recontact']['contact_size_xyz']);osize=(.15,.145,.04);core=p['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']
s=FrontCopRouteState(FrontalBypassState(p,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),'right',size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,edge_speed_enabled=True,edge_core_size=core,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,corridor_midpoint_replan=True,corridor_lateral_replan=True)
s.position_release_monitor=ConfirmedPositionRelease(p['initial_target_xyz'][1],p['direction']);s.load=TracedPeakLoadControl(5.,min_bias_m=-.006);s.load.bind_owner(s)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_frames=0,max_waypoint_error_m=0.,recovery_forks=[],passed=False,training_ready=False,physics_started=False)
def inputs(t):
 r=fr[t];load=hand_target_vertical_load(packets[t-1],'right','parcel_box');contact=loaded_forward_margin(packets[t-1],'right','parcel_box',tr['box'][t],ori['box'][t],size,-1)
 args=(tr['palm_right'][t],tr['box'][t],tr['mailer'][t],footprint_radii(size,ori['box'][t])[0],footprint_radii(osize,ori['mailer'][t])[0])
 kw=dict(tip=r['observed_support_xyz'],quat=ori['box'][t],obstacle_quat=ori['mailer'][t],control_offset_local=r['control_offset_local'],load_n=load,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=contact)
 return args,kw
def observe(state,t):
 state.load._observation=copy.deepcopy(pr[t]['preceding_observation']);state.load._last_action_step=t
tree=ast.parse((S/'collect_paired_sorting.py').read_text())
recovery_node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp) and 'commit_original_recovery(normal_record' in ast.unparse(n))
recovery_code=compile(ast.fix_missing_locations(ast.Module(body=[recovery_node],type_ignores=[])),'<actual collector pressure recovery>','exec')
snapshots={}
try:
 for t in range(1,684):
  a,kw=inputs(t)
  # At a measured handover the saved row is post-adapter. Reconstruct the
  # incoming support reference using the actual pose and prior captured center.
  for events in [ie,re]:
   if events[t]['kind']=='handover':
    pose=np.asarray(events[t]['context']['observed_hand_pose']);center=re[t-1]['center_local_after'] if t>1 else None
    if center is None:center=ie[t-1]['center_local_after'] if t>1 else None
    ref=projected_support_reference(support_mesh()['right'],pose[:3,:3],np.asarray(rotation_xyzw(ori['box'][t]))[:,2],center_local=center)
    kw['tip']=(pose[:3,3]+pose[:3,:3]@ref['reference_local']).tolist();kw['control_offset_local']=ref['reference_local']
  observe(s,t);r=s.update(*a,**kw)
  assert s.load.updates[-1]==pr[t],(t,'pressure mutation mismatch')
  ref={k:np.array(v) for k,v in fr[t]['projected_support_reference'].items()}
  for events,adapter in [(ie,apply_initial),(re,apply_recovery)]:
   r,ref=adapter(r,s,ref,events[t],object_xyz=tr['box'][t],object_rotation=np.asarray(rotation_xyzw(ori['box'][t])))
  err=float(np.max(abs(np.asarray(r['target_xyz'])-np.asarray(fr[t]['target_xyz']))));report['max_waypoint_error_m']=max(err,report['max_waypoint_error_m'])
  assert err<2e-7,(t,'waypoint mismatch',err)
  for key in ['mode','route_stage','recontacts','route_stop_reason','last_recontact_reason']:assert r.get(key)==fr[t].get(key),(t,key,r.get(key),fr[t].get(key))
  assert s.load.bias_m==pf[t]['bias_m'] and s.load.filtered_n==pf[t]['filtered_n'],(t,'final pressure state')
  report['baseline_frames']+=1
  if t in (682,683):snapshots[t]=copy.deepcopy(s)
 report['baseline_reconstructed']=True
 guard=ClearanceGuard(ROOT,S);controller=FrontNormalNondegradation(guard,ROOT,S,enabled=True)
 for t,state in snapshots.items():
  c=cs[t];tc=c['joint_transport_clearance']['collector_context'];v=tc['scene'];scene=RecontactScene(guard,v['side'],v['target_xyz'],v['target_quat'],v['core_size'],v['other_xyz'],v['other_quat'],v['other_size'])
  u,record=controller.refine(step=t,selected=True,side='right',row=fr[t],coordinate=c,scene=scene,current=tc['current'],previous_q=tc['previous_q'],previous_command=tc['previous_command'],parent_command=c['joint_transport_clearance']['output_command'],decay=tc['decay'])
  assert record['requires_recovery'] and not record['requires_stop'];old_filter=state.load.filtered_n;old_count=state.recontacts
  fg=guard.command(u,tc['current'],tc['previous_command'])
  pressure_log=[copy.deepcopy(pf[t])]
  args=NS(front_normal_nondegradation=True,peak_load_bias_guard=True)
  def env(st,rec,log,final):return dict(args=args,step=t,normal_record=rec,frontal_state=st,final_clearance=final,peak_load_frame_log=log)
  negative=[]
  for label in ['stale_step','wrong_bias','wrong_filter','wrong_update_count','rejected_final']:
   ss=copy.deepcopy(state);rec=copy.deepcopy(record);pl=copy.deepcopy(pressure_log);ff=copy.deepcopy(fg)
   if label=='stale_step':pl[-1]['step']-=1
   elif label=='wrong_bias':pl[-1]['bias_m']+=.001
   elif label=='wrong_filter':pl[-1]['filtered_n']+=.1
   elif label=='wrong_update_count':pl[-1]['pressure_update_count']+=1
   else:ff['accepted']=False
   before=(ss.top_mode,ss.recontacts,ss.load.bias_m,ss.load.filtered_n);rp=copy.deepcopy(rec);lp=copy.deepcopy(pl)
   try:exec(recovery_code,env(ss,rec,pl,ff))
   except ValueError:pass
   else:raise AssertionError(('invalid pressure/final accepted',label))
   assert before==(ss.top_mode,ss.recontacts,ss.load.bias_m,ss.load.filtered_n) and rec==rp and pl==lp
   negative.append(label)
  exec(recovery_code,env(state,record,pressure_log,fg));event=record['recovery_transition']
  final_pressure=pressure_log[-1]
  assert final_pressure['before_final_recovery']==pf[t] and final_pressure['final_recovery_transition']==event
  assert final_pressure['top_mode']=='top_lift' and final_pressure['bias_m']==0. and final_pressure['filtered_n']==old_filter
  assert final_pressure['pressure_update_count']==pf[t]['pressure_update_count']
  unchanged=copy.deepcopy(final_pressure)
  try:exec(recovery_code,env(state,record,pressure_log,fg))
  except ValueError:pass
  else:raise AssertionError('duplicate finalization accepted')
  assert pressure_log[-1]==unchanged
  negative.append('duplicate_commit')
  assert state.load.filtered_n==old_filter and state.load.bias_m==0.
  # The archived counter-4 lifecycle finished at its measured handover.
  # Only its inactivity and captured reference are needed: a new counter
  # constructs a fresh lifecycle before inspecting old planning internals.
  assert re[t]['reason']=='recovery_handover_already_complete'
  bridge=FrontRecontactCenterRuntime(guard,'right',core,osize,tc['decay'],enabled=True)
  bridge.last_counter=old_count;bridge.center_local=np.asarray(re[t]['center_local_after'])
  original_center=bridge.center_local.copy();rows=[];planned=False
  fixture_fr=[copy.deepcopy(fr[k]) for k in range(1,t+1)]
  fixture_finals=[copy.deepcopy(pf[k]) for k in range(1,t)]+[copy.deepcopy(final_pressure)]

  for nt in range(t+1,694):
   a,kw=inputs(nt);observe(state,nt);r=state.update(*a,**kw)
   assert r['mode'] in ('top_lift','top_cross') and state.recontacts==old_count+1,(nt,'unexpected recovery phase')
   assert not r['cop_slip_following']['override'] and state.cop_slip.local_anchor is None
   assert state.load.bias_m==0. and r['contact_load']['applied_z_bias_m']==0.
   if r['mode']=='top_lift':assert np.max(abs(np.array(r['target_xyz'][:2])-np.array(fr[t]['observed_support_xyz'][:2])))<2e-7
   nc=cs[nt]['joint_transport_clearance']['collector_context'];ns=nc['scene'];q=np.asarray(nc['current'])
   # Observed poses are archived on eligible planning rows; on lift rows
   # the lifecycle exits before reading poses, but provide FK explicitly.
   hp=guard.model.fk('right',q)[0];ip=guard.model.fk('left',q)[0]
   pose_source='FK (lift gate does not consume pose)'
   if 'context' in re[nt]:
    hp=np.asarray(re[nt]['context']['observed_hand_pose']);ip=np.asarray(re[nt]['context']['observed_inactive_hand_pose']);pose_source='archived measured poses'
   ref=projected_support_reference(guard.model.vertices['right'],hp[:3,:3],np.asarray(rotation_xyzw(ori['box'][nt]))[:,2],center_local=bridge.center_local)
   rr,newref,be=bridge.update(r,state,ref,selected=True,step=nt,current=q,previous_q=nc['previous_q'],previous_command=u if nt==t+1 else nc['previous_command'],target_xyz=ns['target_xyz'],target_quat=ns['target_quat'],other_xyz=ns['other_xyz'],other_quat=ns['other_quat'],observed_load_n=kw['load_n'],observed_hand_pose=hp,observed_inactive_hand_pose=ip,normal_anchor=re[nt]['old_normal_anchor'],inactive_anchor=re[nt]['old_inactive_anchor'])
   assert be['kind']!='stop',(nt,be)
   fixture_fr.append(dict(copy.deepcopy(rr),step=nt))
   fixture_finals.append(dict(step=nt,mode=rr['mode'],top_mode=state.top_mode,bias_m=state.load.bias_m,filtered_n=state.load.filtered_n,pressure_update_count=len(state.load.updates)))
   assert bridge.last_counter==old_count+1 and np.array_equal(bridge.center_local,original_center)
   if r['mode']=='top_lift':assert be['kind']=='unchanged' and not bridge.lifecycle.attempted
   rows.append(dict(step=nt,mode=r['mode'],recontacts=state.recontacts,target_xyz=r['target_xyz'],load=r['contact_load'],cop=r['cop_slip_following'],bridge_event=be,pose_source=pose_source))
   if be['kind']=='command':
    assert bridge.lifecycle.active and bridge.lifecycle.attempted and not bridge.lifecycle.finished
    assert bridge.lifecycle.recontact_index==old_count+1
    fg=guard.command(np.asarray(be['command']),q,np.asarray(nc['previous_command']));assert fg['accepted']
    rows[-1]['planning_final_guard']=fg;planned=True;break
  assert planned,(t,'No verified planning command by 693')
  n=rows[-1]['step']+1
  with np.load(ep/'raw.npz') as z:fixture_q=z['q'][:n,12:23].astype(float);fixture_u=z['action'][:n,12:23].astype(float)
  fixture_u[t]=u;fixture_u[-1]=rows[-1]['bridge_event']['command']
  normal=[];guards=[]
  for k in range(n):
   normal.append(copy.deepcopy(record) if k==t else dict(step=k,enabled=True,selected=False,applied=False,requires_stop=False,requires_recovery=False,parent_command=fixture_u[k].tolist(),output_command=fixture_u[k].tolist(),training_ready=False,reason='pressure_auditor_fixture_passthrough'))
   gr=guard.command(fixture_u[k],fixture_q[k],fixture_u[k-1] if k else np.zeros(11),first=(k==0));assert gr['accepted'],(t,k,'fixture guard')
   guards.append(dict(gr,step=k))
  fixture=dict(scope='Pressure-consumer diagnostic only: historical observations, new recovery state, and original subsequent actions until the first unexecuted planning command. Not a physically collected candidate stream.',frames=n,frontal=dict(plan=p,rows=fixture_fr,training_ready=False),pressure=dict(rows=state.load.updates,final_control_states=fixture_finals,executed_action_count=n,wait=False,training_ready=False),normal_records=normal,final_guards=guards,current=fixture_q.tolist(),actions=fixture_u.tolist(),training_ready=False)
  (D/f'PRESSURE_FORK_{t}.json').write_text(json.dumps(fixture,indent=2,allow_nan=False))
  report['recovery_forks'].append(dict(step=t,commit=event,retained_filter_n=old_filter,rows=rows,first_replanning_step=rows[-1]['step'],planning_command_unexecuted=True,final_pressure_record=final_pressure,negative_native_cases=negative))
 report['passed']=True
except Exception as exc:
 report['error']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());traceback.print_exc()
finally:
 report['source_sha256']={str(q):sha(q) for q in [Path(__file__),S/'collect_paired_sorting.py',S/'front_initial_center_cop_route.py',S/'front_initial_center_route.py',S/'front_initial_center_top_contact.py',S/'front_normal_nondegradation_runtime_candidate_v1.py',*[ep/n for n in ['frontal_bypass.json','coordination.json','peak_load_updates.json','front_initial_center.json','front_recontact_center.json','trace.npz','parcel_orientation.npz','solved_contact_forces.json']]]}
 (D/'RESULT.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({k:report[k] for k in ['passed','baseline_frames','max_waypoint_error_m']},indent=2),flush=True)
if not report['passed']:sys.exit(1)
