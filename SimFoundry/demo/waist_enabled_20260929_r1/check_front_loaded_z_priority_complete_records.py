"""Full10 old-observation decision audit with explicit unissued single steps.
Native replay metadata is synthetic; every q and prior u remains original.
All9740 original final guards are separately checked against original raw u.
Applied proposals must fail when falsely paired with those original raw actions.
This is not a new trajectory, physics test, source-fixture or admission result.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from front_loaded_z_priority_episode_inputs import EpisodeInputs
from audit_front_loaded_z_priority_record import verify_record
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=W/'FRONT_LOADED_Z_PRIORITY_NATIVE_FULL10_REPLAY.json';replay=json.loads(P.read_text());sources={str(P):sha(P)}
for p,h in replay['source_sha256'].items():assert sha(p)==h,p
results=[];negative=[];old_action_rejections=0
for case in replay['episodes']:
 ep=next((W/'front_initial_physical_r1').glob('case_*/'+case['episode']));inputs=EpisodeInputs(ep);rows=case['rows'];assert [r['step'] for r in rows]==list(range(inputs.n));records=[];seen=set()
 for r in rows:
  t=r['step'];m=r['metadata'];args=inputs.arguments(t,m,unissued_output=np.asarray(m['output_command']));record=verify_record(**args);records.append(record);inputs.verify_actual_final_guard(t)
  if m['applied']:
   try:verify_record(**inputs.arguments(t,m))
   except AssertionError:old_action_rejections+=1
   else:raise AssertionError(('old actual action accepted as candidate',ep.name,t))
  if m['reason'] not in seen:
   seen.add(m['reason']);bad=dict(args);bad['metadata']=copy.deepcopy(m);bad['metadata']['reason']='forged_reason'
   mutations={'wrong_branch_reason':bad}
   bad=dict(args);bad['previous_actual']=np.asarray(args['previous_actual']).copy();bad['previous_actual'][0]=np.float32(bad['previous_actual'][0]+.001);mutations['wrong_actual_previous']=bad
   bad=dict(args);bad['selected']=not args['selected'];mutations['wrong_selection']=bad
   bad=dict(args);bad['metadata']=copy.deepcopy(m);bad['metadata']['output_command'][0]+=.001;mutations['changed_logged_output']=bad
   for name,bad in mutations.items():
    try:verify_record(**bad)
    except (AssertionError,ValueError,KeyError):negative.append(dict(episode=ep.name,step=t,branch=m['reason'],mutation=name,rejected=True))
    else:raise AssertionError(('negative accepted',ep.name,t,name))
  if t%400==0:print(ep.name,t,inputs.n,flush=True)
 reasons={s:sum(r['reason']==s for r in records) for s in sorted(seen)};results.append(dict(episode=ep.name,frames=inputs.n,wait=inputs.wait,applied=sum(r['applied'] for r in records),reason_counts=reasons,original_actual_final_guards=inputs.n,records=records));sources.update(inputs.sources)
assert old_action_rejections==658 and sum(e['frames'] for e in results)==9740
for name in ['check_front_loaded_z_priority_complete_records.py','front_loaded_z_priority_episode_inputs.py','audit_front_loaded_z_priority_record.py','audit_front_loaded_z_priority_applied_row.py','audit_front_loaded_z_priority_parent.py','front_loaded_z_priority_audit_geometry.py','support_vertex_stationarity.py','audit_unloaded_wrist_prior_live.py','audit_self_clearance_task_optimality.py','screen_bag_vertical_priority_geometry.py']:sources[str(W/name)]=sha(W/name)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=results,negative_cases=negative,old_actual_action_rejections=old_action_rejections,source_sha256=sources,physical_started=False,new_episode_audit_ready=False,training_ready=False)
p=W/'FRONT_LOADED_Z_PRIORITY_COMPLETE_RECORD_CHECK.json'
with p.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,frames=9740,original_actual_guards=9740,old_actual_action_rejections=old_action_rejections,negative_cases=len(negative),conditions=[{k:v for k,v in e.items() if k!='records'} for e in results]),indent=2))
