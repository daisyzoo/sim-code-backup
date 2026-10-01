"""Actual recorded starting states, then independent synthetic response plants.
Checks the new callable planner/lifecycle, measured-only handover, default-off
and active-path aborts. Plant variants are preflight hypotheses, not physics.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_short_recovery';probe=w/'staged_recontact_pose_probe';sys.path[:0]=[str(probe),str(stage),str(repo)]
from clearance_runtime import ClearanceGuard
from recontact_scene import RecontactScene
from recontact_lifecycle import RecontactLifecycle
from recontact_plan import plan
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(repo,stage);results=[]
for cid,task,side in [(840001,'push_box_to_bin','right'),(840004,'nudge_mailer_to_bin','left')]:
 ep=w/'unloaded_wrist_prior_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());key='box' if side=='right' else 'mailer';other='mailer' if side=='right' else 'box'
 with np.load(ep/'raw.npz') as z:qs=z['q'][:,12:23].astype(float);actions=z['action'][:,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float);oxyz=z[other].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float);oquat=z[other].astype(float)
 core=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);size=[.15,.145,.04] if other=='mailer' else [.14,.09,.045];decay=np.array(fr['plan']['region_causal_response']['decay']);crosses=[];last=None
 for r in fr['rows']:
  if r['mode']=='top_cross' and last!='top_cross' and r['recontacts']>0:crosses.append(r)
  last=r['mode']
 for row in [crosses[0],crosses[-1]]:
  t=row['step'];scene=RecontactScene(guard,side,xyz[t],quat[t],core,oxyz[t],oquat[t],size);q0=qs[t];past0=qs[t-1];prev0=actions[t-1];bias=(q0-prev0)-decay*(past0-prev0)
  start_inputs=dict(step=t,selected=True,parent_mode='top_cross',recontacts=row['recontacts'],guard_stop=False,observed_load_n=0.,filtered_load_n=0.,scene=scene,current=q0,previous_q=past0,previous_command=prev0,decay=decay,observed_hand_pose=guard.model.fk(side,q0)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q0)[0])
  assert RecontactLifecycle().update(**start_inputs)['kind']=='unchanged'
  for changes in [dict(selected=False),dict(recontacts=0),dict(parent_mode='top_push'),dict(parent_mode='top_press'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051)]:
   assert RecontactLifecycle(enabled=True).update(**dict(start_inputs,**changes))['kind']=='unchanged'
  try:plan(scene,q0,step=t,earlier_seed=(t+1,q0))
  except ValueError:pass
  else:raise AssertionError('Future seed accepted')
  plants=[]
  for plant in ['calibrated','slower_decay','faster_decay','varying_bias']:
   state=RecontactLifecycle(enabled=True);state.earliest_seed=(crosses[0]['step'],qs[crosses[0]['step']].copy());q=q0.copy();past=past0.copy();previous=prev0.copy();trace=[];handover=None;aborts=None;first_active=None
   for k in range(245):
    inputs=dict(start_inputs,step=t+k,current=q,previous_q=past,previous_command=previous,observed_hand_pose=guard.model.fk(side,q)[0],observed_inactive_hand_pose=guard.model.fk(scene.inactive,q)[0])
    out=state.update(**inputs)
    if k==0 and out['kind']=='command':
     first_active=copy.deepcopy(state);negative=[]
     for changes in [dict(parent_mode='top_push'),dict(guard_stop=True),dict(observed_load_n=.001),dict(filtered_load_n=.051),dict(recontacts=row['recontacts']+1)]:
      rejected=copy.deepcopy(first_active).update(**dict(inputs,**changes));assert rejected['kind']=='stop' and rejected['requires_stop'];negative.append(rejected['reason'])
     moved=RecontactScene(guard,side,xyz[t]+np.array([.003,0,0]),quat[t],core,oxyz[t],oquat[t],size);rejected=copy.deepcopy(first_active).update(**dict(inputs,scene=moved));assert rejected['kind']=='stop';negative.append(rejected['reason'])
     exhausted=copy.deepcopy(first_active);exhausted.ticks=240;rejected=exhausted.update(**inputs);assert rejected['kind']=='stop';negative.append(rejected['reason']);aborts=negative
    trace.append(out)
    if out['kind']=='handover':
     # Independent measured-pose capture recomputation, not planned endpoint.
     T=guard.model.fk(side,q)[0];verts=guard.model.vertices[side];pts=(verts@T[:3,:3].T+T[:3,3]-scene.target)@scene.rotation;ix=int(pts[:,2].argmin());assert np.max(abs(np.array(out['captured_center_local'])-verts[ix]))<1e-9;assert np.max(abs(np.array(out['selected_surface_local_xy'])-pts[ix,:2]))<1e-8;assert np.max(abs(np.array(out['captured_normal_local_up'])-T[2,:3]))<1e-8;assert min(core[:2]/2-abs(pts[ix,:2]))>=.01;assert out['measured_ready_count']>=3;Ti=guard.model.fk(scene.inactive,q)[0];assert np.max(abs(np.array(out['captured_inactive_anchor_world'])-(Ti[:3,3]+Ti[:3,:3]@np.array([.20,0,.007]))))<1e-8;handover=out;break
    if out['kind']!='command':break
    u=np.array(out['command']);a=np.clip(decay+(.06 if plant=='slower_decay' else -.06 if plant=='faster_decay' else 0),0,.95);b=bias+(np.sin(k*.12)*np.array([0.0001]+[.0003]*10) if plant=='varying_bias' else 0);nextq=(1-a)*u+a*q+b
    actual=scene.check(nextq)
    if not actual['accepted']:trace.append(dict(kind='plant_geometry_rejected',actual=actual));break
    past=q;q=nextq;previous=u
   summary=dict(plant=plant,completed=handover is not None,iterations=len(trace),final_kind=trace[-1]['kind'],final_reason=trace[-1].get('reason'),active_abort_checks=aborts,final_wrist_rad=float(q[5 if side=='left' else 10]),initial_wrist_rad=float(q0[5 if side=='left' else 10]));plants.append(dict(summary=summary,trace=trace));print(ep.name,t,json.dumps(summary),flush=True)
  results.append(dict(episode=ep.name,step=t,plants=plants,source_sha256={n:sha(ep/n) for n in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']}))
  (probe/'LIFECYCLE_CHECK.json').write_text(json.dumps(dict(scope=__doc__,rows=results,checker_sha256=sha(Path(__file__)),source_sha256={str(p):sha(p) for p in probe.glob('*.py')},model_source_sha256=guard.model.source_sha256,physical_validation=False,training_ready=False),indent=2))
