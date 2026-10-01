"""Four actual first/last recovery starts, then independent synthetic plants.
Actual planner called once per preference/start; deterministic plan reused for
plant variants only after binding identical start/scene/seed. All commands and
measured captures audited with independent FK. No simulation physics or data.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_minimum_motion_recontact';sys.path[:0]=[str(stage),str(w),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from minimum_motion_lifecycle import RecontactLifecycle
import minimum_motion_lifecycle as lifecycle
from recontact_plan import plan
from audit_minimum_motion_events import EventAudit
from audit_recontact_pose_events import EventAudit as OriginalAudit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);results=[];sources={}
for cid,task,side in [(840001,'push_box_to_bin','right'),(840004,'nudge_mailer_to_bin','left')]:
 ep=w/'precise_interior_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());events=json.loads((ep/'recontact_pose.json').read_text())['rows'];starts=[r for r in events if r.get('planning')];key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box';decay=np.array(fr['plan']['region_causal_response']['decay'])
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);actions=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);oxyz=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float);oquat=z[other].astype(float)
 for event in [starts[0],starts[-1]]:
  t=event['step'];ctx=event['context'];q0=qs[t];past0=qs[t-1];prev0=actions[t-1];assert np.max(abs(q0-ctx['current']))<1e-7
  core=fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz'];scene=RecontactScene(guard,side,xyz[t],quat[t],core,oxyz[t],oquat[t],[.15,.145,.04] if other=='mailer' else [.14,.09,.045]);seed=(starts[0]['step'],qs[starts[0]['step']].copy());bias=(q0-prev0)-decay*(past0-prev0)
  inputs0=dict(step=t,selected=True,parent_mode=ctx['parent_mode'],recontacts=ctx['recontacts'],guard_stop=False,observed_load_n=ctx['observed_load_n'],filtered_load_n=ctx['filtered_load_n'],scene=scene,current=q0,previous_q=past0,previous_command=prev0,decay=decay,observed_hand_pose=guard.model.fk(side,q0)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q0)[0])
  assert RecontactLifecycle().update(**inputs0)['kind']=='unchanged'
  for change in [dict(selected=False),dict(recontacts=0),dict(parent_mode='top_push'),dict(parent_mode='top_press'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051)]:assert RecontactLifecycle(enabled=True,prefer_interior=True).update(**dict(inputs0,**change))['kind']=='unchanged'
  for prefer in [True]:
   computed=plan(scene,q0,step=t,earlier_seed=seed,prefer_interior=prefer,minimum_motion_pose=True);assert computed['accepted']
   if prefer:EventAudit(repo,stage).verify_preference(computed,current=q0,scene=scene.record(),step=t)
   real_plan=lifecycle.plan
   def cached(s,q,*,step,earlier_seed,prefer_interior,minimum_motion_pose):
    assert minimum_motion_pose is True and s.record()==scene.record() and step==t and prefer_interior is prefer and np.array_equal(q,q0) and earlier_seed[0]==seed[0] and np.array_equal(earlier_seed[1],seed[1]);return copy.deepcopy(computed)
   lifecycle.plan=cached
   try:
    for plant in (['calibrated'] if not prefer else ['calibrated','slower_decay','faster_decay','varying_bias']):
     state=RecontactLifecycle(enabled=True,prefer_interior=prefer);state.earliest_seed=seed;auditor=(EventAudit if prefer else OriginalAudit)(repo,stage);q=q0.copy();past=past0.copy();previous=prev0.copy();trace=[];handover=None;negative=[];independent=[]
     for k in range(245):
      inputs=dict(inputs0,step=t+k,parent_mode=ctx['parent_mode'] if k==0 else 'top_cross',current=q,previous_q=past,previous_command=previous,observed_hand_pose=guard.model.fk(side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0]);out=state.update(**inputs);trace.append(out)
      if k==0 and out['kind']=='command':
       active=copy.deepcopy(state)
       for change in [dict(parent_mode='top_push'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051),dict(recontacts=ctx['recontacts']+1)]:
        rejected=copy.deepcopy(active).update(**dict(inputs,**change));assert rejected['kind']=='stop' and rejected['requires_stop'];negative.append(rejected['reason'])
       moved=RecontactScene(guard,side,xyz[t]+[.003,0,0],quat[t],core,oxyz[t],oquat[t],[.15,.145,.04] if other=='mailer' else [.14,.09,.045]);rejected=copy.deepcopy(active).update(**dict(inputs,scene=moved));assert rejected['kind']=='stop';negative.append(rejected['reason'])
       exhausted=copy.deepcopy(active);exhausted.ticks=240;rejected=exhausted.update(**inputs);assert rejected['kind']=='stop';negative.append(rejected['reason'])
      if out['kind'] not in ('command','handover'):break
      audited=auditor.verify(out,**{k:inputs[k] for k in ['step','current','previous_q','previous_command','decay','selected','parent_mode','recontacts','guard_stop','observed_load_n','filtered_load_n']},scene=scene.record(),final_command=out['command']);independent.append(audited)
      if out['kind']=='handover':handover=out;break
      u=np.array(out['command']);a=np.clip(decay+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0),0,.95);b=bias+(np.sin(k*.12)*np.array([.0001]+[.0003]*10) if plant=='varying_bias' else 0);nextq=(1-a)*u+a*q+b;actual,_=auditor.geometry(nextq,scene.record())
      if not actual['accepted']:trace.append(dict(kind='independent_plant_geometry_rejected',geometry=actual));break
      past=q;q=nextq;previous=u
     summary=dict(episode=ep.name,start_step=t,prefer_interior=prefer,plant=plant,completed=handover is not None,iterations=len(trace),absolute_handover_step=None if handover is None else t+len(trace)-1,within_original1200=bool(handover is not None and t+len(trace)-1<1200),final_kind=trace[-1]['kind'],final_reason=trace[-1].get('reason'),negative_checks=negative,selected=computed['minimum_motion_pose']['selected'],independent_events=len(independent));results.append(dict(summary=summary,trace=trace,independent=independent));print(summary,flush=True)
   finally:lifecycle.plan=real_plan
 for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','recontact_pose.json']:sources[str(ep/name)]=sha(ep/name)
for p in [Path(__file__),w/'audit_minimum_motion_events.py',w/'audit_minimum_motion_plan.py',w/'audit_recontact_interior_events.py',w/'audit_recontact_pose_events.py',w/'audit_unloaded_wrist_prior_live.py',w/'audit_unloaded_wrist_task_optimality.py',*stage.glob('*.py'),stage/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json']:sources[str(p)]=sha(p)
assert len(results)==16
out=dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(r['summary']['completed'] and len(r['summary']['negative_checks'])==7 for r in results),rows=results,original_episode_budget_failures=[r['summary'] for r in results if not r['summary']['within_original1200']],source_sha256=sources,physical_validation=False,training_ready=False);(stage/'LIFECYCLE_CHECK.json').write_text(json.dumps(out,indent=2));print('DONE',out['passed'],'original budget failures',len(out['original_episode_budget_failures']),flush=True)
