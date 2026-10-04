"""Actual parent-audit functions and self-clearance tail on isolated real contexts.
Final output is an explicitly unissued proposal; no state/history is replayed as
new physics. Parent intermediate and previous actually recorded action are distinct.
"""
from pathlib import Path
import ast,copy,json,hashlib,datetime,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from inactive_transport_a3_loaded_episode_inputs import EpisodeInputs
from audit_inactive_transport_a3_v2_z_execution import recorded_rotation,RuntimeGapRepresentation
from audit_inactive_transport_a3_v3_stage_self_clearance import near
from audit_front_loaded_z_priority_record import verify_record
from audit_unloaded_wrist_prior_live import HandModel
from audit_self_clearance_task_optimality import IndependentElbows
from screen_bag_vertical_priority_geometry import Geometry
from simfoundry.data.bounded_ik import bounded_damped_step
from clearance_runtime import ClearanceGuard
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
path=W/'audit_inactive_transport_a3_v3_stage_self_clearance.py';tree=ast.parse(path.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.iter)=='coordinates');start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='priority');code=compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(loop.body[start:]),type_ignores=[])),str(path),'exec')
guard=ClearanceGuard(ROOT,S);hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json');elbows=IndependentElbows(S/'elbow_torso_hulls.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf');cache={};results=[];negative=[];sources={}
for rr in read(S/'ACTUAL_CORE_RUNTIME_PROBE.json')['records']:
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
 base,loaded=cache[str(ep)];e=copy.copy(base);e.u=base.u.copy();e.transport_parent=base.u.copy();e.u[t]=rr['record']['output_command'];e.coords=copy.deepcopy(base.coords);e.coords[t]['inactive_transport_clearance']=copy.deepcopy(rr['record'])
 args=e.arguments(t,loaded[t]);np.testing.assert_array_equal(args['output'],base.u[t]);np.testing.assert_array_equal(args['previous_actual'],base.u[t-1]);np.testing.assert_array_equal(e.arguments(t+1,loaded[t+1])['previous_actual'],e.u[t]);np.testing.assert_array_equal(e.arguments(t+1,loaded[t+1])['output'],base.u[t+1])
 verified=verify_record(**args);assert verified['passed']
 e.final={t:guard.command(e.u[t],e.q[t],e.u[t-1])};e.verify_actual_final_guard(t)
 ns=dict(np=np,near=near,t=t,c=e.coords[t],target=np.array(loaded[t]['context']['parent_command'],dtype=np.float32),priority_records=loaded,transport_parent=e.transport_parent,u=e.u,controller_frames=0)
 exec(code,ns);assert ns['controller_frames']==1
 results.append(dict(run=rr['run'],step=t,side=side,transport_applied=rr['record']['applied'],loaded_z_applied=loaded[t]['applied'],original_loaded_record_passed=True,original_final_guard_passed=True,actual_previous_and_parent_distinct=True));print(json.dumps(results[-1]),flush=True)
 if rr['record']['applied'] and sum(r['transport_applied'] for r in results)==1:
  for label in ['wrong_parent_output','wrong_actual_output','wrong_previous_actual','wrong_coordinate_parent','wrong_coordinate_final']:
   a=copy.copy(args);n=copy.deepcopy({k:v for k,v in ns.items() if k not in ['np','near','__builtins__']});n.update(np=np,near=near,target=np.array(loaded[t]['context']['parent_command'],dtype=np.float32),controller_frames=0)
   if label=='wrong_parent_output':a['output']=e.u[t]
   elif label=='wrong_previous_actual':a['previous_actual']=e.transport_parent[t]
   elif label=='wrong_actual_output':n['u'][t]=e.transport_parent[t]
   elif label=='wrong_coordinate_parent':n['c']['inactive_transport_clearance']['parent_command'][3]+=.001
   else:n['c']['inactive_transport_clearance']['output_command'][3]+=.001
   try:
    if label in ['wrong_parent_output','wrong_previous_actual']:verify_record(**a)
    else:exec(code,n)
   except (AssertionError,ValueError,KeyError):negative.append(label)
   else:raise AssertionError(label)
assert len(results)==22 and sum(r['transport_applied'] for r in results)==15 and sum(r['loaded_z_applied'] for r in results)==4 and len(negative)==5
for p in [Path(__file__),path,W/'inactive_transport_a3_loaded_episode_inputs.py',W/'audit_inactive_transport_a3_v2_z_execution.py',S/'ACTUAL_CORE_RUNTIME_PROBE.json',S/'AUDIT_FAMILY_V3_IMPORT_CHECK.json']:sources[str(p)]=sha(p)
for p,h in sources.items():assert sha(p)==h
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=results,negative_cases=negative,source_sha256=sources,complete_new_push_trajectory_checked=False,physics_started=False,training_ready=False)
with (S/'PARENT_COMMAND_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,contexts=22,transport_unissued=15,loaded_z_applied=4,negative=5)))
