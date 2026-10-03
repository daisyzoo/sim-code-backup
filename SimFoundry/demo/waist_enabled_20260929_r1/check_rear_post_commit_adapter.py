"""Recorded-action/state-field fixtures for unwired post-commit adapter.
Each state fixture reconstructs only fields used by the adapter from a real
frame. They are NOT a continuous alternate rollout or complete state replay.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy
import numpy as np
w=Path(__file__).resolve().parent;root=w.parents[1];stage=w/'staged_front_corridor_midpoint_integrated';draft=w/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(draft),str(stage),str(root)]
from post_commit_adapter import apply_post_commit
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(root,stage);hp=draft/'HISTORICAL_POST_COMMIT_CHECK.json';history=json.loads(hp.read_text());assert history['passed'];sources={str(hp):sha(hp)}
for p,h in history['source_sha256'].items():assert sha(p)==h,p;sources[p]=h
results=[];sample=None
for hr in history['results']:
 ep=w/hr['run']/'case_840023/layout_840023_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());fs={x['step']:x for x in fr['rows']};coords={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};clear=json.loads((ep/'self_clearance.json').read_text());finals={x['step']:x for x in clear['rows'] if x['phase']=='final_command'};posts={x['step']:x for x in clear['rows'] if x['phase']=='post'}
 diag=json.loads((w/'front_corridor_midpoint_physical_r1/REAR_BOX_CURRENT_EDGE_COMMAND_RESIDUAL_DIAGNOSTIC.json').read_text());observations={x['step']:x for x in next(z for z in diag['results'] if z['run']==hr['run'])['records']};proposals={x['step']:x for x in hr['proposals']}
 with np.load(ep/'raw.npz') as z:actions=z['action'][:,12:23].astype(float)
 prov=json.loads((ep.parent/'provenance.json').read_text())
 for name in ['clearance_runtime.py','articulated_hand_geometry.py','self_clearance.py','elbow_torso_hulls.json']:
  archived=next(n for n in prov['source_sha256'] if n.endswith('/'+name));assert sha(stage/name)==prov['source_sha256'][archived];sources[str(stage/name)]=sha(stage/name)
 applied=[];reasons={};disabled=0
 for t,action in enumerate(actions):
  row=fs.get(t);mode=row['mode'] if row else 'initial';target=tuple(row['target_xyz']) if row else None
  state=RearCopRouteState(rear=SimpleNamespace(plan={'direction':-1}),side='right',size=(.14,.09,.045),mode=mode,top_mode=mode,command=target,last_waypoint_xy=target[:2] if target else None)
  contact=dict(valid=t in observations,normal_load_n=observations.get(t,{}).get('normal_load_n',0.))
  args=dict(step=t,side='right',rear_selected=fr['plan']['rear_cop_centering']['enabled'],state=state,row=row,coordinate=coords.get(t),action=action,final_guard=finals[t],post_guard=posts[t],execution_completed=True,slip_contact=contact,guard=guard)
  before=copy.deepcopy(state.__dict__);row_before=copy.deepcopy(row);coordinate_before=copy.deepcopy(coords.get(t));action_before=action.copy()
  assert apply_post_commit(**args) is None and state.__dict__==before;disabled+=1
  record=apply_post_commit(enabled=True,**args);reasons[record['reason']]=reasons.get(record['reason'],0)+1
  assert row==row_before and coords.get(t)==coordinate_before and np.array_equal(action,action_before)
  untouched_before={k:v for k,v in before.items() if k not in ['command','last_waypoint_xy']};untouched_after={k:v for k,v in state.__dict__.items() if k not in ['command','last_waypoint_xy']};assert untouched_before==untouched_after
  if record['applied']:
   expected={k:v for k,v in proposals[t].items() if k!='step'};assert record['suggestion']==expected;assert tuple(record['state_after']['command'])==state.command;applied.append(record)
   if sample is None:
    sample=dict(args);sample['state']=copy.deepcopy(state);sample['state'].__dict__.update(before)
  else:assert state.__dict__==before and t not in proposals
 assert len(applied)==hr['post_commit_y_proposals'];results.append(dict(run=hr['run'],state_field_fixtures=len(actions),disabled_unchanged=disabled,applied=len(applied),reasons=reasons,records=applied));print({k:v for k,v in results[-1].items() if k!='records'},flush=True)
 for name in ['raw.npz','frontal_bypass.json','coordination.json','self_clearance.json']:sources[str(ep/name)]=sha(ep/name)
assert sample is not None
negative=[]
def fresh():
 return {k:(v if k=='guard' else copy.deepcopy(v)) for k,v in sample.items()}
def invalid(label,modify):
 a=fresh();modify(a);before=copy.deepcopy(a['state'].__dict__)
 try:apply_post_commit(enabled=True,**a)
 except ValueError:assert a['state'].__dict__==before;negative.append(dict(case=label,rejected=True))
 else:raise AssertionError('invalid adapter context accepted: '+label)
invalid('stale_row',lambda a:a['row'].update(step=a['step']+1))
invalid('stale_coordinate',lambda a:a['coordinate'].update(step=a['step']+1))
invalid('stale_guard_step',lambda a:a['final_guard'].update(step=a['step']-1))
invalid('wrong_post_guard_phase',lambda a:a['post_guard'].update(phase='pre'))
invalid('wrong_guard_command',lambda a:a['final_guard']['command'].__setitem__(0,a['final_guard']['command'][0]+.001))
invalid('wrong_guard_current',lambda a:a['final_guard']['current'].__setitem__(0,a['final_guard']['current'][0]+.001))
invalid('wrong_route_cursor',lambda a:setattr(a['state'],'command',(0.,0.,0.)))
invalid('wrong_reference_offset',lambda a:a['row'].__setitem__('control_offset_local',[1.,1.,1.]))
invalid('wrong_action_shape',lambda a:a.__setitem__('action',np.zeros(10)))
invalid('nonfinite_contact_load',lambda a:a['slip_contact'].update(normal_load_n=float('nan')))
invalid('nonbool_execution_flag',lambda a:a.__setitem__('execution_completed',1))
for label,modify in [('execution_not_completed',lambda a:a.__setitem__('execution_completed',False)),('post_guard_rejected',lambda a:a['post_guard'].update(accepted=False)),('final_guard_rejected',lambda a:a['final_guard'].update(accepted=False)),('left_hand_unchanged',lambda a:a.__setitem__('side','left')),('not_rear_unchanged',lambda a:a.__setitem__('rear_selected',False)),('invalid_contact_preserved',lambda a:a['slip_contact'].update(valid=False))]:
 a=fresh();modify(a);before=copy.deepcopy(a['state'].__dict__);rr=apply_post_commit(enabled=True,**a);assert not rr['applied'] and before==a['state'].__dict__;negative.append(dict(case=label,reason=rr['reason']))
# Reapplying a successful state change against the old current row is rejected.
a=fresh();assert apply_post_commit(enabled=True,**a)['applied'];before=copy.deepcopy(a['state'].__dict__)
try:apply_post_commit(enabled=True,**a)
except ValueError:assert a['state'].__dict__==before;negative.append(dict(case='duplicate_commit',rejected=True))
else:raise AssertionError('duplicate commit accepted')
for p in [Path(__file__),draft/'post_commit_adapter.py',draft/'reconcile_rear_waypoint.py',stage/'rear_cop_route.py',stage/'region_top_contact.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,results=results,negative_checks=negative,source_sha256=sources,collector_connected=False,full_state_replay=False,new_physics=False,training_ready=False)
with (draft/'POST_COMMIT_ADAPTER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(passed=True,state_field_fixtures=sum(x['state_field_fixtures'] for x in results),applied=sum(x['applied'] for x in results),negative_checks=len(negative)),flush=True)
