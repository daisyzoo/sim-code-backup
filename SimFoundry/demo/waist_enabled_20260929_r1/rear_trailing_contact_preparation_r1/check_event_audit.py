"""Independent first-action checks plus unchanged actual lift-only segments.
Changed candidate actions have no attached historical future. No physics proof.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';T=W/'rear_trailing_contact_candidate_r1';sys.path[:0]=[str(D),str(T),str(S),str(W),str(ROOT)]
from trailing_event_audit import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={}
def read(p):sources[str(p)]=sha(p);return json.loads(Path(p).read_text())
proof=read(D/'NATIVE_PREFIX_CHECK.json');assert proof['complete']
for p,h in proof['source_sha256'].items():assert sha(p)==h,p
params=read(S/'causal_response_parameters.json');decay=params['tasks']['push_box_to_bin']['decay'];rows=[];negative=[]
def inputs(event,command=None):
 c=event['context'];return dict(**{k:c[k] for k in ['step','current','previous_q','previous_command','scene','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']},decay=decay,final_command=event['command'] if command is None else command)
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError):negative.append(label)
 else:raise AssertionError('Bad event accepted '+label)
for r in proof['rows']:
 ev=r['first_changed']['event'];kw=inputs(ev);a=EventAudit(ROOT,S,enabled=True);result=a.verify(ev,**kw);assert result['recovery_total_ticks']==1
 for label in ['budget_count','over_budget','missing_policy','offset','command','previous_q','load','guard','step','disabled_policy']:
  bad=copy.deepcopy(ev);arg=copy.deepcopy(kw);auditor=EventAudit(ROOT,S,enabled=label!='disabled_policy')
  if label=='budget_count':bad['recovery_total_ticks']+=1
  elif label=='over_budget':auditor.recontacts=kw['recontacts'];auditor.total=240
  elif label=='missing_policy':bad['planning'].pop('rear_box_trailing_preference')
  elif label=='offset':bad['planning']['rear_box_trailing_preference']['offset_m']=.01
  elif label=='command':arg['final_command'][0]+=.001
  elif label=='previous_q':arg['previous_q'][0]+=.001
  elif label=='load':arg['observed_load_n']=.1
  elif label=='guard':arg['guard_stop']=True
  elif label=='step':arg['step']+=1
  reject(r['run']+':'+label,lambda:auditor.verify(bad,**arg))
 ep=W/r['run']/'case_840023/layout_840023_push_box_to_bin';history=read(ep/'recontact_pose.json')['rows'];sources[str(ep/'raw.npz')]=sha(ep/'raw.npz')
 with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 first=next(i for i,e in enumerate(history) if e.get('entry_lift_phase'));lift=[];a=EventAudit(ROOT,S,enabled=True)
 for e in history[first:]:
  if not e.get('entry_lift_phase'):break
  step=e['step'];ctx=e['context'];np.testing.assert_array_equal(q[step],ctx['current']);np.testing.assert_array_equal(q[step-1],ctx['previous_q']);np.testing.assert_array_equal(u[step-1],ctx['previous_command']);np.testing.assert_array_equal(u[step],e['command'])
  lift.append(a.verify(e,**inputs(e,command=u[step])))
  if e['entry_lift_phase']=='lift_ready':break
 assert lift and lift[-1]['entry_lift_phase']=='lift_ready' and a.awaiting_original
 # Candidate plan is required after lift: old center evidence cannot pass under changed policy.
 oldnext=history[first+len(lift)];assert oldnext['planning'] and oldnext['kind']=='command'
 reject(r['run']+':old_center_after_lift',lambda:a.verify(oldnext,**inputs(oldnext)))
 rows.append(dict(run=r['run'],new_first_event=result,unchanged_real_lift_events=len(lift),last_lift_step=lift[-1]['step'],old_following_center_plan_rejected=True));print(json.dumps(rows[-1]),flush=True)
# Left-side minimum-motion planner retains its old audit, not right-box preference.
left_ep=W/'joint_transport_physical_r1/case_840020/layout_840020_nudge_mailer_to_bin/recontact_pose.json'
# The current run's second group may still be collecting; use the closed direct parent instead.
left_ep=W/'front_box_recenter_physical_r2/case_840020/layout_840020_nudge_mailer_to_bin/recontact_pose.json'
left_events=read(left_ep)['rows'];left=next(e for e in left_events if e['kind']=='command' and e.get('planning') and not e.get('entry_lift_phase'))
left_decay=params['tasks']['nudge_mailer_to_bin']['decay'];left_kw=inputs(left);left_kw['decay']=left_decay
left_result=EventAudit(ROOT,S,enabled=True).verify(left,**left_kw)
bad=copy.deepcopy(left);bad['planning']['rear_box_trailing_preference']={};reject('left_box_preference_injection',lambda:EventAudit(ROOT,S,enabled=True).verify(bad,**left_kw))
for mod in list(sys.modules.values()):
 file=getattr(mod,'__file__',None)
 if file:
  p=Path(file).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',S/'elbow_torso_hulls.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,left_original_event=left_result,negative=negative,source_sha256=sources,physical_execution=False,training_ready=False)
with (D/'EVENT_AUDIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,new_events=len(rows),lift_events=sum(r['unchanged_real_lift_events'] for r in rows),left_original_event=True,negative=len(negative))),flush=True)
