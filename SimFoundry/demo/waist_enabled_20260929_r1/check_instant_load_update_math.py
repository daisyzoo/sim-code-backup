"""Test independent event audit using a prospective real-call-boundary tracer.
Recorded inputs/pre-states are reused independently; all outputs here are
synthetic candidate events, not an executed candidate physical rollout.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from instant_load_update_trace import TracedInstantLoadControl
from audit_instant_load_update_math import verify_event
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks=[];files=[]

def event(*,active=True,final=5.,peak=6.,filtered=1.,bias=-.001,step=9):
 c=TracedInstantLoadControl(5.,bias_m=bias,filtered_n=filtered,min_bias_m=-.006);owner=SimpleNamespace(load=c,top_mode='top_push' if active else 'top_release');c.bind_owner(owner);values=[peak]+[final]*23;c.observe(action_step=step,after_action_step=step-1,vertical_load_n=values);result=c.update(final,active);assert len(c.updates)==1;return c,result,values
c,r,values=event();valid=c.updates[0];verified=verify_event(valid,action_step=9,previous_action_loads=values);assert verified['additional_final_hold'];checks.append('independent_final_hold_check')
r['instantaneous_load_guard']['guarded_bias_m']=99.;assert c.updates[0]['returned']['instantaneous_load_guard']['guarded_bias_m']==-.001;checks.append('returned_dictionary_mutation_does_not_change_trace')
for name,params in [('peak_only',dict(final=0.,peak=17.,filtered=5.)),('upward',dict(final=8.,peak=9.,filtered=6.)),('inactive',dict(active=False))]:
 cc,_,vv=event(**params);verify_event(cc.updates[0],action_step=9,previous_action_loads=vv);checks.append(name+'_independently_checked')

def reject(name,mutator):
 e=copy.deepcopy(valid);mutator(e)
 try:verify_event(e,action_step=9,previous_action_loads=values)
 except (AssertionError,KeyError,ValueError):checks.append(name)
 else:raise AssertionError(name)
reject('original_peak_bias_cannot_replace_actual_final_bias',lambda e:e['after'].__setitem__('bias_m',e['returned']['peak_bias_guard']['guarded_bias_m']))
reject('inner_peak_result_cannot_be_relabelled_final',lambda e:e['returned']['peak_bias_guard'].__setitem__('guarded_bias_m',e['after']['bias_m']))
reject('filtered_state_tampering',lambda e:e['after'].__setitem__('filtered_n',2.1))
reject('missing_instant_guard',lambda e:e['returned'].pop('instantaneous_load_guard'))
reject('wrong_final_sample',lambda e:e['preceding_observation'].__setitem__('final_load_n',4.))
reject('wrong_peak_sample',lambda e:e['preceding_observation'].__setitem__('previous_action_peak_n',7.))
reject('stale_observation',lambda e:e['preceding_observation'].__setitem__('observed_after_action_step',7))
reject('wrong_action',lambda e:e.__setitem__('action_step',10))
reject('partial_substeps',lambda e:e['preceding_observation'].__setitem__('observed_solver_substeps',23))
reject('changed_target',lambda e:e['before'].__setitem__('desired_n',4.))
reject('changed_lower_bound',lambda e:e['before'].__setitem__('min_bias_m',-.01))
reject('phase_activation_mismatch',lambda e:e.__setitem__('phase_at_update','top_release'))
reject('returned_stored_bias_tampering',lambda e:e['returned'].__setitem__('stored_z_bias_m',-.0015))
reject('returned_applied_bias_tampering',lambda e:e['returned'].__setitem__('applied_z_bias_m',0.))
reject('false_final_hold_flag',lambda e:e['returned']['instantaneous_load_guard'].__setitem__('held_by_final_sample',False))
source=(W/'instant_load_update_trace.py').read_text().replace('from instant_load_control_adapter import InstantLoadControl','from peak_load_control_adapter import PeakLoadControl').replace('class TracedInstantLoadControl(InstantLoadControl):','class TracedPeakLoadControl(PeakLoadControl):');assert source==(W/'peak_load_update_trace.py').read_text();checks.append('trace_body_exact_parent_except_explicit_class')
rows=[]
for case,task in [(840001,'push_box_to_bin'),(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin'),(840004,'nudge_mailer_to_bin'),(840000,'push_box_to_bin'),(840000,'nudge_mailer_to_bin')]:
 ep=W/'peak_guard_groups_r1'/f'case_{case}'/f'layout_{case}_{task}';proof=json.loads((ep/'PRESSURE_STREAM_DIAGNOSIS.json').read_text());assert proof['pressure_verification']['passed']
 for p,h in proof['source_sha256'].items():assert sha(p)==h
 h=json.loads((ep/'PEAK_GUARD_LOAD_HISTORY.json').read_text());loads={x['action_step']:x['vertical_load_n'] for x in h['rows']};events=json.loads((ep/'peak_load_updates.json').read_text())['rows'];additional=0
 for e in events:
  b=e['before'];t=e['action_step'];c=TracedInstantLoadControl(5.,bias_m=b['bias_m'],filtered_n=b['filtered_n'],min_bias_m=-.006);c.bind_owner(SimpleNamespace(load=c,top_mode=e['phase_at_update']));c.observe(action_step=t,after_action_step=t-1,vertical_load_n=loads[t-1]);c.update(e['observed_vertical_load_n'],e['active']);assert len(c.updates)==1;v=verify_event(c.updates[0],action_step=t,previous_action_loads=loads[t-1]);additional+=v['additional_final_hold']
 rows.append(dict(episode=ep.name,synthetic_events=len(events),additional_final_holds=additional));files.extend(ep/n for n in ['PRESSURE_STREAM_DIAGNOSIS.json','PEAK_GUARD_LOAD_HISTORY.json','peak_load_updates.json'])
files.extend(W/n for n in ['instant_load_update_trace.py','instant_load_control_adapter.py','instant_load_bias_guard.py','peak_load_update_trace.py','peak_load_control_adapter.py','peak_load_bias_guard.py','audit_instant_load_update_math.py']);files.append(Path(__file__))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,checks=checks,rows=rows,source_sha256={str(p):sha(p) for p in files},controller_installed=False,physical_validation=False,training_ready=False);dest=W/'INSTANT_LOAD_UPDATE_MATH_CHECK.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,checks=len(checks),rows=rows,physical_validation=False),indent=2))
