"""Controlled native full-front family tests with persistent controller history.
Real front/COP/initial-center/peak-control classes, synthetic observed geometry.
No IK/final-guard replay or new physics; not a training-admission proof.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,math
W=Path(__file__).resolve().parent;C=W/'front_contact_window_candidate_v1';S=W/'staged_front_loaded_z_quarter_v1';sys.path[:0]=[str(C),str(S),str(W.parents[1])]
from front_initial_center_cop_route import FrontCopRouteState
from front_window_native_v3 import WindowFrontCopRouteState
from peak_load_update_trace import TracedPeakLoadControl
from simfoundry.data.top_contact_bypass import support_vertex
def hand_pose_for(point,quat):
 vertex=support_vertex('left',(0.,0.,0.,1.),quat)
 return dict(observed_hand_xyz=tuple(point[i]-vertex[i] for i in range(3)),observed_hand_quat_xyzw=(0.,0.,0.,1.))
records=[];negative=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def make(cls,enabled=False,selected=True,mode='top_push'):
 s=cls(rear=SimpleNamespace(plan=dict(direction=1,initial_target_xyz=[.4,-.09,.77],obstacle_initial_xyz=[.6,.1,.77],margin=.012)),side='left',size=(.15,.145,.04),obstacle_size=(.15,.145,.04),mode=mode,top_mode=mode,command=(.4,-.08,.79),start=(.4,-.08,.79),guarded_descent=True,continuous_drag=True,front_inset_fraction=1.,recontact_travel_z=.86,tilt_recontact_rad=.03,confirm_terminal_release=True,route_report=dict(goal_y=.4),route_x=.4,route_stage='lateral_y',edge_core_size=(.135,.1276,.04))
 s.load=TracedPeakLoadControl(5.,min_bias_m=-.006);s.load.bind_owner(s)
 if cls is WindowFrontCopRouteState:s.contact_window_enabled=enabled;s.contact_window_selected_front=selected
 return s
values=[1.]*17+[0.]*7
def step(s,t,values=values,**kw):
 load=float(values[-1]);s.load.observe(action_step=t,after_action_step=t-1,vertical_load_n=values)
 if isinstance(s,WindowFrontCopRouteState) and s.contact_window_enabled:s.observe_contact_window(action_step=t,after_action_step=t-1,vertical_load_n=values,instantaneous_load_n=load)
 args=dict(tip=(.4,-.08,.79),quat=(0.,0.,0.,1.),obstacle_quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=load,hand_obstacle_gap_m=.05);args.update(kw)
 if isinstance(s,WindowFrontCopRouteState):args.update(hand_pose_for(args['tip'],args['quat']))
 return s.update((.4,-.08,.86),(.4,-.08,.77),(.6,.1,.77),.075,.075,**args)
for label,enabled,selected,v,extra in [('disabled',False,True,values,{}),('unselected',True,False,values,{}),('zero',True,True,[0.]*24,{}),('single_peak',True,True,[20.]+[0.]*23,{}),('continuous',True,True,[1.]*24,{}),('edge_eligibility',True,True,values,dict(tip=(.46,-.08,.79)))]:
 old=make(FrontCopRouteState);new=make(WindowFrontCopRouteState,enabled,selected)
 for t in range(1,8):
  a=step(old,t,v,**extra);b=step(new,t,v,**extra);b.pop('contact_window_interval',None);assert a==b,(label,t,a,b)
  assert old.load.bias_m==new.load.bias_m and old.lost_contact_steps==new.lost_contact_steps
 records.append(dict(case=label,native_steps=7,identity=True))
a=make(FrontCopRouteState);b=make(WindowFrontCopRouteState,True)
for t in range(1,4):x=step(a,t);y=step(b,t)
assert x['mode']=='top_lift' and y['mode']=='top_push';assert y['contact_window_interval']['evidence']['additional_intermittent_evidence'];records.append(dict(case='intermittent_three_steps',parent=x['mode'],candidate=y['mode']))
for t in range(4,7):y=step(b,t,[0.]*24)
assert y['mode']=='top_lift' and y['last_recontact_reason']=='lost_contact';records.append(dict(case='complete_separation_still_lifts'))
for label,kw in [('hand_guard',dict(hand_obstacle_gap_m=.001)),('tilt',dict(quat=(math.sin(.05),0.,0.,math.cos(.05))))]:
 a=make(FrontCopRouteState);b=make(WindowFrontCopRouteState,True)
 for t in range(1,4):
  x=step(a,t,**kw);y=step(b,t,**kw);audit=y.pop('contact_window_interval');assert x==y;assert audit['evidence'] is None;assert b._window_pending is None and b._window_active is None
 records.append(dict(case=label+'_three_intervals_consumed_without_loss_update',native_steps=3,output_mode=y['mode']))
b=make(WindowFrontCopRouteState,True);y=step(b,1,[20.]*17+[0.]*7);assert y['contact_load']['peak_bias_guard']['held_negative_increment'];records.append(dict(case='original_peak_guard'))
a=make(FrontCopRouteState);b=make(WindowFrontCopRouteState,True)
for s in [a,b]:s.recontact_on_route_change=True;s.route_stage='front_x'
x=step(a,1,[1.]*24);y=step(b,1,[1.]*24);audit=y.pop('contact_window_interval');assert x==y and audit['evidence'] is None and y['direction_change_recontact']['restarted'];records.append(dict(case='native_route_transition_can_change_phase_before_loss',interval=audit))
def reject(label,fn):
 try:fn()
 except ValueError:negative.append(label)
 else:raise AssertionError(label)
b=make(WindowFrontCopRouteState,True);base=dict(action_step=1,after_action_step=0,vertical_load_n=values,instantaneous_load_n=0.)
b.observe_contact_window(**base);reject('duplicate_pending',lambda:b.observe_contact_window(**base));reject('bad_previous_step',lambda:make(WindowFrontCopRouteState,True).observe_contact_window(**dict(base,after_action_step=1)))
def bare(s,**extra):
 args=dict(tip=(.4,-.08,.79),quat=(0.,0.,0.,1.),obstacle_quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=0.,hand_obstacle_gap_m=.05);args.update(extra)
 if isinstance(s,WindowFrontCopRouteState):args.update(hand_pose_for(args['tip'],args['quat']))
 return s.update((.4,-.08,.86),(.4,-.08,.77),(.6,.1,.77),.075,.075,**args)
reject('pressure_interval_mismatch',lambda:bare(b));b.load.observe(action_step=1,after_action_step=0,vertical_load_n=values)
reject('changed_force',lambda:bare(b,load_n=1.));b.top_mode='top_press';reject('changed_external_phase',lambda:bare(b));b.top_mode='top_push'
reject('nonfinite_geometry',lambda:bare(b,tip=(float('nan'),0.,0.)));b.edge_core_size=None;reject('missing_actual_core',lambda:bare(b));b.edge_core_size=(.135,.1276,.04);bare(b);reject('reuse',lambda:bare(b));reject('stale_step',lambda:b.observe_contact_window(**base))
reject('missing_observation',lambda:bare(make(WindowFrontCopRouteState,True)))
b=make(WindowFrontCopRouteState,True);b.cop_drive_step_m=.009
try:step(b,1)
except ValueError:pass
else:raise AssertionError('expected original invalid drive rejection')
assert b._window_active is None and b._window_pending is None and b.window_last_disposition['disposition']=='native_update_exception_consumed';records.append(dict(case='native_exception_consumption_recorded'))
# Virtual control point outside core must not replace actual measured hull point.
b=make(WindowFrontCopRouteState,True)
b.load.observe(action_step=1,after_action_step=0,vertical_load_n=values);b.observe_contact_window(**base)
kw=dict(tip=(.49,-.08,.79),quat=(0.,0.,0.,1.),obstacle_quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=0.,hand_obstacle_gap_m=.05)
kw.update(hand_pose_for((.4,-.08,.79),kw['quat']))
y=b.update((.4,-.08,.86),(.4,-.08,.77),(.6,.1,.77),.075,.075,**kw)
g=y['contact_window_interval']['geometry'];assert g['current_support_core_margin_m']>.06 and g['virtual_control_reference_xyz'][0]==.49
assert y['contact_window_interval']['evidence']['additional_intermittent_evidence']
records.append(dict(case='virtual_reference_different_from_physical_hull',geometry=g))
paths=[Path(__file__),C/'NATIVE_FAMILY_DERIVATION_V2.json',C/'front_window_native_v3.py',C/'contact_window_evidence_v2.py',*[C/x for x in ['window_initial_center_top_v2.py','window_initial_center_route_v2.py','window_initial_center_cop_v2.py']],*[S/x for x in ['front_initial_center_top_contact.py','front_initial_center_route.py','front_initial_center_cop_route.py','peak_load_update_trace.py','peak_load_control_adapter.py','peak_load_bias_guard.py']]]
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,cases=records,negative_rejections=negative,source_sha256={str(p):sha(p) for p in paths},actual_front_family=True,synthetic_observations=True,collector_modified=False,physics_verified=False,training_ready=False)
with (C/'NATIVE_FAMILY_CHECK_V3.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,cases=len(records),negative_rejections=len(negative))))
