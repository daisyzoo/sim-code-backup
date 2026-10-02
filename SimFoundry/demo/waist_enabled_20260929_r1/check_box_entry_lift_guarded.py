"""Replay all13 completed synthetic lifecycles through added boundary guards.
Reuse already validated causal planner result ONLY for exactly identical
scene/current/step/earlier seed and unchanged planner sources. Commands are
recomputed by candidate. Independent event audit covers both phases.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_box_center_preference';sys.path[:0]=[str(stage),str(w),str(repo)]
from box_entry_lift_recontact_guarded import RecontactLifecycle
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_box_entry_lift_events import EventAudit,LiftAudit
import minimum_motion_lifecycle as original_module
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source=w/'BOX_ENTRY_LIFT_COMBINED_CHECK.json';baseline=json.loads(source.read_text());assert baseline['complete'] and baseline['all_completed_within_budget'] and len(baseline['rows'])==13
for p,h in baseline['source_sha256'].items():assert sha(p)==h,p
out=w/'BOX_ENTRY_LIFT_GUARDED_CHECK.json';assert not out.exists();guard=ClearanceGuard(repo,stage);results=[];sources={str(source):sha(source)}
def save(complete):
 for p in [Path(__file__),w/'box_entry_lift_recontact_guarded.py',w/'box_recovery_entry_lift.py',w/'audit_box_entry_lift_events.py',w/'audit_box_center_events.py',w/'audit_box_center_plan.py',w/'audit_box_center_preference_plan.py',w/'audit_slow_drag_plan.py',w/'audit_recontact_pose_events.py',*stage.glob('*.py'),stage/'elbow_torso_hulls.json']:sources[str(p)]=sha(p)
 out.write_text(json.dumps(dict(scope=__doc__,complete=complete,passed=bool(complete and len(results)==13 and all(r['commands_exact'] and len(r['boundary_negative_cases'])==9 for r in results)),rows=results,source_sha256=sources,physical_validation=False,training_ready=False),indent=2))
for row in baseline['rows']:
 ep=w/row['run']/'case_840001/layout_840001_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];first=next(e for e in events if e.get('planning'));seed=(first['step'],np.array(first['context']['current']));state=RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True,entry_lift=True);state.earliest_seed=seed;auditor=EventAudit(repo,stage);planned={e['context']['step']:e['planning'] for e in row['trace'] if e.get('planning') is not None and 'entry_lift_phase' not in e};real_plan=original_module.plan;negative=[]
 def cached(scene,q,*,step,earlier_seed,prefer_interior,minimum_motion_pose,box_center_preference):
  assert prefer_interior is minimum_motion_pose is box_center_preference is True;assert earlier_seed[0]==seed[0] and np.array_equal(earlier_seed[1],seed[1]);p=planned[step];assert p['step']==step and p['scene']==scene.record() and np.array_equal(p['start'],q);return copy.deepcopy(p)
 original_module.plan=cached
 try:
  for i,expected in enumerate(row['trace']):
   ctx=expected['context'];scene=RecontactScene(guard,**ctx['scene']);inputs=dict(ctx,scene=scene,decay=expected['proposal']['decay']);event=state.update(**inputs);assert event==expected
   auditor.verify(event,step=ctx['step'],current=ctx['current'],previous_q=ctx['previous_q'],previous_command=ctx['previous_command'],final_command=event['command'],scene=ctx['scene'],decay=expected['proposal']['decay'],selected=ctx['selected'],parent_mode=ctx['parent_mode'],recontacts=ctx['recontacts'],guard_stop=ctx['guard_stop'],observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n'])
   if event.get('entry_lift_phase')=='lift_ready':
    assert state.pending and state.active;next_event=row['trace'][i+1];nc=next_event['context'];ns=RecontactScene(guard,**nc['scene']);ni=dict(nc,scene=ns,decay=next_event['proposal']['decay'])
    for label,change in [('parent_phase',dict(parent_mode='top_push')),('guard',dict(guard_stop=True)),('contact',dict(observed_load_n=.001)),('filtered_contact',dict(filtered_load_n=.051)),('recontact_count',dict(recontacts=nc['recontacts']+1)),('history',dict(step=nc['step']+2))]:
     rejected=copy.deepcopy(state).update(**dict(ni,**change));assert rejected['kind']=='stop' and rejected['reason']=='entry_lift_to_recontact_context_changed';negative.append(label)
    moved=RecontactScene(guard,**dict(nc['scene'],target_xyz=(np.array(nc['scene']['target_xyz'])+[.003,0,0]).tolist()));rejected=copy.deepcopy(state).update(**dict(ni,scene=moved));assert rejected['kind']=='stop';negative.append('object_moved')
    rejected_state=copy.deepcopy(state);rejected_state.original.update=lambda **kw:dict(kind='unchanged',reason='no_verified_endpoint');rejected=rejected_state.update(**ni);assert rejected['kind']=='stop' and rejected['reason']=='no_verified_recontact_after_entry_lift';negative.append('original_planning_rejected')
    rejected_state=copy.deepcopy(state);rejected_state.total_ticks=240;rejected=rejected_state.update(**ni);assert rejected['kind']=='stop' and not rejected_state.active;negative.append('shared_budget')
  assert not state.active and not auditor.active and state.failure is None
 finally:original_module.plan=real_plan
 results.append(dict(run=row['run'],start_step=row['start_step'],total_ticks=state.total_ticks,commands_exact=True,independent_combined_events=len(row['trace']),boundary_negative_cases=negative));save(False);print(results[-1],flush=True)
save(True);print('COMPLETE13 independent+9boundaries each',flush=True)
