"""Real failed-entry context through candidate waiting branch and independent stream.
This is a branch fixture with a placeholder parent command, not new physics.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from audit_front_recontact_headroom_stream import RecoveryStreamAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=W/'front_recontact_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin/front_recontact_center.json';source=json.loads(p.read_text());old=next(x for x in source['rows'] if x['kind']=='command');c=old['context'];z=c['scene'];guard=ClearanceGuard(ROOT,S)
scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size'])
a={k:c[k] for k in ['step','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']}
a.update(scene=scene,**{k:np.asarray(c[k]) for k in ['current','previous_q','previous_command','decay','observed_hand_pose','observed_inactive_hand_pose']})
life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=c['recontacts']);ev=life.update(**a);assert ev['reason']=='waiting_for_inactive_hand_planning_headroom' and not life.attempted and not life.active
ev.update(real_recontact_index=c['recontacts'],center_local_after=None)
row=dict(recontacts=c['recontacts'],mode=c['parent_mode'],contact_load=dict(observed_vertical_load_n=c['observed_load_n'],filtered_vertical_load_n=c['filtered_load_n']))
coord=dict(controller_kind='branch_fixture_parent_placeholder',front_recontact_center_override=None)
k=dict(step=c['step'],current=a['current'],previous_q=a['previous_q'],previous_command=a['previous_command'],final_command=a['previous_command'],scene=z,decay=a['decay'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
def checker():
 ch=RecoveryStreamAudit(ROOT,S);ch.last_step=c['step']-1;return ch
g,_=checker().selection.geometry(a['current'],z)
print(json.dumps(dict(candidate_height=ev['planning_headroom']['actual_z_m'],independent_height=g['inactive_lowest_z_m'],difference=ev['planning_headroom']['actual_z_m']-g['inactive_lowest_z_m'])),flush=True)
ch=checker();assert ch.observe(ev,row,coord,**k);assert not ch.attempted and not ch.finished and not ch.audit.active
checks=[]
for label in ['wrong_reason','wrong_actual_height','wrong_entry_threshold','wrong_original_gate','extra_reserve_field','missing_context','loaded_wait','guard_wait','wrong_counter','wrong_phase']:
 e,r,co,kw=copy.deepcopy((ev,row,coord,k))
 if label=='wrong_reason':e['reason']='waiting_for_original_unloaded_geometry'
 if label=='wrong_actual_height':e['planning_headroom']['actual_z_m']+=1e-5
 if label=='wrong_entry_threshold':e['planning_headroom']['required_entry_z_m']=.84
 if label=='wrong_original_gate':e['planning_headroom']['original_gate_z_m']=.839
 if label=='extra_reserve_field':e['planning_headroom']['allow_relaxation']=True
 if label=='missing_context':e.pop('context')
 if label=='loaded_wait':e['context']['observed_load_n']=kw['observed_load_n']=.1
 if label=='guard_wait':r['route_stop_reason']='fixture_guard'
 if label=='wrong_counter':e['real_recontact_index']=2
 if label=='wrong_phase':r['mode']='top_push'
 try:checker().observe(e,r,co,**kw)
 except (AssertionError,KeyError,ValueError):checks.append(label)
 else:raise AssertionError(label)
# Same measured pose at next step remains a wait, never consumes an attempt.
a['step']+=1;ev2=life.update(**a);ev2.update(real_recontact_index=c['recontacts'],center_local_after=None);kw=dict(k,step=a['step']);assert ch.observe(ev2,row,coord,**kw);assert not life.attempted and not ch.attempted
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,physical_context_step=c['step'],candidate_height=ev['planning_headroom']['actual_z_m'],independent_height=g['inactive_lowest_z_m'],negative_cases=checks,repeated_wait_consumes_no_attempt=True,source_sha256={str(x):sha(x) for x in [Path(__file__),p,W/'audit_front_recontact_headroom_stream.py',S/'front_recontact_center_lifecycle.py']},simulation_started=False,training_ready=False)
with (S/'WAIT_STREAM_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,negative=len(checks))))
