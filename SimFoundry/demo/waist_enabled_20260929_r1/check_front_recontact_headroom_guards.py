"""Guard/default/record corruption checks for isolated headroom candidate.
Reuses explicitly affine fixtures; does not create physical demonstrations.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_center';D=W/'front_bag_recontact_headroom_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from front_recontact_center_lifecycle import FrontRecontactCenterLifecycle
from audit_front_recontact_center_events import RecoveryEventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();base=json.loads((D/'PROBE_RESULT.json').read_text());assert base['passed'];guard=ClearanceGuard(ROOT,S);checks=[]
for p,h in base['source_sha256'].items():assert sha(p)==h,p
rec=base['records'][0];ev=rec['events'][0];ctx=ev['context'];z=ctx['scene'];scene=RecontactScene(guard,z['side'],z['target_xyz'],z['target_quat'],z['core_size'],z['other_xyz'],z['other_quat'],z['other_size']);plan=ev['planning']
def inp(c):
 return dict(step=c['step'],selected=c['selected'],parent_mode=c['parent_mode'],recontacts=c['recontacts'],guard_stop=c['guard_stop'],observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'],scene=scene,current=np.asarray(c['current']),previous_q=np.asarray(c['previous_q']),previous_command=np.asarray(c['previous_command']),decay=np.asarray(c['decay']),observed_hand_pose=np.asarray(c['observed_hand_pose']),observed_inactive_hand_pose=np.asarray(c['observed_inactive_hand_pose']))
def fresh_active():
 life=FrontRecontactCenterLifecycle(enabled=True,recontact_index=rec['counter'])
 with patch('front_recontact_center_lifecycle.plan',return_value=copy.deepcopy(plan)):
  actual=life.update(**inp(ctx));assert actual==ev
 return life
for label,change in [('guard',dict(guard_stop=True)),('loaded',dict(observed_load_n=.01)),('filter_loaded',dict(filtered_load_n=.051)),('counter_changed',dict(recontacts=rec['counter']+1)),('not_selected',dict(selected=False)),('wrong_phase',dict(parent_mode='top_push')),('observation_gap',dict(step=ctx['step']+2))]:
 life=fresh_active();a=inp(rec['events'][1]['context']);a.update(change);out=life.update(**a);assert out['kind']=='stop' and out['requires_stop'] and not life.active;checks.append(label)
life=fresh_active();life.ticks=240;out=life.update(**inp(rec['events'][1]['context']));assert out['kind']=='stop' and out['reason']=='initial_front_path_budget_exhausted';checks.append('original240_budget')
life=fresh_active();a=inp(rec['events'][1]['context']);zz=dict(z);zz['target_xyz']=list(z['target_xyz']);zz['target_xyz'][0]+=.003;a['scene']=RecontactScene(guard,zz['side'],zz['target_xyz'],zz['target_quat'],zz['core_size'],zz['other_xyz'],zz['other_quat'],zz['other_size']);out=life.update(**a);assert out['kind']=='stop' and out['reason']=='object_pose_changed_during_path';checks.append('object_moved')
for label,changes in [('nan_load',dict(observed_load_n=float('nan'))),('missing_load',dict(observed_load_n=None)),('invalid_q',dict(current=np.full(11,np.nan)))]:
 life=fresh_active();a=inp(rec['events'][1]['context']);a.update(changes)
 try:life.update(**a)
 except (TypeError,ValueError):checks.append(label)
 else:raise AssertionError(label)
# Original physical254 observation must still fail unchanged0.84m measured gate.
physical=json.loads((W/'front_recontact_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin/front_recontact_center.json').read_text());bad=physical['rows'][-1]['context'];life=fresh_active();a=inp(rec['events'][1]['context']);a['current']=np.asarray(bad['current']);a['observed_hand_pose']=guard.model.fk('left',a['current'])[0];a['observed_inactive_hand_pose']=guard.model.fk('right',a['current'])[0];out=life.update(**a);assert out['kind']=='stop' and out['proposal']['reason']=='measured_scene_rejected';checks.append('original_measured_height_gate')
for label,changes,enabled in [('disabled',{},False),('unselected',dict(selected=False),True),('initial_contact',dict(recontacts=0),True),('wait',dict(parent_mode='wait'),True),('guard_before_attempt',dict(guard_stop=True),True),('loaded_before_attempt',dict(observed_load_n=.01),True)]:
 life=FrontRecontactCenterLifecycle(enabled=enabled,recontact_index=rec['counter']);a=inp(ctx);a.update(changes)
 with patch('front_recontact_center_lifecycle.plan',side_effect=AssertionError('ineligible planner call')):out=life.update(**a)
 assert out['kind']=='unchanged' and not life.attempted and not life.active and life.ready==0;checks.append(label)
# Independent replay of first actual-shaped affine event rejects altered input,
# command and premature ready; these are not candidate self-checks.
for label in ['wrong_final','wrong_current','fake_counter','ready_without_observations']:
 e=copy.deepcopy(ev);c=copy.deepcopy(ctx);final=np.array(ev['command'])
 if label=='wrong_final':final[0]+=.001
 if label=='wrong_current':c['current'][0]+=.001
 if label=='fake_counter':e['context']['recontacts']+=1
 if label=='ready_without_observations':e['measured_ready_count']=3
 try:RecoveryEventAudit(ROOT,S).verify(e,step=c['step'],current=np.array(c['current']),previous_q=np.array(c['previous_q']),previous_command=np.array(c['previous_command']),final_command=final,scene=z,decay=np.array(c['decay']),selected=True,parent_mode=c['parent_mode'],recontacts=c['recontacts'],guard_stop=False,observed_load_n=c['observed_load_n'],filtered_load_n=c['filtered_load_n'])
 except (AssertionError,ValueError):checks.append(label)
 else:raise AssertionError(label)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__),D/'PROBE_RESULT.json',D/'PREPARATION.json',*D.glob('*.py')]},original_physical_failure_remains_rejected=True,simulation_started=False,collector_integrated=False,training_ready=False)
with (D/'GUARD_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,checks=len(checks))))
