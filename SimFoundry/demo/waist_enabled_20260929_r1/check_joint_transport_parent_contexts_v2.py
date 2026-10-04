"""Actual parent-audit functions and self-clearance tail on isolated real contexts.
Final output is an explicitly unissued proposal; no state/history is replayed as
new physics. Parent intermediate and previous actually recorded action are distinct.
"""
from pathlib import Path
import ast,copy,json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_joint_transport_v1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from joint_transport_j2_loaded_episode_inputs import EpisodeInputs
from audit_joint_transport_j2_v2_z_execution import recorded_rotation,RuntimeGapRepresentation
from audit_joint_transport_j2_v3_stage_self_clearance import near
from audit_front_loaded_z_priority_record import verify_record
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from screen_bag_vertical_priority_geometry import Geometry
from simfoundry.data.bounded_ik import bounded_damped_step
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
path=W/'audit_joint_transport_j2_v3_stage_self_clearance.py';tree=ast.parse(path.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.iter)=='coordinates');start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='priority');code=compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(loop.body[start:]),type_ignores=[])),str(path),'exec')
guard=ClearanceGuard(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');cache={};results=[];negative=[];sources={}
contexts=[]
for n in sorted((W/'joint_transport_runtime_preparation_r1').glob('CONTEXT_*.json')):
 r=read(n);contexts.append(dict(side=r['proposal']['side'],step=r['step'],task='push_box_to_bin' if r['proposal']['side']=='right' else 'nudge_mailer_to_bin',run='inactive_transport_physical_r1',record=r))
for rr in contexts:
 side,t,task=rr['side'],rr['step'],rr['task'];case=840020 if side=='right' else 840023;ep=W/rr['run']/f'case_{case}'/f'layout_{case}_{task}'
 if str(ep) not in cache:
  e=EpisodeInputs.__new__(EpisodeInputs);e.ep=ep;e.n=1200;e.task=task;e.side=side;e.key='box' if side=='right' else 'mailer';e.other='mailer' if side=='right' else 'box'
  with np.load(ep/'raw.npz') as z:e.q=z['q'][:,12:23].astype(float);e.u=z['action'][:,12:23].astype(float)
  e.front=read(ep/'front_initial_center.json');e.capture={r['step']:r for r in e.front['rows']}
  for r in read(ep/'front_recontact_center.json')['rows']:
   if r['center_local_after'] is not None:e.capture[r['step']]=r
  e.coords={r['step']:r for r in read(ep/'coordination.json')};e.rows={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']};e.experts={r['step']:r for r in read(ep/'expert_control.json')};e.packets=read(ep/'solved_contact_forces.json')['rows']
  with np.load(ep/'trace.npz') as z:e.xyz=z[e.key].copy();e.oxy=z[e.other].copy()
  with np.load(ep/'parcel_orientation.npz') as z:e.R=np.array([recorded_rotation(x) for x in z[e.key]]);e.OR=np.array([recorded_rotation(x) for x in z[e.other]])
  e.size=[.15,.145,.04] if side=='right' else [.14,.09,.045];e.elbows=elbows;e.hand=hand;e.solver=bounded_damped_step;e.geometry=RuntimeGapRepresentation(Geometry(ep.parent));loaded={r['step']:r for r in read(ep/'front_loaded_z_priority.json')['rows']};cache[str(ep)]=(e,loaded)
  for n in ['raw.npz','coordination.json','frontal_bypass.json','expert_control.json','front_initial_center.json','front_recontact_center.json','front_loaded_z_priority.json','solved_contact_forces.json','trace.npz','parcel_orientation.npz']:sources[str(ep/n)]=sha(ep/n)
 base,loaded=cache[str(ep)];e=copy.copy(base);e.u=base.u.copy();e.transport_parent=np.array([loaded[k]['output_command'] for k in range(e.n)]);e.u[t]=rr['record']['output_command'];e.coords=copy.deepcopy(base.coords);e.coords[t]['joint_transport_clearance']=copy.deepcopy(rr['record']);e.coords[t]['joint_transport_unexecuted_parent_waist_target_rad']=float(e.transport_parent[t,0]);e.coords[t]['waist_target_rad']=float(e.u[t,0])
 args=e.arguments(t,loaded[t]);np.testing.assert_array_equal(args['output'],e.transport_parent[t]);np.testing.assert_array_equal(args['previous_actual'],base.u[t-1])
 try:verified=verify_record(**args);passed=verified['passed'];failure=None
 except (AssertionError,ValueError,KeyError) as err:
  import traceback
  passed=False;failure=traceback.format_exc()
 if passed:
  e.final={t:guard.command(e.u[t],e.q[t],e.u[t-1])};e.verify_actual_final_guard(t)
  ns=dict(np=np,near=near,t=t,c=e.coords[t],target=np.array(loaded[t]['context']['parent_command'],dtype=np.float32),priority_records=loaded,transport_parent=e.transport_parent,u=e.u,controller_frames=0)
  exec(code,ns);assert ns['controller_frames']==1
 from joint_transport_parent_coordinate_v1 import parent_coordinate
 before=copy.deepcopy(e.coords[t]);view=parent_coordinate(e.coords[t],e.transport_parent[t],e.u[t]);assert e.coords[t]==before
 np.testing.assert_array_equal(args['current'],base.q[t]);np.testing.assert_array_equal(args['previous_actual'],base.u[t-1])
 if side=='right' and t==808:
  for label in ['wrong_parent_waist','hidden_final_waist','wrong_parent_vector','wrong_final_vector']:
   c=copy.deepcopy(e.coords[t]);p=e.transport_parent[t].copy();u=e.u[t].copy()
   if label=='wrong_parent_waist':c['joint_transport_unexecuted_parent_waist_target_rad']+=.001
   elif label=='hidden_final_waist':c['waist_target_rad']=float(p[0])
   elif label=='wrong_parent_vector':p[1]+=.001
   else:u[1]+=.001
   try:parent_coordinate(c,p,u)
   except (AssertionError,ValueError):negative.append(label)
   else:raise AssertionError(label)
 results.append(dict(run=rr['run'],step=t,side=side,joint_applied=rr['record']['applied'],loaded_z_applied=loaded[t]['applied'],original_loaded_record_passed=passed,failure=failure,actual_previous_preserved=True,unissued_output_slot_only=True));print(json.dumps({k:v for k,v in results[-1].items() if k!='failure'}),flush=True)
assert len(results)==8 and len(negative)==4 and all(r['original_loaded_record_passed'] for r in results)
for p in [Path(__file__),path,W/'joint_transport_j2_loaded_episode_inputs.py',W/'audit_joint_transport_j2_v2_z_execution.py',W/'joint_transport_runtime_preparation_r1/RUNTIME_CONTEXT_CHECK.json',W/'joint_transport_runtime_preparation_r1/AUDIT_FAMILY_V2_PREPARATION.json',W/'joint_transport_parent_coordinate_v1.py']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(passed=all(r['original_loaded_record_passed'] for r in results),created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=results,negative_cases=negative,source_sha256=sources,complete_new_push_trajectory_checked=False,physics_started=False,training_ready=False)
with (W/'joint_transport_runtime_preparation_r1/J2_PARENT_CONTEXT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=out['passed'],contexts=len(results),failures=sum(not r['original_loaded_record_passed'] for r in results))))
