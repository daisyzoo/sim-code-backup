"""Real parent state-class transitions on all recorded candidate outputs.
Does not execute physics or claim load release/endpoint arrival. The next physics
step must still be measured, independently audited and fully scene checked.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy,pickle
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_peak_load_guard';sys.path[:0]=[str(W),str(S),str(ROOT)]
from rear_cop_route import RearCopRouteState
from clearance_runtime import ClearanceGuard
from rear_corridor_recovery_state import commit_loaded,begin_lift
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S);loaded=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());lifts=json.loads((W/'REAR_CORRIDOR_UNLOAD_CHECK.json').read_text());assert loaded['status']==lifts['status']=='complete';requests=[(ep['episode'],r,False) for ep in loaded['episodes'] for r in ep['rows'] if r['result']['applied']]+[(r['episode'],r,True) for r in lifts['rows'] if r['result']['applied']];cache={};counts=dict(loaded=0,lift=0);negative=[];sources={}
for epname,test,lift in requests:
 ep=W/epname
 if epname not in cache:
  f=json.loads((ep/'frontal_bypass.json').read_text());c=json.loads((ep/'coordination.json').read_text());cache[epname]=(f['plan'],{x['step']:x for x in f['rows']},{x['step']:x for x in c})
  for n in ['frontal_bypass.json','coordination.json']:sources[str(ep/n)]=sha(ep/n)
 plan,fs,cs=cache[epname];t=test['step'];row=fs[t];coord=cs[t];state=RearCopRouteState(rear=SimpleNamespace(plan=plan),side=coord['active_side'],size=tuple([.14,.09,.045] if coord['active_side']=='right' else [.15,.145,.04]),hold_established_x=True)
 state.top_mode=state.mode='top_push';state.command=tuple(row['target_xyz']);state.last_waypoint_xy=tuple(row['target_xyz'][:2]);state.push_x_anchor=row.get('push_x_anchor_m');state.recontacts=row['recontacts'];state.load.bias_m=row['contact_load']['stored_z_bias_m'];state.load.filtered_n=row['contact_load']['filtered_vertical_load_n'];state.rear_cop.anchor_local=np.array([.001,.002,.003]);state.rear_cop.last_anchor_world=np.array([.4,.1,.8]);before=copy.deepcopy(state)
 result=test['result'];cmd=next(a['command'] for a in result['attempts'] if a['accepted']);args=dict(state=state,guard=guard,row=row,coordinate=coord,current=coord['upper_q'],previous=coord['task_inputs']['previous'],command=cmd,result=result);fn=begin_lift if lift else commit_loaded;event=fn(**args)
 assert state.rear_corridor_last_commit_step==t
 if lift:
  assert state.recontacts==before.recontacts+1 and state.load.bias_m==0 and state.load.filtered_n==before.load.filtered_n and state.top_mode==state.mode=='top_lift' and state.command is None and state.rear_cop.anchor_local is None and state.rear_corridor_recontact_pending
  counts['lift']+=1
 else:
  assert state.command==state.last_waypoint_xy+(state.command[2],) and state.push_x_anchor==state.command[0]
  assert state.load.bias_m==before.load.bias_m and state.load.filtered_n==before.load.filtered_n and state.recontacts==before.recontacts and state.top_mode==state.mode=='top_push';counts['loaded']+=1
 if ('repeat_lift' if lift else 'repeat_loaded') not in negative:
  try:fn(**args)
  except ValueError:negative.append('repeat_'+('lift' if lift else 'loaded'))
  else:raise AssertionError('Repeated commit accepted')
  for name,change in [('command_mismatch',dict(command=np.array(cmd)+.001)),('invalid_result',dict(result=dict(result,applied=False)))]:
   fresh=copy.deepcopy(before)
   try:fn(**dict(args,state=fresh,**change))
   except ValueError:assert pickle.dumps(fresh)==pickle.dumps(before);negative.append(name+('_lift' if lift else '_loaded'))
   else:raise AssertionError(name+' accepted')
for p in [Path(__file__),W/'rear_corridor_recovery_state.py',W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json',W/'REAR_CORRIDOR_UNLOAD_CHECK.json',S/'rear_cop_route.py',S/'region_top_contact.py',S/'rear_cop_centering.py',S/'clearance_runtime.py']:sources[str(p)]=sha(p)
assert counts==dict(loaded=1693,lift=250)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,counts=counts,negative_checks=negative,source_sha256=sources,training_ready=False)
with (W/'REAR_CORRIDOR_STATE_COMMIT_V2_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
