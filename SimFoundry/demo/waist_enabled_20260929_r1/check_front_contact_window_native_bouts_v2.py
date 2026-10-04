"""Real recorded loaded bouts through actual collector constructor and front stack.
Each bout seeds current recorded parent state once, then both native controllers
carry their own history. Future observations remain recorded; no dynamic outcome,
unloaded planner rollout, IK or final-command guard certification is claimed.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,sys,copy,json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
from front_window_native_v4 import WindowFrontCopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState,extent_x_from_quat
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from peak_load_update_trace import TracedPeakLoadControl
from margin_confirmed_position_release import ConfirmedPositionRelease
from clearance_runtime import ClearanceGuard
from peak_load_observation import extract
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};results=[]
def bound(p):sources[str(p)]=sha(p);return p
def read(p):return json.loads(bound(p).read_text())
nodes=list(ast.walk(ast.parse(bound(S/'collect_paired_sorting.py').read_text())));construct=next(n for n in nodes if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='top_cls');code=compile(ast.Module(body=[construct],type_ignores=[]),'<actual collector constructor>','exec');guard=ClearanceGuard(ROOT,S)
for case,task,side,key,other_key,actor in [(840023,'nudge_mailer_to_bin','left','mailer','box','mailer'),(840020,'push_box_to_bin','right','box','mailer','parcel_box')]:
 ep=W/'front_loaded_z_quarter_physical_r2'/f'case_{case}'/f'layout_{case}_{task}';args=NS(**read(ep.parent/'provenance.json')['args']);fr=read(ep/'frontal_bypass.json');plan=fr['plan'];rows={r['step']:r for r in fr['rows']};experts=read(ep/'expert_control.json');packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']}
 with np.load(bound(ep/'raw.npz')) as z:q=z['q'][:,12:23]
 with np.load(bound(ep/'trace.npz')) as z:trace={k:z[k].astype(float) for k in z.files}
 with np.load(bound(ep/'parcel_orientation.npz')) as z:ori={k:z[k].astype(float) for k in z.files}
 meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert meta['recording_sha256']==sha(ep/'substep_contacts.npz');m=meta['metadata'];stride=24+m['expected_manager_steps']
 with np.load(bound(ep/'substep_contacts.npz')) as z:a={k:z[k].copy() for k in z.files}
 other_size=(.15,.145,.04) if side=='right' else (.14,.095,.045);size=tuple(plan['top_recontact']['contact_size_xyz']);core=tuple(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'])
 def make(enabled,lo):
  extra=dict(obstacle_size=other_size,route_clearance_m=args.expert_front_clearance_m,recover_clearance=args.expert_front_recover_clearance,confirm_nominal_clearance=args.expert_front_confirm_nominal_clearance,object_relative_lead=args.expert_front_object_relative_lead,recontact_travel_z=args.expert_front_recontact_z,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,corridor_midpoint_replan=True,corridor_lateral_replan=True,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=args.front_cop_drive_step_m,edge_speed_enabled=True,edge_core_size=core)
  if enabled:extra.update(contact_window_enabled=True,contact_window_selected_front=True)
  env=dict(top_cls=WindowFrontCopRouteState if enabled else FrontCopRouteState,frontal_state=FrontalBypassState(copy.deepcopy(plan)),side=side,contact_size=size,top_extra=extra,args=args,front_route_selected=True,effective_drag_step_m=.003,effective_top_fraction=plan['top_recontact']['effective_top_fraction']);exec(code,env);s=env['frontal_state'];r=rows[lo];f=r['contact_load'];R=Rotation.from_quat(ori[key][lo]).as_matrix()
  s.top_mode=s.mode='top_push';s.mode_step=experts[lo]['mode_step'];s.command=tuple(r['target_xyz']);s.last_emitted_xy=tuple(r['target_xyz'][:2]);s.last_route_stage=s.route_stage=r['route_stage'];s.push_x_anchor=r['push_x_anchor_m'];s.recontacts=r['recontacts'];s.last_recontact_reason=r['last_recontact_reason'];s.approach_xy_bias=list(r['approach_xy_bias_m']);s.lost_contact_steps=0;s.start=tuple(r['observed_support_xyz']);s.descent_z=r['observed_support_xyz'][2]
  s.selected_surface_local_xy=tuple((R.T@(np.array(r['parcel_top_xyz'])-trace[key][lo]))[:2]);s.route_report=copy.deepcopy(plan['front_route_candidates']);s.route_x=next(r for r in s.route_report['candidates'] if r['route']=='front')['waypoints_xy'][1][0]-.003
  c=r['clearance_progress'];s.clearance_progress=FrontClearanceProgress(s.route_clearance_m,c['front_hold_y'],stage=c['route_stage'],recoveries=c['clearance_recovery_count'],confirm_nominal_clearance=c['nominal_clearance_confirmation'],safe_observations=c['safe_clearance_observations'],recovery_hysteresis_m=c['recovery_hysteresis_m'])
  micro=r['direction_change_recontact']['micro_repair_retention'];reset=r['direction_change_recontact']['stage_changed'] and r['route_stage']=='lateral_y';s.micro_return.start_xy=None if reset else micro['repair_start_xy'];s.micro_return.maximum_excursion_m=0. if reset else micro['maximum_excursion_m']
  cop=r['cop_slip_following']
  if cop['override']:s.cop_slip.local_anchor=np.array(cop['anchor_local']);s.cop_slip.previous_anchor_world=trace[key][lo]+R@s.cop_slip.local_anchor
  s.load=TracedPeakLoadControl(5.,bias_m=f['stored_z_bias_m'],filtered_n=f['filtered_vertical_load_n'],min_bias_m=-.006);s.load.bind_owner(s);s.load._last_action_step=lo
  s.position_release_monitor=ConfirmedPositionRelease(plan['initial_target_xyz'][1],plan['direction'])
  for xyz in trace[key][max(0,lo-9):lo+1]:s.position_release_monitor.observe(xyz)
  return s
 bouts=[];start=None
 for t,r in rows.items():
  if r['mode']=='top_push' and start is None:start=t
  if r['mode']!='top_push' and start is not None:bouts.append((start,t));start=None
 if start is not None:bouts.append((start,max(rows)))
 for lo,end in bouts:
  off=make(False,lo);on=make(True,lo);records=[]
  for t in range(lo+1,end+1):
   prev=t-1;i=prev*stride;j=i+stride;c0=int(a['contact_offsets'][i]);c1=int(a['contact_offsets'][j]);packed={k:a[k][i:j] for k in ['action_step','substep_tick','kind']};packed.update(contact_offsets=a['contact_offsets'][i:j+1]-c0,shape_ids=a['shape_ids'][c0:c1],force_torque_world=a['force_torque_world'][c0:c1]);obs=extract(packed,m,after_action_step=prev,side=side,target_name=actor)
   packet=packets[prev];load=hand_target_vertical_load(packet,side,actor);assert abs(load-obs['final_vertical_load_n'])<1e-5;slip=loaded_forward_margin(packet,side,actor,trace[key][t],ori[key][t],size,plan['direction']);r=rows[t]
   kw=dict(tip=r['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other_key][t],control_offset_local=r['observed_support_offset_local'],load_n=load,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=slip)
   positional=(trace['palm_'+side][t],trace[key][t],trace[other_key][t],extent_x_from_quat(size,ori[key][t]),extent_x_from_quat(other_size,ori[other_key][t]))
   T,_,_=guard.model.fk(side,q[t]);out=[]
   for s in [off,on]:
    s.load.observe(action_step=t,after_action_step=prev,vertical_load_n=obs['vertical_load_n']);extra={}
    if s is on:s.observe_contact_window(action_step=t,after_action_step=prev,vertical_load_n=obs['vertical_load_n'],instantaneous_load_n=load);extra=dict(observed_hand_xyz=T[:3,3],observed_hand_quat_xyzw=Rotation.from_matrix(T[:3,:3]).as_quat())
    out.append(s.update(*positional,**kw,**extra))
   baseline,candidate=out
   assert baseline['mode']==r['mode'],(ep.name,t,'baseline mode',baseline['mode'],r['mode'])
   np.testing.assert_allclose(baseline['target_xyz'],r['target_xyz'],atol=2e-6,rtol=0,err_msg=f'{ep.name}:{t}:parent waypoint')
   np.testing.assert_allclose(baseline['contact_load']['stored_z_bias_m'],r['contact_load']['stored_z_bias_m'],atol=1e-9,rtol=0)
   record=dict(step=t,parent_mode=baseline['mode'],candidate_mode=candidate['mode'],parent_waypoint=list(baseline['target_xyz']),candidate_waypoint=list(candidate['target_xyz']),candidate_interval=candidate['contact_window_interval'],candidate_counter=on.lost_contact_steps,parent_counter=off.lost_contact_steps)
   records.append(record)
  results.append(dict(episode=ep.name,start_state_after_step=lo,last_action=end,native_updates=len(records),parent_matches_original=True,own_candidate_history=True,records=records));print(json.dumps({k:v for k,v in results[-1].items() if k!='records'}),flush=True)
for module in list(sys.modules.values()):
 name=getattr(module,'__file__',None)
 if name:
  p=Path(name).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
sources[str(Path(__file__).resolve())]=sha(__file__)
for p,h in sources.items():assert sha(p)==h
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,bouts=results,total_native_updates=sum(r['native_updates'] for r in results),source_sha256=sources,full_prefix_replay=False,final_joint_guard_verified=False,physics_verified=False,training_ready=False)
with (D/'NATIVE_LOADED_BOUT_CHECK_V2.json').open('x') as f:json.dump(report,f,indent=2)
print('PASSED',report['total_native_updates'])
