"""Actual first context plus explicitly hypothetical causal continuation.
No measured physical recovery is claimed. Negative lifecycle fixtures verify
commitment, measured-only admission, original geometry and shared budget.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_recontact_headroom';D=W/'inactive_hand_headroom_draft_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from inactive_clearance_lifecycle import InactiveClearanceLifecycle
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_initial_center_planning_v2 import SelectionAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ep=W/'front_recontact_headroom_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin'
source=json.loads((ep/'front_recontact_center.json').read_text())['rows'];guard=ClearanceGuard(ROOT,S);audit=SelectionAudit(ROOT,S)
with np.load(ep/'raw.npz') as z:rawq=z['q'][:,12:23];rawu=z['action'][:,12:23]
def context(step):
 c=copy.deepcopy(next(r for r in source if r['step']==step)['context']);s=c.pop('scene');c['scene']=RecontactScene(guard,s['side'],s['target_xyz'],s['target_quat'],s['core_size'],s['other_xyz'],s['other_quat'],s['other_size']);np.testing.assert_array_equal(c['current'],rawq[step]);np.testing.assert_array_equal(c['previous_command'],rawu[step-1]);return c
records=[];negatives=[]
for step in [405,528]:
 c=context(step);life=InactiveClearanceLifecycle(recontact_index=c['recontacts'],enabled=True);first=life.update(**c)
 assert first['kind']=='command' and first['phase']=='inactive_clearance_preparation' and life.active and life.preparing and not life.attempted and life.ticks==1
 for name in ['nominal','predicted']:
  for q,stored in zip(first['proposal']['sampled_paths'][name]['states'],first['proposal']['sampled_paths'][name]['checks']):
   independent,_=audit.geometry(q,c['scene'].record());audit.compare_geometry(stored,independent);assert independent['accepted']
 # Hypothetical continuation, never substitute this for another raw observation.
 future=dict(c,step=step+1,current=first['proposal']['predicted_q'],previous_q=c['current'],previous_command=first['command'])
 for side,key in [('left','observed_hand_pose'),('right','observed_inactive_hand_pose')]:future[key]=guard.model.fk(side,future['current'])[0]
 for label,changes in [('contact',dict(observed_load_n=.1)),('filter',dict(filtered_load_n=.051)),('guard',dict(guard_stop=True)),('unselected',dict(selected=False)),('phase',dict(parent_mode='top_push')),('counter',dict(recontacts=c['recontacts']+1)),('skipped_observation',dict(step=step+2))]:
  clone=copy.copy(life);event=clone.update(**dict(future,**changes));assert event['kind']=='stop' and clone.failure;again=clone.update(**future);assert again['kind']=='stop';negatives.append(dict(step=step,case=label,reason=event['reason']))
 clone=copy.copy(life);clone.ticks=240;event=clone.update(**future);assert event['kind']=='stop' and event['reason']=='initial_front_path_budget_exhausted';negatives.append(dict(step=step,case='shared_budget',reason=event['reason']))
 clone=copy.copy(life);bad=dict(future,observed_inactive_hand_pose=np.eye(4))
 try:clone.update(**bad)
 except ValueError:negatives.append(dict(step=step,case='pose_not_measured_from_q'))
 else:raise AssertionError('Malformed observed pose admitted')
 clone=copy.copy(life);below=context(754);below.update(step=step+1,recontacts=c['recontacts']);event=clone.update(**below);assert event['kind']=='stop';negatives.append(dict(step=step,case='future_bad_actual_geometry',reason=event['reason']))
 # The optimizer prediction is not used as observation inside lifecycle.
 clone=copy.copy(life);unchanged=dict(c,step=step+1);event=clone.update(**unchanged);assert clone.preparing and not clone.attempted and event['kind']=='command';negatives.append(dict(step=step,case='predicted_headroom_without_measured_change_does_not_start'))
 # Shared budget includes preparation and original recovery command.
 next_event=life.update(**future);assert next_event['kind']=='command' and next_event['measured_clearance_transition'] and next_event['preparation_ticks']==1 and life.ticks==2 and life.active and not life.preparing
 original=copy.deepcopy(next_event['planning']);trials=audit.verify_selection(original,scene=future['scene'].record(),current=future['current'],previous_q=future['previous_q'],previous_command=future['previous_command'],decay=future['decay'],step=future['step']);assert trials['passed']
 records.append(dict(actual_step=step,first_actual_context_command=first,hypothetical_next_event=next_event,independent_planning_trials=trials));print(step,'passed',flush=True)
for step in [405,754]:
 c=context(step);life=InactiveClearanceLifecycle(recontact_index=c['recontacts'],enabled=False);e=life.update(**c);assert e['kind']=='unchanged' and e['reason']=='disabled';negatives.append(dict(step=step,case='disabled'))
c=context(754);life=InactiveClearanceLifecycle(recontact_index=c['recontacts'],enabled=True);e=life.update(**c);assert e['kind']=='unchanged' and not life.active and not life.attempted;negatives.append(dict(step=754,case='original_bad_geometry_not_repaired'))
files=[Path(__file__),D/'inactive_clearance_lifecycle.py',D/'inactive_clearance_proposal.py',ep/'raw.npz',ep/'front_recontact_center.json',W/'audit_front_initial_center_planning_v2.py',*S.glob('*.py')]
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=records,negative_cases=negatives,passed=True,source_sha256={str(p):sha(p) for p in files},collector_integrated=False,physical_started=False,training_ready=False)
with (D/'LIFECYCLE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,actual_contexts=len(records),negative_cases=len(negatives),physical_started=False)))
