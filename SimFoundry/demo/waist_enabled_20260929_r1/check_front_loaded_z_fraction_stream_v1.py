"""Two complete archived front episodes; independent one-step proposals only.
Keep actual measured state and previous action at each step. Recompute transport
only when quarter-Z changes its input; otherwise bind the recorded downstream
output. This is NOT a counterfactual closed-loop trajectory or force prediction.
"""
from pathlib import Path
import sys,json,copy,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';C=W/'front_loaded_z_fraction_candidate_v1';D=W/'front_loaded_z_fraction_stream_check_r1';D.mkdir(exist_ok=False);sys.path[:0]=[str(C),str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from front_loaded_z_fraction import FrontLoadedZFraction
from joint_transport_runtime import JointTransportRuntime
from recontact_scene import RecontactScene
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from screen_bag_vertical_priority_geometry import Geometry
from front_loaded_z_priority_audit_geometry import evaluate,point
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
guard=ClearanceGuard(ROOT,S);full=FrontLoadedZFraction(guard);quarter=FrontLoadedZFraction(guard,.25);transport=JointTransportRuntime(guard,ROOT,S,enabled=True)
hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');sources={};summaries=[]
for case,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/f'front_corridor_lateral_physical_r1/case_{case}/layout_{case}_{task}';side='left' if task=='nudge_mailer_to_bin' else 'right';g=Geometry(ep.parent);sources.update(g.sources);rows=[];coords=read(ep/'coordination.json');fr={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}
 ready=read(ep/'READY_FOR_AUDIT.json')
 for p,h in ready['source_sha256'].items():assert sha(p)==h,p
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float)
 assert len(q)==1200 and [c['step'] for c in coords]==list(range(1,1200));assert np.max(abs(q[0]))<1e-4 and np.array_equal(u[0],np.zeros(11))
 for co0 in coords:
  t=co0['step'];co=copy.deepcopy(co0);original=co['front_loaded_z_priority'];ctx=original['context'];tr=co['joint_transport_clearance'];tc=tr['collector_context'];co['front_loaded_z_priority_side']=side
  np.testing.assert_array_equal(q[t],ctx['current']);np.testing.assert_array_equal(u[t-1],ctx['previous']);np.testing.assert_array_equal(tr['parent_command'],original['output_command']);np.testing.assert_array_equal(u[t],tr['output_command'])
  sc=tc['scene'];scene=None if sc is None else RecontactScene(guard,**sc);extra={} if sc is None else dict(target_rotation=Rotation.from_quat(sc['target_quat']).as_matrix(),other_xyz=sc['other_xyz'],other_rotation=Rotation.from_quat(sc['other_quat']).as_matrix(),other_size=sc['other_size'])
  args=dict(step=t,selected=original['selected'],row=fr[t],coordinate=co,current=q[t],previous=u[t-1],parent_command=ctx['parent_command'],**extra)
  xfull,mfull=full.refine(**args);np.testing.assert_array_equal(xfull,original['output_command']);assert mfull==original,('default metadata mismatch',ep.name,t)
  x,m=quarter.refine(**args);changed=not np.array_equal(x,xfull);independent=None
  if 'solver' in m:
   a=m.get('reduced_z_task',{}).get('modified_task',co['task_inputs']);independent=evaluate(a,co,np.asarray(m['solver']['candidate_command']),np.asarray(ctx['parent_command']),hand,elbows,g,side)
   assert independent['passed']==m['nominal_verification']['passed'],('independent mismatch',t)
  if changed:
   co['front_loaded_z_priority']=m
   if m['applied']:co['waist_target_rad']=float(x[0])
   out,tm=transport.refine(step=t,selected=tr['selected'],side=side,row=fr[t],coordinate=co,scene=scene,current=q[t],previous_q=q[t-1],previous_command=u[t-1],parent_command=x,decay=tc['decay'])
  else:out=np.asarray(tr['output_command']);tm=tr
  final=guard.command(out,q[t],u[t-1]);assert final['accepted'],('final guard rejected',ep.name,t)
  low=np.maximum.reduce([guard.lower,q[t]-guard.limits,u[t-1]-.055]);high=np.minimum.reduce([guard.upper,q[t]+guard.limits,u[t-1]+.055]);assert np.all(out>=low-2e-7) and np.all(out<=high+2e-7) and min(elbows.gap(out))>=.005-2e-7
  zsummary={}
  if 'target_rotation' in ctx:
   normal=np.asarray(ctx['target_rotation'])[:,2];center=np.asarray(ctx['center_local']);observed=point(hand,q[t],side,normal,center)
   zsummary={name:float((point(hand,v,side,normal,center)[2]-observed[2])*1000) for name,v in [('priority_dz_mm',x),('final_dz_mm',out)]}
  rows.append(dict(step=t,quarter_applied=m['applied'],changed_from_full=changed,quarter_reason=m['reason'],transport_recomputed=changed,transport_applied=tm['applied'],transport_reason=tm['reason'],independent_nominal_passed=None if independent is None else independent['passed'],final_guard_passed=True,independent_final_bounds_elbows_passed=True,**zsummary))
  if changed:
   with (D/f'{case}_{task}_{t:04d}.json').open('x') as f:json.dump(dict(step=t,priority=m,transport=tm,final_guard=final,independent_nominal=independent),f,indent=2)
  if t%40==0:
   status=dict(episode=ep.name,steps_checked=t,expected=1199,changed=sum(r['changed_from_full'] for r in rows),quarter_applied=sum(r['quarter_applied'] for r in rows),physics_started=False,training_ready=False);(D/'PROGRESS.json').write_text(json.dumps(status,indent=2));print(json.dumps(status),flush=True)
 summary=dict(episode=ep.name,frames=1200,steps_checked=len(rows),first_frame_zero=True,default_exact_all_steps=True,changed=sum(r['changed_from_full'] for r in rows),quarter_applied=sum(r['quarter_applied'] for r in rows),rows=rows);summaries.append(summary)
 with (D/f'{case}_{task}_SUMMARY.json').open('x') as f:json.dump(summary,f,indent=2)
 for n in ['coordination.json','frontal_bypass.json','raw.npz','READY_FOR_AUDIT.json']:sources[str(ep/n)]=sha(ep/n)
for mod in list(sys.modules.values()):
 f=getattr(mod,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
for p in [Path(__file__),S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episodes=summaries,source_sha256=sources,passed=True,collector_integrated=False,physics_started=False,training_ready=False)
with (D/'RESULT.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,episodes=len(summaries),steps=sum(s['steps_checked'] for s in summaries))),flush=True)
