"""Controlled synthetic native phase/pressure regression, not actual physics.
Uses the original peak-load adapter and actual top-contact update method.
Does not verify FrontCopRoute, IK/final geometry, or full observed trajectories.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,json,hashlib,datetime,math
W=Path(__file__).resolve().parent;C=W/'front_contact_window_candidate_v1';S=W/'staged_front_loaded_z_quarter_v1';sys.path[:0]=[str(C),str(S),str(W.parents[1])]
from simfoundry.data.top_contact_bypass import TopContactBypassState
from top_contact_window import WindowTopContactBypassState
from peak_load_update_trace import TracedPeakLoadControl
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[];negative=[]
def make(cls,enabled=False,selected=True,mode='top_push'):
 s=cls(rear=SimpleNamespace(plan=dict(direction=1,initial_target_xyz=[.4,-.09,.77],margin=.012)),side='left',size=(.15,.145,.04),mode=mode,top_mode=mode,command=(.4,-.08,.79),start=(.4,-.08,.79),guarded_descent=True,continuous_drag=True,front_inset_fraction=1.,recontact_travel_z=.86,tilt_recontact_rad=.03,confirm_terminal_release=True)
 s.load=TracedPeakLoadControl(5.,min_bias_m=-.006);s.load.bind_owner(s)
 if isinstance(s,WindowTopContactBypassState):s.contact_window_enabled=enabled;s.contact_window_selected_front=selected
 return s
def step(s,t,values,*,quat=(0.,0.,0.,1.),target=(.4,-.08,.77)):
 load=float(values[-1]);s.load.observe(action_step=t,after_action_step=t-1,vertical_load_n=values)
 if isinstance(s,WindowTopContactBypassState) and s.contact_window_enabled:s.observe_contact_window(action_step=t,after_action_step=t-1,vertical_load_n=values,instantaneous_load_n=load)
 return s.update((.4,-.08,.86),target,(.55,.15,.77),.075,.07,tip=(.4,-.08,.79),quat=quat,control_offset_local=(0.,0.,0.),load_n=load)
for label,enabled,selected,values in [('disabled',False,True,[1.]*23+[0.]),('rear',True,False,[1.]*23+[0.]),('no_contact',True,True,[0.]*24),('single_peak',True,True,[20.]+[0.]*23),('full_contact',True,True,[1.]*24)]:
 old=make(TopContactBypassState);new=make(WindowTopContactBypassState,enabled,selected)
 for t in range(1,7):
  a=step(old,t,values);b=step(new,t,values);e=b.pop('contact_window_loss_evidence',None);assert a==b,(label,t)
  assert old.lost_contact_steps==new.lost_contact_steps and old.load.bias_m==new.load.bias_m and old.load.filtered_n==new.load.filtered_n
 records.append(dict(case=label,original_output_identity_steps=6,final_mode=new.top_mode,passed=True))
old=make(TopContactBypassState);new=make(WindowTopContactBypassState,True);values=[1.]*17+[0.]*7
for t in range(1,4):
 a=step(old,t,values);b=step(new,t,values)
 assert b['contact_load']['observed_vertical_load_n']==a['contact_load']['observed_vertical_load_n']==0
 assert b['contact_load']['filtered_vertical_load_n']==a['contact_load']['filtered_vertical_load_n']
assert a['mode']=='top_lift' and b['mode']=='top_push' and new.lost_contact_steps==0
records.append(dict(case='majority_intermit_preserves_push_loss_counter_only',steps=3,parent_mode=a['mode'],candidate_mode=b['mode'],passed=True))
for t in range(4,7):b=step(new,t,[0.]*24)
assert b['mode']=='top_lift' and b['last_recontact_reason']=='lost_contact'
records.append(dict(case='three_complete_lost_intervals_still_recontact',passed=True))
for label,kw,expected in [('tilt',dict(quat=(math.sin(.05),0.,0.,math.cos(.05))),'top_lift'),('terminal',dict(target=(.4,.25,.77)),'top_release')]:
 s=make(WindowTopContactBypassState,True);s.lost_contact_steps=2;b=step(s,1,values,**kw);assert b['mode']==expected
 if label=='tilt':assert b['last_recontact_reason']=='incipient_tilt_independent'
 records.append(dict(case=label+'_priority_preserved',mode=b['mode'],passed=True))
s=make(WindowTopContactBypassState,True);b=step(s,1,[20.]*17+[0.]*7);g=b['contact_load']['peak_bias_guard'];assert g['peak_exceeded'] and g['held_negative_increment'] and s.load.bias_m==0
records.append(dict(case='original_peak_negative_increment_guard_preserved',passed=True))
for label,enabled,selected in [('nonpush',True,True)]:
 a=make(TopContactBypassState,mode='top_press');b=make(WindowTopContactBypassState,enabled,selected,mode='top_press')
 x=step(a,1,values);y=step(b,1,values);y.pop('contact_window_loss_evidence');assert x==y
 records.append(dict(case='nonpush_identity',passed=True))
def reject(label,fn):
 try:fn()
 except ValueError:negative.append(label)
 else:raise AssertionError(label)
s=make(WindowTopContactBypassState,True);base=dict(action_step=1,after_action_step=0,vertical_load_n=values,instantaneous_load_n=0.)
s.observe_contact_window(**base);reject('duplicate_unconsumed_interval',lambda:s.observe_contact_window(**base));s.top_mode='top_press';reject('phase_changed_between_observation_and_update',lambda:s._consume_contact_window(0.))
s=make(WindowTopContactBypassState,True);reject('missing_observation',lambda:s._consume_contact_window(0.));reject('future_observation',lambda:s.observe_contact_window(**dict(base,after_action_step=1)))
s.observe_contact_window(**base);reject('pressure_window_action_mismatch',lambda:s._consume_contact_window(0.));s.load._last_action_step=1;s._consume_contact_window(0.);reject('reused_observation',lambda:s._consume_contact_window(0.));reject('stale_action',lambda:s.observe_contact_window(**base))
paths=[Path(__file__),C/'top_contact_window.py',C/'contact_window_evidence.py',C/'NATIVE_BASE_PREPARATION_V1.json',W.parents[1]/'simfoundry/data/top_contact_bypass.py',W.parents[1]/'simfoundry/data/contact_load_control.py',*[S/n for n in ['peak_load_update_trace.py','peak_load_control_adapter.py','peak_load_bias_guard.py']]]
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,cases=records,negative_rejections=negative,source_sha256={str(p):sha(p) for p in paths},native_base_only=True,front_route_wired=False,physics_verified=False,training_ready=False)
with (C/'NATIVE_BASE_PHASE_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,cases=len(records),negative_rejections=len(negative))))
