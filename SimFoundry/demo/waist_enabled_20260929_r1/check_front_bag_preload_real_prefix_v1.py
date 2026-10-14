"""Reconstruct real controller history, then fixed-observation recovery forks.
Front bag baseline reconstruction with isolated one-step changed-waypoint forks.
Recorded adapter events and pressure observation summaries are replay inputs;
this does not revalidate their physical measurements or predict new dynamics.
"""
from pathlib import Path
import sys,copy,json,hashlib,datetime,traceback,ast
from types import SimpleNamespace as NS
import numpy as np
W=Path(__file__).resolve().parent; ROOT=W.parents[1];S=W/'staged_front_bag_preload_hold_v1';D=W/'front_bag_preload_real_prefix_r1';D.mkdir(exist_ok=False)
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
from front_bag_preload_waypoint_candidate_v1 import FrontBagPreload,commit_original_recovery
from front_box_recenter_runtime import FrontRecontactCenterRuntime
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_effective_height_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin'
f=read(ep/'frontal_bypass.json');p=f['plan'];fr={r['step']:r for r in f['rows']};cs={r['step']:r for r in read(ep/'coordination.json')};pr={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']};pf={r['step']:r for r in read(ep/'peak_load_updates.json')['final_control_states']}
ie={r['step']:r for r in read(ep/'front_initial_center.json')['rows']};re={r['step']:r for r in read(ep/'front_recontact_center.json')['rows']};packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']}
with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
size=tuple(p['top_recontact']['contact_size_xyz']);osize=(.15,.145,.04);core=p['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']
s=FrontCopRouteState(FrontalBypassState(p,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),'left',size,guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9,obstacle_size=osize,route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recontact_travel_z=.86,recovery_hysteresis_m=.0005,cop_drive_step_m=.002,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,edge_speed_enabled=True,edge_core_size=core,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,corridor_midpoint_replan=True,corridor_lateral_replan=True)
s.position_release_monitor=ConfirmedPositionRelease(p['initial_target_xyz'][1],p['direction']);s.load=TracedPeakLoadControl(5.,min_bias_m=-.006);s.load.bind_owner(s)
report=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_frames=0,max_waypoint_error_m=0.,recovery_forks=[],passed=False,training_ready=False,physics_started=False)
def inputs(t):
 r=fr[t];load=hand_target_vertical_load(packets[t-1],'left','mailer');contact=loaded_forward_margin(packets[t-1],'left','mailer',tr['mailer'][t],ori['mailer'][t],size,1)
 args=(tr['palm_left'][t],tr['mailer'][t],tr['box'][t],footprint_radii(size,ori['mailer'][t])[0],footprint_radii(osize,ori['box'][t])[0])
 kw=dict(tip=r['observed_support_xyz'],quat=ori['mailer'][t],obstacle_quat=ori['box'][t],control_offset_local=r['control_offset_local'],load_n=load,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=contact)
 return args,kw
def observe(state,t):
 state.load._observation=copy.deepcopy(pr[t]['preceding_observation']);state.load._last_action_step=t
snapshots={}
try:
 for t in range(1,1200):
  a,kw=inputs(t)
  # At a measured handover the saved row is post-adapter. Reconstruct the
  # incoming support reference using the actual pose and prior captured center.
  for events in [ie,re]:
   if events[t]['kind']=='handover':
    pose=np.asarray(events[t]['context']['observed_hand_pose']);center=re[t-1]['center_local_after'] if t>1 else None
    if center is None:center=ie[t-1]['center_local_after'] if t>1 else None
    ref=projected_support_reference(support_mesh()['left'],pose[:3,:3],np.asarray(rotation_xyzw(ori['mailer'][t]))[:,2],center_local=center)
    kw['tip']=(pose[:3,3]+pose[:3,:3]@ref['reference_local']).tolist();kw['control_offset_local']=ref['reference_local']
  observe(s,t);r=s.update(*a,**kw)
  assert s.load.updates[-1]==pr[t],(t,'pressure mutation mismatch')
  ref={k:np.array(v) for k,v in fr[t]['projected_support_reference'].items()}
  for events,adapter in [(ie,apply_initial),(re,apply_recovery)]:
   r,ref=adapter(r,s,ref,events[t],object_xyz=tr['mailer'][t],object_rotation=np.asarray(rotation_xyzw(ori['mailer'][t])))
  err=float(np.max(abs(np.asarray(r['target_xyz'])-np.asarray(fr[t]['target_xyz']))));report['max_waypoint_error_m']=max(err,report['max_waypoint_error_m'])
  assert err<2e-7,(t,'waypoint mismatch',err)
  for key in ['mode','route_stage','recontacts','route_stop_reason','last_recontact_reason']:assert r.get(key)==fr[t].get(key),(t,key,r.get(key),fr[t].get(key))
  assert s.load.bias_m==pf[t]['bias_m'] and s.load.filtered_n==pf[t]['filtered_n'],(t,'final pressure state')
  report['baseline_frames']+=1
  if t in (166,348,499,657,796,984,1084):snapshots[t]=copy.deepcopy(s)

 report['baseline_reconstructed']=True
 report['baseline_frames_expected']=1199
 assert report['baseline_frames']==1199 and len(snapshots)==7
 chain_path=W/'front_bag_preload_command_chain_r2/RESULT.json';chain=read(chain_path);assert chain['passed']
 for path,h in chain['source_sha256'].items():assert sha(path)==h,path
 entries={r['step']:r['branches']['candidate'] for r in chain['rows']}
 guard=ClearanceGuard(ROOT,S)
 tree=ast.parse((S/'collect_paired_sorting.py').read_text())
 final=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='clearance_guard is not None' and 'final_clearance' in ast.unparse(n))
 commit=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_bag_preload_hold' and 'commit_after_final_guard(' in ast.unparse(n))
 previous=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()')
 target=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_bag_preload_hold' and 'preload_controller.propose(' in ast.unparse(n))
 def program(nodes):
  loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(0)],ctx=ast.Load()),body=copy.deepcopy(nodes)+[ast.Assign(targets=[ast.Name(id='reached',ctx=ast.Store())],value=ast.Constant(True))],orelse=[])
  return compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<native preload collector statements>','exec')
 target_program=program([target]);commit_program=program([final,commit,previous])
 class Tensor:
  def __init__(self,x):self.x=np.asarray(x);self.torch=self
  def __getitem__(self,k):return Tensor(self.x[k])
  def detach(self):return self
  def cpu(self):return self
  def numpy(self):return self.x
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 forks=[]
 for t,state in snapshots.items():
  proposal_env=dict(args=NS(front_bag_preload_hold=True),preload_controller=FrontBagPreload(enabled=True),step=t,side='left',frontal_plan=p,frontal_state=copy.deepcopy(state),waypoint={k:copy.deepcopy(v) for k,v in fr[t].items() if k!='step'},reached=False)
  exec(target_program,proposal_env);assert proposal_env['reached'];proposal=proposal_env['preload_proposal'];assert proposal['record']['kind']=='hold'
  # Bind to the separately audited changed full9D/quarter/transport solution.
  expected=read(W/'front_bag_preload_waypoint_r1/RESULT.json')['isolated_original_entry_proposals'];want=next(r for r in expected if r['step']==t)
  assert proposal['record']==want
  candidate=entries[t];assert candidate['full9D_certificate']['passed'] and candidate['final_guard_passed']
  xy_error=np.clip(np.float32(.72)*(np.asarray(proposal['record']['output_target_xyz'],np.float32)-np.asarray(cs[t]['control_point_positions']['left'],np.float32)),np.float32(-.035),np.float32(.035))
  # z record retains coordinate full task inputs; inspect its recorded solve binding.
  a=copy.deepcopy(u[t]);a[12:23]=candidate['command']
  e=dict(proposal_env,np=np,action=a,previous=u[t-1].copy(),default=np.zeros(23,np.float32),robot=NS(data=NS(joint_pos=Tensor(q[t][None]))),ordered_ids=list(range(23)),clearance_guard=guard,clearance_rows=[],clearance_failure=None,preload_waypoint_log=[],reached=False)
  bad=copy.deepcopy(e);bad['clearance_guard']=guard;bad['action'][12]=10.;old_command=bad['frontal_state'].command;old_history=bad['previous'].copy();old_pressure=(bad['frontal_state'].load.bias_m,bad['frontal_state'].load.filtered_n)
  exec(commit_program,bad);assert not bad['reached'] and bad['clearance_failure']['reason']=='final_override_not_verified' and not bad['preload_waypoint_log']
  assert bad['frontal_state'].command==old_command and old_pressure==(bad['frontal_state'].load.bias_m,bad['frontal_state'].load.filtered_n) and np.array_equal(bad['previous'],old_history)
  pressure=(e['frontal_state'].load.bias_m,e['frontal_state'].load.filtered_n,len(e['frontal_state'].load.updates));exec(commit_program,e);assert e['reached'] and len(e['preload_waypoint_log'])==1
  ss=e['frontal_state'];assert ss.command==tuple(proposal['record']['output_target_xyz']) and ss.last_emitted_xy==tuple(proposal['record']['output_target_xyz'][:2])
  assert pressure==(ss.load.bias_m,ss.load.filtered_n,len(ss.load.updates)) and np.array_equal(e['previous'],e['action'])
  # One next observation from archived input: demonstrates state continuity only.
  # It cannot predict load or classify any changed physical trajectory.
  a,kw=inputs(t+1);observe(ss,t+1);row=ss.update(*a,**kw)
  if row['cop_slip_following'].get('override'):
   np.testing.assert_array_equal(row['cop_slip_following']['previous_command_xy'],proposal['record']['output_target_xyz'][:2])
  forks.append(dict(step=t,native_final_guard=True,native_commit=True,real_state_command_updated=True,pressure_unchanged=True,unsafe_final_rejected_before_history=True,next_fixed_observation_mode=row['mode'],next_cop_previous_uses_admitted_target=bool(row['cop_slip_following'].get('override')),new_physics=False))
  print(json.dumps(forks[-1]),flush=True)
 report.update(passed=True,preload_forks=forks,source_sha256={str(x):sha(x) for x in [Path(__file__),chain_path,W/'front_bag_preload_waypoint_r1/RESULT.json',*[ep/n for n in ['raw.npz','frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz','peak_load_updates.json','front_initial_center.json','front_recontact_center.json','solved_contact_forces.json']],*[x for x in S.iterdir() if x.is_file()]]},physical_launch_allowed=False,training_ready=False)
 (D/'RESULT.json').write_text(json.dumps(report,indent=2));print('PASSED actual front bag prefix and seven native commit forks',flush=True)
except BaseException:
 report['traceback']=traceback.format_exc();(D/'FAILURE.log').write_text(report['traceback']);(D/'RESULT.json').write_text(json.dumps(report,indent=2));raise
