"""Three fresh runtime starts with small hypothetical target-yaw motion.
Independent URDF ready/capture and geometry recomputation. Adapter state is a
stand-in, objects otherwise fixed, unloaded synthetic responses; not physics.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,datetime,copy
import numpy as np
from scipy.spatial.transform import Rotation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_joint_transport_reserve_v1';sys.path[:0]=[str(D),str(S),str(W),str(ROOT)]
from trailing_runtime import FrontRecontactCenterRuntime as Runtime
from trailing_adapter import apply
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from audit_front_initial_center_events import EventAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((D/'PREPARATION.json').read_text())
for x in prep['sources']:
 for name in ['parent','candidate']:assert sha(x[name])==x[name+'_sha256']
ep=W/'joint_transport_reserve_physical_r1/case_840020/layout_840020_push_box_to_bin';rows=[r for r in json.loads((ep/'front_recontact_center.json').read_text())['rows'] if r.get('planning')];starts=[rows[i] for i in [0,6,12]];coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};guard=ClearanceGuard(ROOT,S);audit=EventAudit(ROOT,S);records=[]
class Reset:
 def reset(self):pass
for start in starts:
 ctx=start['context'];z=ctx['scene'];counter=start['real_recontact_index'];q,qp,prev,a=[np.asarray(ctx[k]) for k in ['current','previous_q','previous_command','decay']];bias0=q-prev-a*(qp-prev);original=RecontactScene(guard,**z);rt=Runtime(guard,'right',z['core_size'],z['other_size'],a,enabled=True,trailing_landing=True);rt.last_counter=counter-1;state=SimpleNamespace(recontacts=counter,size=np.asarray(z['core_size']),load=SimpleNamespace(bias_m=0.),cross_axis_control=Reset(),cop_slip=Reset(),last_emitted_xy=None);ref={k:np.asarray(v) for k,v in coord[start['step']-1]['active_support_reference'].items()};row=dict(mode=ctx['parent_mode'],recontacts=counter,contact_load=dict(filtered_vertical_load_n=ctx['filtered_load_n'],applied_z_bias_m=0.,stored_z_bias_m=0.));ready=0;trace=[];negative=[]
 for tick in range(241):
  yaw=.001*np.sin(tick*.37);zz=dict(z,target_quat=(Rotation.from_rotvec([0,0,yaw])*Rotation.from_quat(z['target_quat'])).as_quat().tolist());scene=RecontactScene(guard,**zz);assert not scene.moved_since(original)['changed'];inputs=dict(selected=True,step=start['step']+tick,current=q,previous_q=qp,previous_command=prev,target_xyz=zz['target_xyz'],target_quat=zz['target_quat'],other_xyz=zz['other_xyz'],other_quat=zz['other_quat'],observed_load_n=0.,observed_hand_pose=guard.model.fk('right',q)[0],observed_inactive_hand_pose=guard.model.fk('left',q)[0],normal_anchor=start['old_normal_anchor'],inactive_anchor=start['old_inactive_anchor']);row,ref,event=rt.update(row,state,ref,**inputs);kind=event['kind'];assert kind in ['command','handover'],event.get('reason');cmd=np.asarray(event['command']);proof=event['proposal'];waypoint=np.asarray(proof['waypoint']);bias=q-prev-a*(qp-prev);expected=np.clip((waypoint-a*q-bias)/(1-a),np.maximum.reduce([audit.lo,q-audit.limits,prev-.055]),np.minimum.reduce([audit.hi,q+audit.limits,prev+.055])).astype(np.float32);np.testing.assert_array_equal(expected,cmd);pred=(1-a)*cmd+a*q+bias;np.testing.assert_allclose(pred,proof['predicted_q'],atol=1e-12,rtol=0)
  for v in [q,cmd,pred]:assert audit.geometry(v,zz)[0]['accepted']
  g,details=audit.geometry(q,zz);point=details['point'];offset=(details['rotation'].T@np.array([0,.020,0]))[:2];np.testing.assert_array_equal(offset,event['landing_preference_local_xy']);plan=rt.lifecycle.plan;alignment=abs(details['rotation'][:,2]@details['pose'][:3,:3]@np.asarray(plan['thin_axis_local']));isready=bool(max(abs(q-np.asarray(plan['endpoint'])))<=.003 and max(abs(point[:2]-offset))<=.002+2e-7 and min(details['core'][:2]/2-abs(point[:2]))>=.01 and .004<=g['active_above_top_m']<=.01 and alignment>=.8-2e-7 and np.all(q>=audit.lo-2e-7) and np.all(q<=audit.hi+2e-7));ready=ready+1 if isready else 0;assert event['measured_ready_count']==ready and (kind=='handover')==(ready>=3)
  if tick==0:
   assert event['planning']['planning_xy_reserve_m']==.0005 and event['planning']['transport_preflight']['predicted_capture_discarded'] and rt.center_local is None
   for label,change in [('rotation',{'target_quat':(Rotation.from_rotvec([0,0,.021])*Rotation.from_quat(z['target_quat'])).as_quat().tolist()}),('translation',{'target_xyz':(np.asarray(z['target_xyz'])+[.0021,0,0]).tolist()})]:
    bad=copy.deepcopy(rt).update(copy.deepcopy(row),copy.deepcopy(state),copy.deepcopy(ref),**dict(inputs,step=inputs['step']+1,**change))[2];assert bad['kind']=='stop' and bad['reason']=='object_pose_changed_during_path';negative.append(label)
  trace.append(dict(step=start['step']+tick,kind=kind,yaw_change_rad=yaw,point_local=point.tolist(),current_target_xy=offset.tolist(),event=event))
  if kind=='handover':
   np.testing.assert_allclose(event['selected_surface_local_xy'],point[:2],atol=1e-8,rtol=0);np.testing.assert_allclose(row['target_xyz'],details['pose'][:3,3]+details['pose'][:3,:3]@np.asarray(event['captured_center_local']),atol=1e-8,rtol=0);assert state.mode=='top_press' and state.load.bias_m==0.;assert max(abs(np.asarray(event['landing_preference_local_xy'])-np.asarray(plan['landing_preference_local_xy'])))>1e-8
   bad=dict(event,landing_preference_local_xy=plan['landing_preference_local_xy'])
   try:apply(dict(row,route_stop_reason=None,release_reason=None),copy.deepcopy(state),ref,bad,object_xyz=scene.target,object_rotation=scene.rotation)
   except ValueError:negative.append('stale_planning_rotation_capture')
   else:raise AssertionError('Stale rotation accepted')
   break
  nextq=(1-a)*cmd+a*q+bias0;assert audit.geometry(nextq,zz)[0]['accepted'];qp,q,prev=q,nextq,cmd;row=dict(row,mode='top_cross',contact_load=dict(row['contact_load'],filtered_vertical_load_n=0.))
 assert kind=='handover';result=dict(start_step=start['step'],ticks=rt.lifecycle.ticks,handover=True,negative_rejections=negative,trace=trace);records.append(result);(D/'MOVING_RUNTIME_PROGRESS.json').write_text(json.dumps(dict(completed=len(records),expected=3,rows=records,training_ready=False),indent=2));print(json.dumps({k:v for k,v in result.items() if k!='trace'}),flush=True)
sources={str(p):sha(p) for p in [D/'PREPARATION.json',Path(__file__),ep/'front_recontact_center.json',ep/'coordination.json',S/'causal_response_parameters.json',S/'elbow_torso_hulls.json',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']}
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
with (D/'MOVING_RUNTIME_CHECK.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,complete=True,scenarios=3,handover_scenarios=3,rows=records,source_sha256=sources,collector_integrated=False,physical_started=False,training_ready=False),f,indent=2)
print('COMPLETE3',flush=True)
