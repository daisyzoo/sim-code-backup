"""Uninstalled adapter checked on original controller transitions and real inputs.
Synthetic owner states and independent per-event replay only; no rollout.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,json,hashlib,datetime,math
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1]),str(W/'staged_peak_load_guard')]
from instant_load_control_adapter import InstantLoadControl
from peak_load_control_adapter import PeakLoadControl
from region_top_contact import TopContactBypassState
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks=[]

def armed(cls=InstantLoadControl,*,final=5.,peak=6.,bias=-.001,filtered=1.,step=1):
    c=cls(5.,bias_m=bias,filtered_n=filtered,min_bias_m=-.006);c.observe(action_step=step,after_action_step=step-1,vertical_load_n=[peak]+[final]*23);return c

def reject(name,fn):
    try:fn()
    except ValueError:checks.append(name)
    else:raise AssertionError(name)

c=armed();r=c.update(5.,True);assert c.bias_m==-.001 and c.filtered_n==2. and r['instantaneous_load_guard']['held_by_final_sample'];checks.append('lagging_filter_preserved_final_target_holds_down')
reject('consumed_observation_rejected',lambda:c.update(5.,True))
reject('duplicate_observation_rejected',lambda:c.observe(action_step=1,after_action_step=0,vertical_load_n=[5.]*24))
c=armed();old=(c.bias_m,c.filtered_n);reject('mismatched_load_rejected_without_mutation',lambda:c.update(4.,True));assert (c.bias_m,c.filtered_n)==old
for final,peak,filtered,active in [(4.9,6.,1.,True),(0.,17.,5.,True),(7.,8.,6.,True),(5.,6.,1.,False)]:
    c=armed(final=final,peak=peak,filtered=filtered);p=armed(PeakLoadControl,final=final,peak=peak,filtered=filtered)
    nr=c.update(final,active);pr=p.update(final,active);assert c.bias_m==p.bias_m and c.filtered_n==p.filtered_n and all(nr[k]==v for k,v in pr.items())
checks.append('below_target_peak_only_upward_and_inactive_match_parent')

def state(mode,**fields):
    rear=SimpleNamespace(plan={'direction':-1,'initial_target_xyz':(.5,0.,.775),'margin':.012})
    return TopContactBypassState(rear=rear,side='right',size=(.14,.09,.045),top_mode=mode,mode=mode,
        load=armed(),guarded_descent=True,continuous_drag=True,front_inset_fraction=1.,tilt_recontact_rad=.03,
        start=(.5,0.,.7975),command=(.5,0.,.7975),descent_z=.80,**fields)
args=dict(palm=(.5,0.,.85),target=(.5,0.,.775),obstacle=(.3,.2,.77),target_radius_x=.07,obstacle_radius_x=.075,tip=(.5,0.,.7975),quat=(0.,0.,0.,1.),control_offset_local=(0.,0.,0.),load_n=5.)
scenarios=[('press_to_push','top_press',dict(settled=2),{},'top_push',False),('tilt_guard_clears_after_hold','top_push',{},dict(quat=(0.,math.sin(.04/2),0.,math.cos(.04/2))),'top_lift',True),('misaligned_press_resets','top_press',{},dict(tip=(.54,0.,.7975)),'top_descend',True),('descent_does_not_activate_early','top_descend',dict(settled=2),{},'top_press',False),('release_inactive','top_release',dict(release=(.5,0.,.7975)),{},'top_release',False)]
for name,mode,fields,inputs,expected,reset in scenarios:
    a=state(mode,**fields);b=copy.deepcopy(a);b.load=armed(PeakLoadControl);ar=a.update(**(args|inputs));br=b.update(**(args|inputs));assert ar['mode']==br['mode']==expected and a.load.filtered_n==b.load.filtered_n
    assert a.recontacts==b.recontacts and a.last_recontact_reason==b.last_recontact_reason
    if reset:assert a.load.bias_m==b.load.bias_m==0.
    if mode not in ('top_press','top_push'):assert ar['contact_load']['applied_z_bias_m']==0.
    checks.append(name)
a=state('top_push',lost_contact_steps=2);a.load=armed(final=0.,peak=17.,filtered=5.);b=copy.deepcopy(a);b.load=armed(PeakLoadControl,final=0.,peak=17.,filtered=5.);ar=a.update(**(args|dict(load_n=0.)));br=b.update(**(args|dict(load_n=0.)));assert ar['mode']==br['mode']=='top_lift' and a.load.bias_m==b.load.bias_m==0.;checks.append('original_three_sample_lost_contact_guard_preserved')
source=W/'INSTANT_LOAD_BIAS_GUARD_CHECK.json';proof=json.loads(source.read_text());assert proof['passed']
for p,h in proof['source_sha256'].items():assert sha(p)==h
counts=[]
for row in proof['rows']:
    ep=next((W/'peak_guard_groups_r1').glob('case_*/'+row['episode']));p=json.loads((ep/'peak_load_updates.json').read_text());h=json.loads((ep/'PEAK_GUARD_LOAD_HISTORY.json').read_text());loads={x['action_step']:x['vertical_load_n'] for x in h['rows']};changed=0
    for e in p['rows']:
        before=e['before'];c=InstantLoadControl(5.,bias_m=before['bias_m'],filtered_n=before['filtered_n'],min_bias_m=-.006);t=e['action_step'];c.observe(action_step=t,after_action_step=t-1,vertical_load_n=loads[t-1]);result=c.update(e['observed_vertical_load_n'],e['active'])
        assert c.filtered_n==e['after']['filtered_n'];proposal=e['returned']['peak_bias_guard']['proposed_bias_m'];expected=before['bias_m'] if (e['active'] and loads[t-1][-1]>=5. and proposal<before['bias_m']) else e['after']['bias_m'];assert c.bias_m==expected
        changed+=abs(c.bias_m-e['after']['bias_m'])>1e-12
    assert changed==row['additional_holds'];counts.append(dict(episode=ep.name,actual_input_events=len(p['rows']),additional_holds=changed))
paths=[Path(__file__),W/'instant_load_control_adapter.py',W/'instant_load_bias_guard.py',W/'peak_load_control_adapter.py',W/'peak_load_bias_guard.py',W/'staged_peak_load_guard/region_top_contact.py',W.parents[1]/'simfoundry/data/contact_load_control.py',source]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,checks=checks,actual_input_one_step_counts=counts,controller_installed=False,physical_validation=False,training_ready=False,source_sha256={str(p):sha(p) for p in paths});dest=W/'INSTANT_LOAD_CONTROL_ADAPTER_CHECK.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,checks=len(checks),one_step_counts=counts,physical_validation=False),indent=2))
