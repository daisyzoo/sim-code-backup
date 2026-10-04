"""Three actual front-box recovery starts x1reserve plan x4hypothetical plants.
Original240-command budget, explicit20mm landing target and independent URDF
geometry at every step. Cached plans, fixed object poses and synthetic unloaded
responses do not prove real contact, collision-free dynamic paths or success.
"""
from pathlib import Path
import sys,json,hashlib,datetime,copy
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from offset_lifecycle import FrontRecontactCenterLifecycle
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();data=json.loads((D/'RESULT.json').read_text());assert data['completed']
for p,h in data['source_sha256'].items():assert sha(p)==h,p
parent_check=W/'front_box_trailing_landing_probe_r1/TRACKING_CHECK.json';parent=json.loads(parent_check.read_text());assert parent['complete'] and parent['scenarios']==24
for p,h in parent['source_sha256'].items():assert sha(p)==h,p
sources={str(D/'RESULT.json'):sha(D/'RESULT.json'),str(parent_check):sha(parent_check)};guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);records=[]
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';events={e['step']:e for e in json.loads((ep/'front_recontact_center.json').read_text())['rows']}
for case in data['contexts']:
 row=events[case['step']];ctx=row['context'];z=ctx['scene'];scene=RecontactScene(guard,**z);q0,qp0,u0,a=[np.asarray(ctx[k]) for k in ['current','previous_q','previous_command','decay']];bias0=q0-u0-a*(qp0-u0)
 for variant,plan,offset in [('offset_reserve_05mm',case['planning'],np.asarray(case['offset_local_xy']))]:
  assert plan['accepted'] and plan['scene']==scene.record() and np.array_equal(plan['start'],q0)
  for plant in ['calibrated','slower_decay','faster_decay','varying_bias']:
   state=FrontRecontactCenterLifecycle(enabled=True,recontact_index=row['real_recontact_index'],offset_local_xy=offset);state.active=state.attempted=True;state.plan=copy.deepcopy(plan);state.scene=scene;q=q0.copy();qp=qp0.copy();prev=u0.copy();trace=[];negative=[];ready=0;kind=reason=None
   for k in range(241):
    inputs=dict(step=case['step']+k,selected=True,parent_mode='top_cross',recontacts=row['real_recontact_index'],guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q,previous_q=qp,previous_command=prev,decay=a,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0])
    event=state.update(**inputs);kind=event['kind'];reason=event.get('reason')
    if kind not in ['command','handover']:trace.append(dict(step=inputs['step'],kind=kind,reason=reason));break
    cmd=np.asarray(event['command']);proof=event['proposal'];waypoint=np.asarray(proof['waypoint']);bias=q-prev-a*(qp-prev);request=(waypoint-a*q-bias)/(1-a);lo=np.maximum.reduce([audit.lo,q-audit.limits,prev-.055]);hi=np.minimum.reduce([audit.hi,q+audit.limits,prev+.055]);expected=np.clip(request,lo,hi).astype(np.float32);np.testing.assert_array_equal(expected,cmd);pred=(1-a)*cmd+a*q+bias;np.testing.assert_allclose(pred,proof['predicted_q'],atol=1e-12,rtol=0)
    checked=[]
    for label,v in [('measured',q),('command',cmd),('predicted',pred)]:
     g,_=audit.geometry(v,z);assert g['accepted'],(case['step'],variant,plant,k,label,g)
     if label!='measured':assert g['inactive_lowest_z_m']>=.8405
     checked.append(dict(label=label,geometry=g))
    g,details=audit.geometry(q,z);point=details['point'];axis=np.asarray(plan['thin_axis_local']);alignment=abs(details['rotation'][:,2]@details['pose'][:3,:3]@axis);isready=bool(max(abs(q-np.asarray(plan['endpoint'])))<=.003 and max(abs(point[:2]-offset))<=.002+2e-7 and min(details['core'][:2]/2-abs(point[:2]))>=.01 and .004<=g['active_above_top_m']<=.01 and alignment>=.8-2e-7 and np.all(q>=audit.lo-2e-7) and np.all(q<=audit.hi+2e-7));ready=ready+1 if isready else 0
    assert event['measured_ready_count']==ready and (kind=='handover')==(ready>=3)
    if k==0:
     for label,change in [('phase',dict(parent_mode='top_push')),('guard',dict(guard_stop=True)),('load',dict(observed_load_n=.001)),('recovery_changed',dict(recontacts=row['real_recontact_index']+1))]:
      bad=copy.deepcopy(state).update(**dict(inputs,**change));assert bad['kind']=='stop';negative.append(label)
     expired=copy.deepcopy(state);expired.ticks=240;bad=expired.update(**dict(inputs,step=inputs["step"]+1));assert bad['kind']=='stop' and bad['reason']=='initial_front_path_budget_exhausted';negative.append('240_budget')
    trace.append(dict(step=inputs['step'],kind=kind,ticks=state.ticks,waypoint_index=state.index,ready=ready,command=cmd.tolist(),point_local=point.tolist(),independent_checks=checked))
    if kind=='handover':break
    alpha=np.clip(a+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0.),0,.95);biasplant=bias0+(np.sin(k*.12)*np.r_[.0001,np.full(10,.0003)] if plant=='varying_bias' else 0.);nextq=(1-alpha)*cmd+alpha*q+biasplant;g,_=audit.geometry(nextq,z)
    if not g['accepted']:kind='hypothetical_next_geometry_rejected';reason='independent_geometry';trace.append(dict(kind=kind,geometry=g));break
    qp,q,prev=q,nextq,cmd
   result=dict(start_step=case['step'],recontact_index=row['real_recontact_index'],variant=variant,plant=plant,tracking_ticks=state.ticks,handover=kind=='handover',final_kind=kind,reason=reason,negative_guards=negative,trace=trace);assert state.ticks<=240;records.append(result)
   (D/'TRACKING_LIVE_PROGRESS.json').write_text(json.dumps(dict(completed_scenarios=len(records),expected=12,rows=records,training_ready=False),indent=2));print(json.dumps({k:v for k,v in result.items() if k!='trace'}),flush=True)
assert len(records)==12
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),D/'PREPARATION.json',ep/'front_recontact_center.json',S/'causal_response_parameters.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=True,scenarios=12,handover_scenarios=sum(r['handover'] for r in records),rows=records,source_sha256=sources,physical_started=False,collector_integrated=False,training_ready=False)
with (D/'TRACKING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print('COMPLETE12',report['handover_scenarios'],flush=True)
