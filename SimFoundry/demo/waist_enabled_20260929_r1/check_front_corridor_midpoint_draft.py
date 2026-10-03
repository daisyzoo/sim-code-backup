"""Draft-only original-observation screen and actual route/COP class fixtures.
The command proposal fixture is explicitly unissued, not a candidate trajectory.
No physics launch or training admission. Full IK/path/collector/audit wiring remain.
"""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,sys,collections
from types import SimpleNamespace
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_midpoint';P=W/'staged_front_loaded_z_priority';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_corridor_midpoint_runtime import select
from front_initial_center_cop_route import FrontCopRouteState
from simfoundry.data.tabletop_route_candidates import footprint_radii
from simfoundry.data.front_clearance_progress import FrontClearanceProgress
from simfoundry.data.contact_load_control import hand_target_vertical_load
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
# The original class has identical dependencies; load only its own class under a
# distinct module name. Parent COP import name is changed only in this fixture.
spec=importlib.util.spec_from_file_location('original_midpoint_fixture_route',P/'front_initial_center_route.py');parent=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parent;spec.loader.exec_module(parent)
import types
parent_cop=types.ModuleType('original_midpoint_fixture_cop');parent_cop.__file__=str(P/'front_initial_center_cop_route.py');sys.modules[parent_cop.__name__]=parent_cop
original_cop=(P/'front_initial_center_cop_route.py').read_text();renamed=original_cop.replace('from front_initial_center_route import FrontTopRouteState','from original_midpoint_fixture_route import FrontTopRouteState');assert renamed!=original_cop
exec(compile(renamed,parent_cop.__file__,'exec'),parent_cop.__dict__)
counts=[];sample=None
for run in ['front_initial_physical_r1','front_z_priority_physical_r1']:
 for case,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
  ep=W/run/f'case_{case}'/f'layout_{case}_{task}';fr=read(ep/'frontal_bypass.json');plan=fr['plan'];box=task=='push_box_to_bin';key='box' if box else 'mailer';other='mailer' if box else 'box';size=[.14,.09,.045] if box else [.15,.145,.04];osize=[.15,.145,.04] if box else [.14,.09,.045]
  with np.load(ep/'trace.npz') as z:target=z[key].astype(float);obstacle=z[other].astype(float)
  with np.load(ep/'parcel_orientation.npz') as z:tq=z[key].astype(float);oq=z[other].astype(float)
  front=next(x for x in plan['front_route_candidates']['candidates'] if x['route']=='front');route_x=front['waypoints_xy'][1][0]-.003;stopped=False;reasons=collections.Counter();changed=[]
  for row in fr['rows']:
   t=row['step'];tr=footprint_radii(size,tq[t]);orr=footprint_radii(osize,oq[t]);goal=min(route_x,obstacle[t,0]-orr[0]-tr[0]-.012-.003)
   args=dict(original_goal_x=goal,route_stage=row['route_stage'],target=target[t].tolist(),obstacle=obstacle[t].tolist(),size=size,other_size=osize,quat=tq[t].tolist(),other_quat=oq[t].tolist(),direction=plan['direction'],planning_margin=.012,initial_other=plan['obstacle_initial_xyz'],hand_obstacle_gap_m=row['hand_obstacle_gap_m'],parent_guard_reason=None,prior_stop_reason='previous_actual_stop' if stopped else None)
   result,record=select(**args);reasons[record['reason']]+=1
   if record['changed']:
    lo,hi=record['safe_interval_x'];lp=linprog([0.,-1.],A_ub=[[-1.,1.],[1.,1.]],b_ub=[-lo,hi],bounds=[(None,None),(0,None)],method='highs');assert lp.success and abs(lp.x[0]-result)<1e-10
    assert result-tr[0]-.28>=.005 and obstacle[t,0]-result-orr[0]-tr[0]>=.012
    changed.append(t)
    if run=='front_z_priority_physical_r1' and case==840023 and t==173:sample=(ep,fr,args,row,route_x,target,obstacle,tq,oq)
   else:assert result==goal
   stopped=stopped or bool(row.get('route_stop_reason'))
  counts.append(dict(run=run,episode=ep.name,rows=len(fr['rows']),changed_steps=changed,reasons=dict(reasons)))
  for n in ['trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
assert sample is not None
ep,fr,args,row,route_x,target,obstacle,tq,oq=sample;t=173;previous=next(x for x in fr['rows'] if x['step']==t-1);plan=fr['plan'];packets=read(ep/'solved_contact_forces.json');packet=next(x for x in packets['rows'] if x['after_action_step']==t-1)
load=hand_target_vertical_load(packet,'left','mailer');rot=Rotation.from_quat(tq[t]).as_matrix();weights=[];points=[]
for contact in packet['parcel_contacts']:
 slots=[i for i,label in enumerate(contact['shapes']) if '/mailer/' in label]
 if len(slots)!=1 or not any('left_wrist' in label for label in contact['shapes']):continue
 force=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rot[:,2])
 if normal>.05:weights.append(normal);points.append(contact['position_world'])
assert sum(weights)>=.3;local=rot.T@(np.average(points,axis=0,weights=weights)-target[t]);slip=dict(valid=True,normal_load_n=sum(weights),weighted_contact_local=local.tolist())
kwargs=dict(tip=row['observed_support_xyz'],quat=tq[t].tolist(),obstacle_quat=oq[t].tolist(),control_offset_local=row['control_offset_local'],load_n=load,hand_obstacle_gap_m=row['hand_obstacle_gap_m'],slip_contact=slip)
tr=footprint_radii(args['size'],tq[t]);orr=footprint_radii(args['other_size'],oq[t])
callargs=(row['observed_support_xyz'],target[t].tolist(),obstacle[t].tolist(),tr[0],orr[0])
def state(cls,on=None):
 extra={} if on is None else dict(corridor_midpoint_replan=on)
 s=cls(SimpleNamespace(plan=copy.deepcopy(plan)),'left',tuple(args['size']),obstacle_size=tuple(args['other_size']),route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9,tilt_recontact_rad=.03,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=.002,edge_speed_enabled=True,edge_core_size=tuple(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']),**extra)
 s.top_mode=s.mode='top_push';s.command=tuple(previous['target_xyz']);s.mode_step=7;s.route_x=route_x;s.route_report=copy.deepcopy(plan['front_route_candidates']);s.start=tuple(previous['observed_support_xyz']);s.last_emitted_xy=tuple(previous['target_xyz'][:2]);s.last_route_stage='front_x';s.load.desired_n=5.;s.load.bias_m=previous['contact_load']['stored_z_bias_m'];s.load.filtered_n=previous['contact_load']['filtered_vertical_load_n'];s.clearance_progress=FrontClearanceProgress(.012,plan['initial_target_xyz'][1],confirm_nominal_clearance=True,recovery_hysteresis_m=.0005)
 oldrot=Rotation.from_quat(tq[t-1]).as_matrix();s.selected_surface_local_xy=tuple((oldrot.T@(np.asarray(previous['parcel_top_xyz'])-target[t-1]))[:2]);s.cop_slip.local_anchor=np.array(previous['cop_slip_following']['anchor_local']);s.cop_slip.previous_anchor_world=target[t-1]+oldrot@s.cop_slip.local_anchor
 return s
old=state(parent_cop.FrontCopRouteState).update(*copy.deepcopy(callargs),**copy.deepcopy(kwargs));off=state(FrontCopRouteState,False).update(*copy.deepcopy(callargs),**copy.deepcopy(kwargs));assert old==off
assert old['mode']=='front_guard_lift' and old['route_stop_reason']=='front_corridor_no_table_margin';np.testing.assert_array_equal(old['target_xyz'],row['target_xyz'])
on=state(FrontCopRouteState,True).update(*copy.deepcopy(callargs),**copy.deepcopy(kwargs));assert on['front_corridor_midpoint']['changed'] and on['mode']=='top_push' and on['route_stop_reason'] is None and on['cop_slip_following']['override'] and on['front_diagonal_entry']['selected'];assert abs(on['route_goal_x']-on['front_corridor_midpoint']['goal_x'])<1e-12;np.testing.assert_allclose(on['target_xyz'][:2],on['cop_slip_following']['command_xy'],atol=0,rtol=0);assert np.max(abs(np.asarray(on['target_xyz'][:2])-previous['target_xyz'][:2]))<=.003+1e-12
negatives=[]
for name,change in [('hand_gap',dict(hand_obstacle_gap_m=.004)),('parent_guard',dict(parent_guard_reason='target_table_margin_5mm')),('latched',dict(prior_stop_reason='front_corridor_no_table_margin')),('wrong_phase',dict(route_stage='lateral_y')),('non_target_moved',dict(initial_other=[args['obstacle'][0]-.02,*args['obstacle'][1:]])),('no_width',dict(other_size=[.2,.09,.045]))]:
 x=dict(args,**change);value,record=select(**x);assert value==x['original_goal_x'] and not record['changed'];negatives.append(name)
for name,change in [('nan',dict(original_goal_x=float('nan'))),('invalid_quaternion',dict(quat=[0,0,0,0])),('weakened_margin',dict(planning_margin=.011)),('invalid_size',dict(size=[-.15,.145,.04]))]:
 try:select(**dict(args,**change))
 except ValueError:negatives.append(name)
 else:raise AssertionError('invalid input accepted '+name)
# Actual class latched/hand guards retain the original stop under enabled flag.
for name in ['latched','hand_gap']:
 s=state(FrontCopRouteState,True);kw=copy.deepcopy(kwargs)
 if name=='latched':s.stop_reason='front_corridor_no_table_margin';s.stop_tip=tuple(row['observed_support_xyz'])
 else:kw['hand_obstacle_gap_m']=.004
 result=s.update(*copy.deepcopy(callargs),**kw);assert result['mode']=='front_guard_lift' and not result['front_corridor_midpoint']['changed'];negatives.append('actual_class_'+name)
for p in [Path(__file__),P/'front_initial_center_route.py',P/'front_initial_center_cop_route.py',S/'front_corridor_midpoint_runtime.py',S/'front_initial_center_route.py',S/'front_initial_center_cop_route.py',S/'front_diagonal_entry_geometry_probe.py',S/'ROUTE_CLASS_PATCH.json']:sources[str(p)]=sha(p)
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,observed_screens=counts,observed_rows=sum(x['rows'] for x in counts),actual_route_cop_single_step_fixture=dict(step=t,unissued=True,default_off_exact_parent=True,enabled_mode=on['mode'],original_waypoint=old['target_xyz'],unissued_candidate_waypoint=on['target_xyz'],nominal_route=on['front_corridor_midpoint'],cop_goal=on['cop_slip_following']['diagonal_entry_control']['goal_xy']),negative_cases_rejected=negatives,source_sha256=sources,collector_wired=False,full_ik_and_final_guard_verified=False,physical_started=False,training_ready=False)
with (S/'DRAFT_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
