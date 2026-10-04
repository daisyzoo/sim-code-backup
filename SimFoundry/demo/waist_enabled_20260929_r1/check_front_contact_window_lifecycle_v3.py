"""Native first update and measured-reference adapter transaction fixtures.
Actual stage constructor, pressure, full front stack and adapters are executed.
First update uses recorded raw geometry; longer transition sequence uses explicit
synthetic observations/events, not a planner rollout or physical-success proof.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,sys,json,copy,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_window_native_v4 import WindowFrontCopRouteState
from front_initial_center_cop_route import FrontCopRouteState
from peak_load_update_trace import TracedPeakLoadControl
from simfoundry.data.frontal_bypass import FrontalBypassState,extent_x_from_quat
from clearance_runtime import ClearanceGuard
from front_initial_center_adapter import apply as initial_apply
from front_recontact_center_adapter import apply as recovery_apply
from margin_confirmed_position_release import ConfirmedPositionRelease
from simfoundry.data.top_contact_bypass import support_vertex
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def assert_consumed(state,row,t):
 i=row['contact_window_interval'];assert i['action_step']==t and state._window_pending is None and state._window_active is None
 assert state.window_last_disposition==i and i['training_ready'] is False
 return copy.deepcopy(i)
# First actual constructor call starts with None; no manually seeded top phase.
case=W/'front_loaded_z_quarter_physical_r2/case_840023';ep=case/'layout_840023_nudge_mailer_to_bin';args=NS(**read(case/'provenance.json')['args']);fr=read(ep/'frontal_bypass.json');plan=fr['plan'];r=fr['rows'][0];assert r['step']==1
p=S/'collect_paired_sorting.py';sources[str(p)]=sha(p);nodes=list(ast.walk(ast.parse(p.read_text())));construct=next(n for n in nodes if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='top_cls');code=compile(ast.Module(body=[construct],type_ignores=[]),'<actual collector constructor>','exec')
shape_nodes=[n for n in nodes if isinstance(n,ast.Assign) and isinstance(n.value,ast.IfExp) and any(isinstance(t,ast.Name) and t.id in ('target_size','obstacle_size') for t in n.targets)];env=dict(side='left');exec(compile(ast.Module(body=shape_nodes,type_ignores=[]),'<actual collector dimensions>','exec'),env);size=env['target_size'];other=env['obstacle_size'];core=tuple(np.array(plan['front_cop_slip_following']['edge_speed']['actual_core_size_xyz']))
loaded=[]
for name,keys in [('raw.npz',['q']),('trace.npz',['mailer','box','palm_left']),('parcel_orientation.npz',['mailer','box'])]:
 p=ep/name;sources[str(p)]=sha(p)
 with np.load(p) as z:loaded.append({k:z[k].copy() for k in keys})
raw,trace,ori=loaded;guard=ClearanceGuard(ROOT,S);T,_,_=guard.model.fk('left',raw['q'][1,12:23]);actual=[]
for enabled in [False,True]:
 extra=dict(obstacle_size=other,route_clearance_m=args.expert_front_clearance_m,recover_clearance=args.expert_front_recover_clearance,confirm_nominal_clearance=args.expert_front_confirm_nominal_clearance,object_relative_lead=args.expert_front_object_relative_lead,recontact_travel_z=args.expert_front_recontact_z,recovery_hysteresis_m=args.expert_front_recovery_hysteresis_m,recontact_on_route_change=True,diagonal_entry=True,retain_micro_repair_contact=True,corridor_midpoint_replan=True,corridor_lateral_replan=True,cop_slip_enabled=True,reset_cop_on_route_change=True,route_axis_only=True,cop_drive_step_m=args.front_cop_drive_step_m,edge_speed_enabled=True,edge_core_size=core)
 if enabled:extra.update(contact_window_enabled=True,contact_window_selected_front=True)
 e=dict(top_cls=WindowFrontCopRouteState if enabled else FrontCopRouteState,frontal_state=FrontalBypassState(copy.deepcopy(plan)),side='left',contact_size=size,top_extra=extra,args=args,front_route_selected=True,effective_drag_step_m=.003,effective_top_fraction=plan['top_recontact']['effective_top_fraction']);exec(code,e);state=e['frontal_state'];assert state.top_mode is None
 state.load=TracedPeakLoadControl(5.,min_bias_m=-.006);state.load.bind_owner(state);state.load.observe(action_step=1,after_action_step=0,vertical_load_n=[0.]*24);kw={}
 if enabled:state.observe_contact_window(action_step=1,after_action_step=0,vertical_load_n=[0.]*24,instantaneous_load_n=0.);kw=dict(observed_hand_xyz=T[:3,3],observed_hand_quat_xyzw=Rotation.from_matrix(T[:3,:3]).as_quat())
 row=state.update(trace['palm_left'][1].tolist(),trace['mailer'][1].tolist(),trace['box'][1].tolist(),extent_x_from_quat(size,ori['mailer'][1].tolist()),extent_x_from_quat(other,ori['box'][1].tolist()),tip=r['observed_support_xyz'],quat=ori['mailer'][1].tolist(),obstacle_quat=ori['box'][1].tolist(),control_offset_local=r['observed_support_offset_local'],load_n=0.,hand_obstacle_gap_m=r['hand_obstacle_gap_m'],slip_contact=None,**kw)
 if enabled:first_interval=assert_consumed(state,row,1);assert first_interval['observed_phase'] is None;row.pop('contact_window_interval')
 actual.append(row)
assert actual[0]==actual[1];assert actual[0]['mode']==r['mode'];np.testing.assert_allclose(actual[0]['target_xyz'],r['target_xyz'],rtol=0,atol=2e-6)
# Import only test helper definitions, not the prior test runner or candidate V3.
p=W/'check_front_contact_window_native_family_v3.py';sources[str(p)]=sha(p);tree=ast.parse(p.read_text());helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['hand_pose_for','make','step']];scope=dict(SimpleNamespace=NS,FrontCopRouteState=FrontCopRouteState,WindowFrontCopRouteState=WindowFrontCopRouteState,TracedPeakLoadControl=TracedPeakLoadControl,support_vertex=support_vertex,values=[1.]*17+[0.]*7);exec(compile(ast.Module(body=helpers,type_ignores=[]),'<test helper definitions only>','exec'),scope)
make,step=scope['make'],scope['step'];state=make(WindowFrontCopRouteState,True,mode='top_cross');reference={'reference_local':np.zeros(3)};sequence=[]
def advance(t,values):
 before=state.top_mode;row=step(state,t,values);interval=assert_consumed(state,row,t);assert interval['observed_phase']==before
 sequence.append(dict(step=t,interval=interval,phase_before=before,phase_native_after=state.top_mode,phase_after_adapter=state.top_mode,counter_after=state.lost_contact_steps,recontacts=state.recontacts,adapter='none'))
 return row

def adapter(row,t,kind,recovery=False):
 global reference
 event=dict(kind=kind,context=dict(recontacts=state.recontacts))
 if kind=='handover':event.update(measured_ready_count=3,reference={'reference_local':[0.,0.,0.]},observed_support_xyz=[.4,-.08,.79],selected_surface_local_xy=[0.,0.])
 row,reference=(recovery_apply if recovery else initial_apply)(row,state,reference,event,object_xyz=np.array([.4,-.08,.77]),object_rotation=np.eye(3))
 assert state._window_pending is None and state._window_active is None
 # Adapter returns a copy preserving the pre-adapter native interval.
 assert row['contact_window_interval']==sequence[-1]['interval'];assert state.lost_contact_steps==0
 sequence[-1].update(phase_after_adapter=state.top_mode,adapter=('recovery_' if recovery else 'initial_')+kind)
 return row
for t in [1,2]:adapter(advance(t,[0.]*24),t,'command')
adapter(advance(3,[0.]*24),3,'handover');assert state.top_mode=='top_press'
for t in range(4,8):row=advance(t,[1.]*24)
assert state.top_mode=='top_push' and row['contact_window_interval']['evidence'] is None
row=advance(8,[1.]*17+[0.]*7);assert row['contact_window_interval']['evidence']['additional_intermittent_evidence']
for t in range(9,12):row=advance(t,[0.]*24)
assert state.top_mode=='top_lift' and state.recontacts==1 and state.last_recontact_reason=='lost_contact'
adapter(row,11,'command',True);adapter(advance(12,[0.]*24),12,'handover',True);assert state.top_mode=='top_press'
for t in range(13,17):row=advance(t,[1.]*24)
assert state.top_mode=='top_push'
transition=[x for x in sequence if x['step']>=13 and x['phase_before']=='top_press' and x['phase_native_after']=='top_push'];assert len(transition)==1 and transition[0]['interval']['evidence'] is None
row=advance(17,[1.]*24);assert row['contact_window_interval']['evidence'] is not None
# Explicit terminal-position branch with original10-sample release monitor.
terminal=make(WindowFrontCopRouteState,True);terminal.position_release_monitor=ConfirmedPositionRelease(-.09,1)
for _ in range(9):terminal.position_release_monitor.observe((.4,.21,.77))
terminal.load.observe(action_step=1,after_action_step=0,vertical_load_n=[1.]*24);terminal.observe_contact_window(action_step=1,after_action_step=0,vertical_load_n=[1.]*24,instantaneous_load_n=1.)
pose=scope['hand_pose_for']((.4,.21,.79),(0.,0.,0.,1.));row=terminal.update((.4,.21,.86),(.4,.21,.77),(.6,.1,.77),.075,.075,tip=(.4,.21,.79),quat=(0.,0.,0.,1.),obstacle_quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=1.,hand_obstacle_gap_m=.05,**pose);terminal_interval=assert_consumed(terminal,row,1);assert terminal_interval['evidence'] is None and row['mode']=='top_release' and row['release_reason']=='confirmed_original_target_position'
# A latched route guard consumes every interval without a pressure update.
state2=make(WindowFrontCopRouteState,True);guarded=[]
for t in [1,2,3]:
 row=step(state2,t,[0.]*24,hand_obstacle_gap_m=.001 if t==1 else .05);i=assert_consumed(state2,row,t);assert i['evidence'] is None and row['mode']=='front_guard_lift';guarded.append(i)
assert state2.load.updates==[]
# Native exception consumes once; the next valid interval is accepted.
state3=make(WindowFrontCopRouteState,True);state3.cop_drive_step_m=.009
try:step(state3,1)
except ValueError:pass
else:raise AssertionError('native exception absent')
assert state3._window_pending is state3._window_active is None;state3.cop_drive_step_m=.001;row=step(state3,2);assert_consumed(state3,row,2)
# Reproduce the newly found structural-auditor bug on the real first interval.
import front_contact_window_stage_source_binding_v1 as old_binding
first=dict(step=1,**first_interval);meta=dict(front_contact_window=dict(version='front_window_native_v4',enabled=True,selected_front=True,recorded_intervals=1,training_ready=False));log=dict(version='front_window_native_v4',enabled=True,selected_front=True,rows=[first],executed_frames=2,training_ready=False)
try:old_binding.verify_window_structure(enabled=True,task='nudge_mailer_to_bin',frames=2,meta=meta,plan=dict(front_route_selected=True,front_contact_window=old_binding.WINDOW_PLAN),log=log)
except AssertionError:old_rejects_legal_none=True
else:raise AssertionError('Expected old source binding bug')
for module in list(sys.modules.values()):
 path=getattr(module,'__file__',None)
 if path:
  p=Path(path).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,actual_constructor_initial_phase_none=True,first_native_interval=first_interval,first_parent_identity=True,first_original_waypoint_matches=True,adapter_sequence=sequence,terminal_interval=terminal_interval,latched_guard_intervals=guarded,exception_next_interval_accepted=True,old_structural_binding_rejects_legal_first_none=old_rejects_legal_none,source_sha256=sources,complete_unloaded_planner_rollout=False,physics_verified=False,training_ready=False)
with (D/'NATIVE_LIFECYCLE_CHECK_V3.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_first_none=True,adapter_updates=len(sequence),latched_guard_updates=len(guarded),old_binding_bug_reproduced=True)))
