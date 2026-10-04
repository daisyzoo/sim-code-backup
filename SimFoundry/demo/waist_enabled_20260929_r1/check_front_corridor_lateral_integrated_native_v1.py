"""Actual native route/COP boundary reconstruction, not a physical rollout.
Reconstruct the observed deterministic recontact reset at593 using prior data,
verify native output against actual593, then fork once at594. Nothing after
observation594 is used as a response to the candidate. No joint/IK claim.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy,importlib.util
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';C=W/'front_corridor_lateral_candidate_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_initial_center_cop_route import FrontCopRouteState
import front_initial_center_route as route
from peak_load_update_trace import TracedPeakLoadControl
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease
from simfoundry.data.tabletop_route_candidates import footprint_radii
from simfoundry.data.contact_load_control import hand_target_vertical_load
spec=importlib.util.spec_from_file_location('lateral_native_candidate',C/'selection.py');candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
proof=read(C/'GEOMETRY_REPRODUCTION.json')
for p,h in proof['source_sha256'].items():assert sha(p)==h,p
R=W/'joint_transport_reserve_physical_r1';ep=R/'case_840023/layout_840023_nudge_mailer_to_bin';protocol=read(R/'PROTOCOL.json');ready=read(ep/'READY_FOR_AUDIT.json')
for p,h in ready['source_sha256'].items():assert sha(p)==h,p
stage_prep=read(S/'COLLECTOR_PREPARATION.json')
for name,h in stage_prep['stage_sha256'].items():assert sha(S/name)==h
for name,h in stage_prep['parent_files'].items():
 p=Path(stage_prep['parent'])/name;assert protocol['frozen_files_sha256'][str(p)]==h==sha(p)
fr=read(ep/'frontal_bypass.json');plan=fr['plan'];rows={r['step']:r for r in fr['rows']};pressure=read(ep/'peak_load_updates.json');finals={x['step']:x for x in pressure['final_control_states']};packets={x['after_action_step']:x for x in read(ep/'solved_contact_forces.json')['rows']};meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json')['metadata']
with np.load(ep/'trace.npz') as z:trace={k:z[k][:595].copy() for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k][:595].copy() for k in z.files}
with np.load(ep/'substep_contacts.npz') as z:a={k:z[k] for k in z.files}
# Only592/593 substep force intervals, ending before issuing594.
def load24(t):
 stride=24+meta['expected_manager_steps'];base=t*stride;ticks=a['substep_tick'][base:base+stride];values=[]
 assert np.all(a['action_step'][base:base+stride]==t)
 for tick in range(1,25):
  matches=np.flatnonzero(ticks==tick);assert len(matches)>0;j=base+int(matches[0]);load=0.
  for k in range(int(a['contact_offsets'][j]),int(a['contact_offsets'][j+1])):
   names=[meta['shape_labels'][int(i)] for i in a['shape_ids'][k]]
   if any('left_wrist_roll' in n for n in names) and any('/mailer/' in n for n in names):load+=abs(float(a['force_torque_world'][k,2]))
  values.append(load)
 return values

def inputs(t):
 row=rows[t];packet=packets[t-1];rot=Rotation.from_quat(ori['mailer'][t]).as_matrix();points=[];weights=[]
 for contact in packet['parcel_contacts']:
  slots=[i for i,label in enumerate(contact['shapes']) if '/mailer/' in label]
  if len(slots)!=1 or not any('left_wrist' in label for label in contact['shapes']):continue
  force=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rot[:,2])
  if normal>.05:weights.append(normal);points.append(contact['position_world'])
 slip=None if not weights else dict(valid=True,normal_load_n=sum(weights),weighted_contact_local=(rot.T@(np.average(points,axis=0,weights=weights)-trace['mailer'][t])).tolist())
 tr=footprint_radii((.15,.145,.04),ori['mailer'][t]);orr=footprint_radii((.14,.09,.045),ori['box'][t]);load=hand_target_vertical_load(packet,'left','mailer');np.testing.assert_allclose(load,load24(t-1)[-1],atol=1e-5,rtol=0)
 return (trace['palm_left'][t].tolist(),trace['mailer'][t].tolist(),trace['box'][t].tolist(),tr[0],orr[0]),dict(tip=row['observed_support_xyz'],quat=ori['mailer'][t].tolist(),obstacle_quat=ori['box'][t].tolist(),control_offset_local=row['control_offset_local'],load_n=load,hand_obstacle_gap_m=row['hand_obstacle_gap_m'],slip_contact=slip)

s=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(plan)),'left',(.15,.145,.04),obstacle_size=(.14,.09,.045),route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,corridor_midpoint_replan=True,guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=tuple(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']),recontact_travel_z=.86,alignment_tolerance_m=.010,confirm_terminal_release=True)
prev=rows[592];assert prev['route_stage']=='front_x' and prev['mode']=='top_push' and prev['clearance_progress']['clearance_recovery_count']==0
s.top_mode=s.mode='top_push';s.mode_step=51;s.command=tuple(prev['target_xyz']);s.last_emitted_xy=tuple(prev['target_xyz'][:2]);s.last_route_stage='front_x';s.recontacts=prev['recontacts'];s.route_stage='front_x';s.start=tuple(prev['observed_support_xyz'])
chosen,s.route_report=route.select_front_route(trace['mailer'][1],trace['box'][1],s.size,s.obstacle_size,ori['mailer'][1],ori['box'][1],1,margin=.012);s.route_x=chosen['waypoints_xy'][1][0]-.003
s.load=TracedPeakLoadControl(5.,min_bias_m=-.006);s.load.bind_owner(s);s.load.bias_m=finals[592]['bias_m'];s.load.filtered_n=finals[592]['filtered_n']
s.clearance_progress=FrontClearanceProgress(.012,prev['clearance_progress']['front_hold_y'],stage='front_x',recoveries=0,confirm_nominal_clearance=True,safe_observations=prev['clearance_progress']['safe_clearance_observations'],recovery_hysteresis_m=.0005)
s.position_release_monitor=ConfirmedPositionRelease(plan['initial_target_xyz'][1],1)
for t in range(1,593):s.position_release_monitor.observe(trace['mailer'][t])
s.cop_slip.local_anchor=np.asarray(prev['cop_slip_following']['anchor_local']);s.cop_slip.previous_anchor_world=trace['mailer'][592]+Rotation.from_quat(ori['mailer'][592]).as_matrix()@s.cop_slip.local_anchor
s.load.observe(action_step=593,after_action_step=592,vertical_load_n=load24(592));args,kw=inputs(593);reproduced=s.update(*args,**kw)
assert reproduced['direction_change_recontact']['restarted'] and reproduced['mode']=='top_lift' and s.recontacts==3
checks=[]
for k in ['mode','target_xyz','route_stage','route_stop_reason','recontacts','direction_change_recontact','clearance_progress','contact_load','front_corridor_midpoint','cop_slip_following']:
 def near(actual,expected,path):
  if isinstance(actual,dict):
   assert actual.keys()==expected.keys(),path
   for key in actual:near(actual[key],expected[key],path+'.'+key)
  elif isinstance(actual,(list,tuple)):
   assert len(actual)==len(expected),path
   for i,(a,b) in enumerate(zip(actual,expected)):near(a,b,path+'.'+str(i))
  elif isinstance(actual,(int,float)) and not isinstance(actual,bool):assert abs(actual-expected)<2e-10,(path,actual,expected)
  else:assert actual==expected,(path,actual,expected)
 near(reproduced[k],rows[593][k],k);checks.append(k)
assert s.start==tuple(rows[593]['observed_support_xyz']) and s.command is None and s.mode_step==1 and s.selected_surface_local_xy is None
# Recontact reset makes the next state's consumed fields explicit and bound.
base=copy.deepcopy(s);args,kw=inputs(594)
def invoke(enabled,mutation=None):
 state=copy.deepcopy(base);newkw=copy.deepcopy(kw)
 if mutation=='latched':state.stop_reason='front_corridor_no_table_margin';state.stop_tip=tuple(kw['tip'])
 if mutation=='hand_gap':newkw['hand_obstacle_gap_m']=.0049
 state.load.observe(action_step=594,after_action_step=593,vertical_load_n=load24(593))
 original=route.select_corridor_midpoint
 try:
  state.corridor_lateral_replan=enabled
  result=state.update(*copy.deepcopy(args),**newkw)
 finally:route.select_corridor_midpoint=original
 return result
old=invoke(False);new=invoke(True)
for k in ['mode','target_xyz','route_stage','route_stop_reason','front_corridor_midpoint','cop_slip_following']:near(old[k],rows[594][k],k)
assert new['mode']=='top_lift' and new['route_stop_reason'] is None and new['front_corridor_midpoint']['changed'];np.testing.assert_allclose(new['target_xyz'],rows[593]['target_xyz'],atol=0,rtol=0)
assert new['contact_load']['applied_z_bias_m']==0. and new['travel_height_m']==.86
negative=[]
for label in ['latched','hand_gap']:
 bad=invoke(True,label);assert bad['mode']=='front_guard_lift' and not bad['front_corridor_midpoint']['changed'];negative.append(dict(case=label,mode=bad['mode'],reason=bad['route_stop_reason']))
for p in [Path(__file__),C/'selection.py',ep/'trace.npz',ep/'parcel_orientation.npz',ep/'substep_contacts.npz']:sources[str(p)]=sha(p)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,reproduced_actual_reset_step=593,actual_reset_fields_verified=checks,original_guard_step594_reproduced=True,original_waypoint=old['target_xyz'],unissued_candidate_waypoint=new['target_xyz'],candidate_row=new,guard_checks=negative,source_sha256=sources,full_prefix_controller_replay=False,native_boundary_reset_reconstruction=True,physics_started=False,full_joint_ik_and_guard_verified=False,training_ready=False,next='Integrate opt-in phase switch and native independent audits in isolated collector; verify final joint command and existing guard/fallback geometry before physical trial.')
report['actual_integrated_class_switch_used']=True
report['fixture_parent_sha256']=sha(W/'check_front_corridor_lateral_native_v1.py')
with (W/'front_corridor_lateral_preparation_r1/INTEGRATED_NATIVE_BOUNDARY_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:report[k] for k in ['passed','reproduced_actual_reset_step','original_waypoint','unissued_candidate_waypoint','guard_checks','full_joint_ik_and_guard_verified']},indent=2))
