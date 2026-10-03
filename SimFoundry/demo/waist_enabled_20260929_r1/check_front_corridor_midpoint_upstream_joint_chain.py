"""UNISSUED first midpoint proposal through actual collector selection and full audit loop.
The upstream proposal reuses actual six position task rows/current/previous and
nominal FK normal rows, because the historical raw wrist quaternion was not
archived. No synthetic future observations and no new physical success claim.
"""
from pathlib import Path
import ast,copy,datetime,hashlib,json,sys
from types import SimpleNamespace
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_midpoint_integrated';D=W/'staged_front_corridor_midpoint';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Reuse bound first-proposal setup exactly, excluding its exclusive report writer.
p=W/'check_front_corridor_midpoint_joint_proposal.py';bound=json.loads((D/'SINGLE_STEP_JOINT_PROPOSAL_CHECK.json').read_text())
for name,h in bound['source_sha256'].items():assert sha(name)==h,name
for name in ['waist_coordination_clearance.py','task_ik_precision.py','front_loaded_z_priority.py','front_initial_center_route.py','front_initial_center_cop_route.py','front_corridor_midpoint_runtime.py']:
 assert sha(S/name)==sha(D/name),name
tree=ast.parse(p.read_text());cut=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sources' for t in n.targets));ns={'__file__':str(p),'__name__':'midpoint_upstream_unissued_fixture'};exec(compile(ast.Module(body=tree.body[:cut],type_ignores=[]),str(p),'exec'),ns)
E,c,row,command,metadata,normal=[ns[k] for k in ['E','c','row','command','metadata','normal']];t=173
assert metadata['applied'] is True
# Actual collector AST: preserve a captured normal anchor in top_push, drop it
# in old guard-lift. No robot values needed when the anchor already exists.
collector=ast.parse((S/'collect_paired_sorting.py').read_text());block=None
for n in ast.walk(collector):
 if isinstance(n,ast.If) and ast.unparse(n.test)=='args.expert_top_contact_normal_hold and frontal_plan is not None':block=n
assert block is not None
selector=compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'<exact collector normal selection>','exec')
for mode,expected in [('top_push',E.capture[t]['old_normal_anchor']),('front_guard_lift',None)]:
 env=dict(args=SimpleNamespace(expert_top_contact_normal_hold=True),frontal_plan=E.frontal['plan'],expert=SimpleNamespace(mode=mode),top_contact_normal_anchor=E.capture[t]['old_normal_anchor'],active_normal_anchor=None)
 exec(selector,env);assert env['active_normal_anchor']==expected
# Exact native coordinator tail performs task concatenation, original bounded
# solver, precise self-clearance solution, waist clipping and action conversion.
coordinator=ast.parse((S/'waist_coordination_clearance.py').read_text());fn=next(n for n in coordinator.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='jac' for v in n.targets));tail=copy.deepcopy(fn.body[start:]);assert isinstance(tail[-1],ast.Return);# Keep the full function tail including its early rejected-command return.
import torch
joint_positions=torch.zeros((1,23),dtype=torch.float32);joint_positions[0,12:23]=torch.tensor(E.q[t],dtype=torch.float32)
env=dict(np=np,torch=torch,rows=[torch.tensor(c['task_inputs']['jacobian'],dtype=torch.float32)],errors=[torch.tensor(c['task_inputs']['error'],dtype=torch.float32)],robot=SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=joint_positions))),joint_ids=list(range(12,23)),waist_preference=E.coords[t]['waist_preference_rad'],waist_limit=1.,bounded=True,clearance_geometry=ns['guard'].geometry,previous_command=E.u[t-1],precise_task_ik=True,action=np.zeros(23,dtype=np.float32),default=np.zeros(23,dtype=np.float32),indices=list(range(12,23)),palms=c['palm_positions'],points=c['control_point_positions'],active_point_offset=c['active_point_offset_local'],anchor={'right':c['inactive_anchor']},state=SimpleNamespace(side='left'),active_support_reference=c['active_support_reference'],normal_record=c['contact_normal_tracking'],yaw_record=None,trace_jacobian=False)
native_fn=ast.FunctionDef(name='native_tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=tail,decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[native_fn],type_ignores=[])),'<exact native coordinator tail>','exec'),env)
env['native_result']=env['native_tail']()
np.testing.assert_array_equal(np.asarray(env['native_result']['task_inputs']['jacobian']),np.asarray(c['task_inputs']['jacobian']))
np.testing.assert_array_equal(np.asarray(env['native_result']['task_inputs']['error']),np.asarray(c['task_inputs']['error']))
native=np.clip(env['action'][12:23],E.u[t-1].astype(np.float32)-np.float32(.055),E.u[t-1].astype(np.float32)+np.float32(.055)).astype(np.float32)
np.testing.assert_array_equal(native,np.asarray(metadata['context']['parent_command'],np.float32))
# Run the entire generated auditor's command chain loop, not only its final
# replacement statements. Actual previous stays u172; u173 here is explicitly
# an unissued output fixture stored in memory, never written as a trajectory.
source=W/'audit_front_corridor_midpoint_stage_self_clearance.py';tree=ast.parse(source.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.target)=='c' and ast.unparse(n.iter)=='coordinates');program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<entire actual self-clearance command chain loop>','exec')
from audit_front_corridor_midpoint_stage_self_clearance import near,bounded_damped_step,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
c=dict(c,step=t);c['front_loaded_z_priority']=metadata
base=dict(np=np,near=near,bounded_damped_step=bounded_damped_step,U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,count=1200,failure=None,verified_events={},verified_front_events={},q={t:E.q[t].astype(np.float32)},u={t:np.asarray(command,np.float32),t-1:E.u[t-1].astype(np.float32)},lo=lo,hi=hi,limits=np.r_[.015,np.full(10,.04)],fk=lambda q:q,gap=E.elbows.gap,terminals={},priority_records={t:metadata},controller_frames=0,overrides=0,intersection_rows=[],coordinates=[c])
exec(program,base);assert base['controller_frames']==1;near(base['target'],command,0)
negative=[]
for label in ['previous_action','upstream_error','parent_command','raw_output','normal_task_dropped']:
 test=dict(base);test['coordinates']=[copy.deepcopy(c)];test['u']={k:v.copy() for k,v in base['u'].items()};test['priority_records']={t:copy.deepcopy(metadata)};test['controller_frames']=0
 if label=='previous_action':test['u'][t-1][0]+=.001
 elif label=='upstream_error':test['coordinates'][0]['task_inputs']['error'][0]+=.001
 elif label=='parent_command':test['priority_records'][t]['context']['parent_command'][0]+=.001
 elif label=='raw_output':test['u'][t][0]+=.001
 else:
  test['coordinates'][0]['task_inputs']['jacobian']=test['coordinates'][0]['task_inputs']['jacobian'][:6];test['coordinates'][0]['task_inputs']['error']=test['coordinates'][0]['task_inputs']['error'][:6]
 try:exec(program,test)
 except (AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError(('corruption accepted',label))
sources=dict(bound['source_sha256'])
for p in [Path(__file__),source,S/'collect_paired_sorting.py',S/'waist_coordination_clearance.py',D/'SINGLE_STEP_JOINT_PROPOSAL_CHECK.json',W/'FRONT_CORRIDOR_MIDPOINT_COMMAND_BRIDGE_CHECK.json']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,step=t,unissued=True,actual_previous_action=True,collector_normal_selection_verified=True,original_native_coordinator_tail_verified=True,entire_upstream_audit_loop_verified=True,negative_cases_rejected=negative,source_sha256=sources,normal_rotation_source='nominal FK, historical runtime wrist quaternion not archived',physical_started=False,full_episode_or_dynamic_path_verified=False,training_ready=False)
with (S/'UPSTREAM_JOINT_CHAIN_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['source_sha256','scope']},indent=2))
