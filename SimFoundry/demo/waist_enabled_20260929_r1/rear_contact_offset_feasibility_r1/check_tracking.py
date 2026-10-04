"""Six real recovery starts x original/offset plans x four hypothetical plants.
Caches independently checked same-observation plans and runs the ORIGINAL
tracking/handover lifecycle; this is not fresh planning or collector integration.
No historical future q is replayed after new commands. Fixed observed objects,
unloaded contact assumptions and surrogate plants do not establish dynamics.
Existing entry-lift ticks already spent at each real start count toward240.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
import minimum_motion_lifecycle as runtime
from offset_audit import PlanAudit
from audit_box_center_preference_events import EventAudit as OriginalEventAudit
class Audit(PlanAudit):verify=OriginalEventAudit.verify
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();data=json.loads((D/'RESULT.json').read_text());assert data['complete'] and len(data['rows'])==6
for f,h in data['source_sha256'].items():assert sha(f)==h,f
source_files={str(D/'RESULT.json'):sha(D/'RESULT.json')};records=[];out=D/'TRACKING_CHECK.json';assert not out.exists();guard=ClearanceGuard(ROOT,S)
def save(complete):
 for mod in list(sys.modules.values()):
  f=getattr(mod,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):source_files[str(p)]=sha(p)
 for p in [Path(__file__),S/'causal_response_parameters.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:source_files[str(p)]=sha(p)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=complete,expected_scenarios=48,completed_scenarios=len(records),handover_scenarios=sum(r['handover'] for r in records),rows=records,source_sha256=source_files,actual_physics=False,training_ready=False)
 temp=out.with_suffix('.tmp');temp.write_text(json.dumps(report,indent=2));temp.replace(out)
params=json.loads((S/'causal_response_parameters.json').read_text());decay=np.asarray(params['tasks']['push_box_to_bin']['decay'])
for case in data['rows']:
 ep=W/case['run']/'case_840023/layout_840023_push_box_to_bin';events=json.loads((ep/'recontact_pose.json').read_text())['rows'];event=next(e for e in events if e['step']==case['step']);ctx=event['context'];source_files[str(ep/'recontact_pose.json')]=sha(ep/'recontact_pose.json');q0=np.array(ctx['current']);qp0=np.array(ctx['previous_q']);prev0=np.array(ctx['previous_command']);scene=RecontactScene(guard,**ctx['scene']);bias=q0-prev0-decay*(qp0-prev0);spent=event['recovery_total_ticks']-1;assert 0<=spent<240
 for variant,plan,preferred in [('original',event['planning'],[0.,0.]),('offset',case['proposal'],case['preferred_xy_m'])]:
  assert plan['step']==case['step'] and plan['start']==q0.tolist() and plan['scene']==ctx['scene']
  def cached(s,q,**kw):
   assert s.record()==ctx['scene'] and np.array_equal(q,q0) and kw['step']==case['step']
   assert kw['prefer_interior'] and kw['minimum_motion_pose'] and kw['box_center_preference']
   return copy.deepcopy(plan)
  runtime.plan=cached
  for plant in ['calibrated','slower_decay','faster_decay','varying_bias']:
   state=runtime.RecontactLifecycle(enabled=True,prefer_interior=True,box_center_preference=True);audit=Audit(ROOT,S);audit.preferred_xy=np.array(preferred);q=q0.copy();qp=qp0.copy();previous=prev0.copy();trace=[];checks=[];negative=[];last_kind=None;last_reason=None;start_saved=False
   for k in range(241-spent):
    if spent+state.ticks>=240:last_kind='combined_budget_exhausted';last_reason='original_entry_plus_tracking240';break
    inputs=dict(ctx,step=case['step']+k,current=q,previous_q=qp,previous_command=previous,scene=scene,decay=decay)
    if k:
     inputs.update(observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0],observed_load_n=0.,filtered_load_n=0.)
    ev=state.update(**inputs);trace.append(ev);last_kind=ev['kind'];last_reason=ev.get('reason')
    if ev['kind'] not in ['command','handover']:break
    if not start_saved:
     start_saved=True
     for label,change in [('phase',dict(parent_mode='top_push')),('guard',dict(guard_stop=True)),('new_load',dict(observed_load_n=.001)),('recovery_count',dict(recontacts=ctx['recontacts']+1))]:
      bad=copy.deepcopy(state).update(**dict(inputs,**change));assert bad['kind']=='stop' and bad['requires_stop'];negative.append(label)
     expired=copy.deepcopy(state);expired.ticks=240;bad=expired.update(**inputs);assert bad['kind']=='stop' and bad['reason']=='recontact_path_budget_exhausted';negative.append('original240_budget')
    command=np.array(ev['command']);audit_inputs={k:inputs[k] for k in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']};check=audit.verify(ev,**audit_inputs,final_command=command,scene=scene.record());checks.append(check)
    if ev['kind']=='handover':break
    alpha=np.clip(decay+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0.),0,.95);b=bias+(np.sin(k*.12)*np.r_[.0001,np.full(10,.0003)] if plant=='varying_bias' else 0.);nextq=(1-alpha)*command+alpha*q+b;g,_=audit.geometry(nextq,scene.record())
    if not g['accepted']:
     last_kind='hypothetical_next_geometry_rejected';last_reason='independent_geometry';trace.append(dict(kind=last_kind,geometry=g));break
    qp=q;q=nextq;previous=command
   row=dict(run=case['run'],start_step=case['step'],variant=variant,plant=plant,entry_ticks_already_spent=spent,tracking_ticks=state.ticks,combined_ticks=spent+state.ticks,handover=last_kind=='handover',final_kind=last_kind,final_reason=last_reason,negative_guards=negative,independent_events=checks,trace=trace);assert row['combined_ticks']<=240;records.append(row);save(False);print(json.dumps({k:v for k,v in row.items() if k not in ['trace','independent_events']}),flush=True)
assert len(records)==48;save(True);print('COMPLETE48',sum(r['handover'] for r in records),flush=True)
