"""Fresh six-context planning/lifecycle and independently bound policy checks.
All historical observations are independent inputs. Only first unissued command
is checked; no actual future is attached to a changed command.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';O=W/'rear_contact_offset_feasibility_r1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from trailing_recontact_plan import plan
from trailing_minimum_motion_lifecycle import RecontactLifecycle
from trailing_entry_lift_lifecycle import RecontactLifecycle as CombinedLifecycle
from trailing_contact_audit import PlanAudit
from audit_box_center_preference_events import EventAudit as OriginalEventAudit
class EventAudit(PlanAudit):verify=OriginalEventAudit.verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[];out=D/'CHECK.json';assert not out.exists();guard=ClearanceGuard(ROOT,S)
def read(p):sources[str(p)]=sha(p);return json.loads(Path(p).read_text())
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):return dict(case=label,rejected=True)
 raise AssertionError('Mutation accepted: '+label)
reference=read(O/'RESULT.json');assert reference['complete'] and len(reference['rows'])==6
for p,h in reference['source_sha256'].items():assert sha(p)==h,p
frozen=read(D/'PLAN.json')
for n,h in frozen['candidate_sha256'].items():assert sha(D/n)==h,n
params=read(S/'causal_response_parameters.json');decay=params['tasks']['push_box_to_bin']['decay'];cache={}
def save(complete):
 for mod in list(sys.modules.values()):
  file=getattr(mod,'__file__',None)
  if file:
   p=Path(file).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 for p in [Path(__file__),S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,rows=rows,source_sha256=sources,collector_integrated=False,physical_execution=False,training_ready=False)
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(report,indent=2));tmp.replace(out)
for ref in reference['rows']:
 ep=W/ref['run']/'case_840023/layout_840023_push_box_to_bin'
 if ep not in cache:
  events=read(ep/'recontact_pose.json')['rows'];first=next(e for e in events if (e.get('planning') or {}).get('box_center_preference_pose'))
  with np.load(ep/'raw.npz',allow_pickle=False) as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
  sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');cache[ep]=(events,first,q,u)
 events,first,q,u=cache[ep];t=ref['step'];ev=next(e for e in events if e['step']==t);ctx=ev['context'];scene=RecontactScene(guard,**ctx['scene']);earliest=(first['step'],np.array(first['context']['current']))
 np.testing.assert_array_equal(ctx['current'],q[t]);np.testing.assert_array_equal(ctx['previous_q'],q[t-1]);np.testing.assert_array_equal(ctx['previous_command'],u[t-1])
 original=plan(scene,q[t],step=t,earlier_seed=earliest,prefer_interior=True,minimum_motion_pose=True,box_center_preference=True)
 assert original==ev['planning'],'Disabled fresh planner must exactly reproduce actual plan'
 PlanAudit(ROOT,S,enabled=False).verify_preference(original,current=q[t],scene=scene.record(),step=t)
 runtime=RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True,box_trailing_preference=True);runtime.earliest_seed=earliest
 inputs=dict(ctx,scene=scene,decay=decay);event=runtime.update(**inputs);assert event['kind']=='command' and event['planning'] is not None
 created=event['planning'];assert {k:v for k,v in created.items() if k!='rear_box_trailing_preference'}==ref['proposal'],'Fresh whole planner must reproduce offset probe including original parent'
 auditor=EventAudit(ROOT,S,enabled=True);kw={k:inputs[k] for k in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']};audit=auditor.verify(event,**kw,final_command=event['command'],scene=scene.record())
 negative=[]
 for label in ['missing_policy','offset','direction','inset','preferred','step','quaternion','objective']:
  bad=copy.deepcopy(created);m=bad['rear_box_trailing_preference']
  if label=='missing_policy':bad.pop('rear_box_trailing_preference')
  elif label=='offset':m['offset_m']=.010
  elif label=='direction':m['world_direction']=[0.,-1.,0.]
  elif label=='inset':m['original_inset_m']=.012
  elif label=='preferred':m['preferred_local_xy_m'][0]+=.001
  elif label=='step':m['step']+=1
  elif label=='quaternion':m['observed_target_quat'][0]+=.001
  else:bad['box_center_preference_pose']['endpoint_attempts'][0]['objective']+=1
  negative.append(reject(label,lambda:PlanAudit(ROOT,S,enabled=True).verify_preference(bad,current=q[t],scene=scene.record(),step=t)))
 negative.append(reject('changed_plan_in_disabled_auditor',lambda:PlanAudit(ROOT,S,enabled=False).verify_preference(created,current=q[t],scene=scene.record(),step=t)))
 for label,change in [('guard',dict(guard_stop=True)),('phase',dict(parent_mode='top_push')),('load',dict(observed_load_n=.001)),('count',dict(recontacts=ctx['recontacts']+1))]:
  stopped=copy.deepcopy(runtime).update(**dict(inputs,**change));assert stopped['kind']=='stop' and stopped['requires_stop'];negative.append(dict(case=label,rejected=True))
 combined=CombinedLifecycle(enabled=True,prefer_interior=True,box_center_preference=True,entry_lift=True,box_trailing_preference=True);combined.original=copy.deepcopy(runtime);combined.total_ticks=240;stopped=combined.update(**inputs);assert stopped['kind']=='stop' and stopped['reason']=='combined_recovery_budget_exhausted';negative.append(dict(case='combined240_budget',rejected=True))
 row=dict(run=ref['run'],step=t,disabled_original_plan_exact=True,fresh_offset_plan_exact=True,first_unissued_lifecycle_event_verified=True,preferred_xy_m=created['rear_box_trailing_preference']['preferred_local_xy_m'],negative=negative,event=event,audit=audit);rows.append(row);save(False);print(json.dumps({k:v for k,v in row.items() if k not in ['event','audit','negative']}),flush=True)
assert len(rows)==6 and sum(len(r['negative']) for r in rows)==84;save(True);print('COMPLETE6_FRESH_LIFECYCLE84_NEGATIVE',flush=True)
