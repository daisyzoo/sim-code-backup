"""Fresh runtime planning at three real starts, then four hypothetical plants each.
No externally cached plan, no historical future reuse. Fixed objects and an
adapter state stand-in: this is runtime integration evidence, not collector
integration, physical task success or training admission.
"""
from pathlib import Path
from types import SimpleNamespace
import copy,datetime,hashlib,json,sys
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from trailing_runtime import FrontRecontactCenterRuntime as Runtime
from front_box_recenter_runtime import FrontRecontactCenterRuntime as Original
from trailing_adapter import apply as adapter
from trailing_selection import select_planned
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=json.loads((D/'PREPARATION.json').read_text())
for x in prep['derivations']:
 for k in ['parent','candidate']:assert sha(x[k])==x[k+'_sha256'],x[k]
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';events=json.loads((ep/'front_recontact_center.json').read_text())['rows'];starts=[r for r in events if r.get('planning')];starts=[starts[i] for i in [0,6,12]]
coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);records=[];default_checks=[]
class Reset:
 def __init__(self):self.count=0
 def reset(self):self.count+=1

def state_for(z,counter):
 return SimpleNamespace(recontacts=counter,size=np.asarray(z['core_size']),load=SimpleNamespace(bias_m=9.),cross_axis_control=Reset(),cop_slip=Reset(),last_emitted_xy=(9.,9.))
def canon(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,dict):return {k:canon(x) for k,x in v.items()}
 if isinstance(v,(tuple,list)):return [canon(x) for x in v]
 if isinstance(v,SimpleNamespace):return canon(vars(v))
 if isinstance(v,Reset):return v.count
 return v
for start in starts:
 ctx=start['context'];z=ctx['scene'];scene=RecontactScene(guard,**z);q0,qp0,u0,a=[np.asarray(ctx[k]) for k in ['current','previous_q','previous_command','decay']];bias0=q0-u0-a*(qp0-u0);counter=start['real_recontact_index'];offset=(scene.rotation.T@np.array([0.,.020,0.]))[:2]
 reference0={k:np.asarray(v) for k,v in coord[start['step']-1]['active_support_reference'].items()}
 row0=dict(mode=ctx['parent_mode'],recontacts=counter,contact_load=dict(filtered_vertical_load_n=ctx['filtered_load_n'],applied_z_bias_m=0.,stored_z_bias_m=0.))
 def inputs(q,qp,prev,k):
  return dict(selected=True,step=start['step']+k,current=q,previous_q=qp,previous_command=prev,target_xyz=z['target_xyz'],target_quat=z['target_quat'],other_xyz=z['other_xyz'],other_quat=z['other_quat'],observed_load_n=0.,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0],normal_anchor=start['old_normal_anchor'],inactive_anchor=start['old_inactive_anchor'])
 def new(cls,**kw):
  obj=cls(guard,'right',z['core_size'],z['other_size'],a,enabled=True,**kw);obj.last_counter=counter-1;return obj
 # The default branch must preserve the full original event/state/reference.
 old,off=new(Original),new(Runtime);so,sf=state_for(z,counter),state_for(z,counter)
 ro=old.update(copy.deepcopy(row0),so,copy.deepcopy(reference0),**inputs(q0,qp0,u0,0));rf=off.update(copy.deepcopy(row0),sf,copy.deepcopy(reference0),**inputs(q0,qp0,u0,0));assert canon(ro)==canon(rf);assert canon(so)==canon(sf);default_checks.append(start['step'])
 rt=new(Runtime,trailing_landing=True);st=state_for(z,counter);assert rt.lifecycle is None
 first=rt.update(copy.deepcopy(row0),st,copy.deepcopy(reference0),**inputs(q0,qp0,u0,0));planning=first[2]['planning'];assert planning['accepted'] and planning['planning_xy_reserve_m']==.0005;assert np.array_equal(planning['landing_preference_local_xy'],offset);assert planning['transport_preflight']['predicted_capture_discarded'];assert first[2]['kind']=='command' and rt.center_local is None and rt.lifecycle.ready==0;assert 'captured_center_local' not in first[2]
 # A mismatched preference cannot slip through private plan selection.
 negatives=[]
 for label,changes in [('reserve',{'planning_xy_reserve_m':0.}),('offset',{'landing_preference_local_xy':[0.,0.]})]:
  bad=copy.deepcopy(planning);bad.update(changes)
  try:select_planned(bad,scene,q0,step=start['step'],previous_q=qp0,previous_command=u0,decay=a,recontact_index=counter)
  except ValueError:negatives.append(label)
  else:raise AssertionError('Forged selection accepted')
 for plant in ['calibrated','slower_decay','faster_decay','varying_bias']:
  runtime=copy.deepcopy(rt);state=copy.deepcopy(st);outrow,reference,event=copy.deepcopy(first);q=q0.copy();qp=qp0.copy();prev=u0.copy();ready=0;trace=[];negative=list(negatives);kind=None
  for k in range(241):
   if k:
    row=dict(outrow,mode='top_cross',contact_load=dict(outrow['contact_load'],filtered_vertical_load_n=0.))
    outrow,reference,event=runtime.update(row,state,reference,**inputs(q,qp,prev,k))
   kind=event['kind'];assert kind in ['command','handover'],event.get('reason');cmd=np.asarray(event['command']);proof=event['proposal'];waypoint=np.asarray(proof['waypoint']);bias=q-prev-a*(qp-prev);expected=np.clip((waypoint-a*q-bias)/(1-a),np.maximum.reduce([audit.lo,q-audit.limits,prev-.055]),np.minimum.reduce([audit.hi,q+audit.limits,prev+.055])).astype(np.float32);np.testing.assert_array_equal(cmd,expected);pred=(1-a)*cmd+a*q+bias;np.testing.assert_allclose(pred,proof['predicted_q'],atol=1e-12,rtol=0)
   checked=[]
   for label,v in [('measured',q),('command',cmd),('predicted',pred)]:
    geometry,_=audit.geometry(v,z);assert geometry['accepted'],(label,geometry)
    if label!='measured':assert geometry['inactive_lowest_z_m']>=.8405
    checked.append(dict(label=label,geometry=geometry))
   geometry,detail=audit.geometry(q,z);point=detail['point'];alignment=abs(detail['rotation'][:,2]@detail['pose'][:3,:3]@np.asarray(planning['thin_axis_local']));isready=bool(max(abs(q-np.asarray(planning['endpoint'])))<=.003 and max(abs(point[:2]-offset))<=.002+2e-7 and min(detail['core'][:2]/2-abs(point[:2]))>=.01 and .004<=geometry['active_above_top_m']<=.01 and alignment>=.8-2e-7 and np.all(q>=audit.lo-2e-7) and np.all(q<=audit.hi+2e-7));ready=ready+1 if isready else 0;assert event['measured_ready_count']==ready and (kind=='handover')==(ready>=3)
   trace.append(dict(step=start['step']+k,kind=kind,command=cmd.tolist(),point_local=point.tolist(),independent_checks=checked,measured_ready_count=ready))
   if k==0:
    for label,change in [('phase',{'mode':'top_push'}),('guard',{'route_stop_reason':'test_original_guard'}),('load',{'contact_load':{'filtered_vertical_load_n':1.}})]:
     badrt=copy.deepcopy(runtime);bad=badrt.update(dict(row0,**change),copy.deepcopy(state),copy.deepcopy(reference),**inputs(q,qp,prev,1))[2];assert bad['kind']=='stop';negative.append(label)
     again=badrt.update(copy.deepcopy(row0),copy.deepcopy(state),copy.deepcopy(reference),**inputs(q,qp,prev,2))[2];assert again['kind']=='stop' and again['reason']==bad['reason'];negative.append(label+'_latched')
    expired=copy.deepcopy(runtime);expired.lifecycle.ticks=240;bad=expired.update(copy.deepcopy(row0),copy.deepcopy(state),copy.deepcopy(reference),**inputs(q,qp,prev,1))[2];assert bad['kind']=='stop' and bad['reason']=='initial_front_path_budget_exhausted';negative.append('240_budget')
   if kind=='handover':
    np.testing.assert_allclose(event['selected_surface_local_xy'],point[:2],atol=1e-8,rtol=0);np.testing.assert_allclose(outrow['target_xyz'],detail['pose'][:3,3]+detail['pose'][:3,:3]@np.asarray(event['captured_center_local']),atol=1e-8,rtol=0);assert outrow['mode']=='top_press' and state.mode=='top_press';assert state.load.bias_m==0. and state.relative_contact_anchor is None and state.push_x_anchor is None;assert np.array_equal(runtime.center_local,event['captured_center_local'])
    for label,changes in [('offset',{'landing_preference_local_xy':[0.,0.]}),('reserve',{'planning_xy_reserve_m':0.}),('outside_xy',{'selected_surface_local_xy':(offset+[.003,0.]).tolist()}),('ready',{'measured_ready_count':2})]:
     before=state_for(z,counter);saved=canon(before)
     try:adapter(copy.deepcopy(row0),before,copy.deepcopy(reference0),dict(event,**changes),object_xyz=scene.target,object_rotation=scene.rotation)
     except ValueError:assert canon(before)==saved;negative.append('handover_'+label)
     else:raise AssertionError('Invalid handover accepted')
    break
   alpha=np.clip(a+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0.),0,.95);biasplant=bias0+(np.sin(k*.12)*np.r_[.0001,np.full(10,.0003)] if plant=='varying_bias' else 0.);nextq=(1-alpha)*cmd+alpha*q+biasplant;geometry,_=audit.geometry(nextq,z);assert geometry['accepted'];qp,q,prev=q,nextq,cmd
  assert kind=='handover' and runtime.lifecycle.ticks<=240
  result=dict(start_step=start['step'],plant=plant,ticks=runtime.lifecycle.ticks,handover=True,negative_rejections=negative,trace=trace);records.append(result);(D/'FRESH_RUNTIME_PROGRESS.json').write_text(json.dumps(dict(completed_scenarios=len(records),expected=12,rows=records,training_ready=False),indent=2));print(json.dumps({k:v for k,v in result.items() if k!='trace'}),flush=True)
sources={str(D/'PREPARATION.json'):sha(D/'PREPARATION.json'),str(ep/'front_recontact_center.json'):sha(ep/'front_recontact_center.json'),str(ep/'coordination.json'):sha(ep/'coordination.json')}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),S/'causal_response_parameters.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
with (D/'FRESH_RUNTIME_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=True,defaultoff_full_first_event_matches=default_checks,fresh_planning_starts=3,scenarios=len(records),handover_scenarios=sum(r['handover'] for r in records),rows=records,source_sha256=sources,collector_integrated=False,physical_started=False,training_ready=False),f,indent=2)
print('COMPLETE12',flush=True)
