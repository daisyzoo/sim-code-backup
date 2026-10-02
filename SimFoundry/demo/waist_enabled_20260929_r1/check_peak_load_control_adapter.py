"""Uninstalled adapter checks including actual frozen top-controller transitions.
Synthetic state fixtures, not a physical rollout or a successful-task claim.
"""
from pathlib import Path
from types import SimpleNamespace
import sys
import math
import json
import hashlib
import datetime
import copy

W = Path(__file__).resolve().parent
sys.path[:0] = [str(W.parents[1]), str(W/'staged_substep_observer'), str(W)]
from peak_load_control_adapter import PeakLoadControl
from simfoundry.data.contact_load_control import ContactLoadControl
from region_top_contact import TopContactBypassState

checks = []
def armed(*, peak=17., final=0., bias=-.001, filtered=5., step=1):
    c = PeakLoadControl(desired_n=5., bias_m=bias, filtered_n=filtered, min_bias_m=-.006)
    c.observe(action_step=step, after_action_step=step-1, vertical_load_n=[peak]+[final]*23)
    return c

def reject(name, fn):
    try:
        fn()
    except ValueError:
        checks.append(name)
    else:
        raise AssertionError(name)

c = armed(); r = c.update(0., True)
assert c.bias_m == -.001 and c.filtered_n == 3.75 and r['peak_bias_guard']['held_negative_increment']
checks.append('high_peak_holds_bias_original_filter_unchanged')
reject('observation_cannot_be_reused', lambda: c.update(0., True))
reject('same_action_cannot_be_rearmed', lambda: c.observe(action_step=1, after_action_step=0, vertical_load_n=[0.]*24))
c = armed(); old=(c.bias_m,c.filtered_n)
reject('mismatching_last_tick_rejected_before_mutation', lambda: c.update(1., True))
assert (c.bias_m,c.filtered_n)==old
c=armed(peak=17., final=17.); r=c.update(17.,True)
p=ContactLoadControl(5.,bias_m=-.001,filtered_n=5.,min_bias_m=-.006); expected=p.update(17.,True)
assert c.bias_m==p.bias_m and c.filtered_n==p.filtered_n and all(r[k]==v for k,v in expected.items())
checks.append('high_peak_upward_relief_exactly_parent')
for active in [False,True]:
    c=armed(peak=9.8,final=4.); p=ContactLoadControl(5.,bias_m=-.001,filtered_n=5.,min_bias_m=-.006)
    r=c.update(4.,active);expected=p.update(4.,active)
    assert all(r[k]==v for k,v in expected.items())
checks.append('below_threshold_parent_outputs_exact_active_and_inactive')
for name,kw in [('stale',dict(after_action_step=0,action_step=2,vertical_load_n=[0.]*24)),
                ('partial',dict(after_action_step=0,action_step=1,vertical_load_n=[0.]*23)),
                ('nan',dict(after_action_step=0,action_step=1,vertical_load_n=[math.nan]*24))]:
    c=PeakLoadControl(5.,min_bias_m=-.006)
    reject(name+'_observation_rejected', lambda kw=kw: c.observe(**kw))

def state(mode, **kwargs):
    rear=SimpleNamespace(plan={'direction':-1,'initial_target_xyz':(.5,0.,.775),'margin':.012})
    return TopContactBypassState(rear=rear,side='right',size=(.14,.09,.045),
                top_mode=mode,mode=mode,load=armed(),guarded_descent=True,
                continuous_drag=True,front_inset_fraction=1.,tilt_recontact_rad=.03,
                start=(.5,0.,.7975),command=(.5,0.,.7975),descent_z=.80,**kwargs)

args=dict(palm=(.5,0.,.85), target=(.5,0.,.775), obstacle=(.3,.2,.77),
          target_radius_x=.07, obstacle_radius_x=.075, tip=(.5,0.,.7975),
          quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=0.)

# Compare reset/filter/phase outcomes to the same original controller with its
# original load class. All mutations stay inside synthetic Python state objects.
scenarios=[('press_to_push', 'top_press', dict(settled=2), {}, 'top_push', False),
           ('tilt_guard_after_pressure', 'top_push', {}, {'quat':(0.,math.sin(.04/2),0.,math.cos(.04/2))},'top_lift',True),
           ('lost_contact_after_pressure', 'top_push', dict(lost_contact_steps=2), {},'top_lift',True),
           ('misaligned_press_resets_bias', 'top_press', {}, {'tip':(.54,0.,.7975)},'top_descend',True),
           ('descend_to_press_does_not_apply_stale_bias', 'top_descend', dict(settled=2), {},'top_press',False),
           ('release_keeps_bias_inactive', 'top_release', dict(release=(.5,0.,.7975)), {},'top_release',False)]
for name,mode,fields,inputs,expected_mode,reset in scenarios:
    new=state(mode,**fields);parent=copy.deepcopy(new)
    parent.load=ContactLoadControl(5.,bias_m=-.001,filtered_n=5.,min_bias_m=-.006)
    nr=new.update(**(args|inputs));pr=parent.update(**(args|inputs))
    assert nr['mode']==pr['mode']==expected_mode,(name,nr['mode'],pr['mode'])
    assert new.load.filtered_n==parent.load.filtered_n
    assert new.last_recontact_reason==parent.last_recontact_reason and new.recontacts==parent.recontacts
    if reset:assert new.load.bias_m==parent.load.bias_m==0.
    if mode not in ('top_press','top_push'):assert nr['contact_load']['applied_z_bias_m']==0.
    checks.append(name)

paths=[Path(__file__),W/'peak_load_control_adapter.py',W/'peak_load_bias_guard.py',
       W/'staged_substep_observer/region_top_contact.py',
       W.parents[1]/'simfoundry/data/contact_load_control.py']
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
         scope=__doc__,checks=checks,controller_installed=False,physical_validation=False,
         training_ready=False,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
dest=W/'PEAK_LOAD_CONTROL_ADAPTER_CHECK.json';assert not dest.exists()
dest.write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,checks=len(checks),physical_validation=False)))
