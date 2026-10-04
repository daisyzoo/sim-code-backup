"""Single unissued first-loaded-box proposal through original full joint chain.
Actual step181 observations/current/previous/action Jacobians and normal rows
are retained. The Cartesian finite-preload proposal is hypothetical; no future
observations or physical outcomes are generated, and nothing is admitted.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_material_preload';sys.path[:0]=[str(S),str(W),str(ROOT)]
from material_preload_v2 import MaterialPreload
from audit_front_box_material_preload_rows_v2 import MaterialPreloadAudit
from front_loaded_z_priority_episode_inputs import EpisodeInputs
from audit_front_box_material_z_execution import recorded_rotation,RuntimeGapRepresentation
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from front_loaded_z_priority import FrontLoadedZPriority
from audit_front_loaded_z_priority_record import verify_record
from audit_front_loaded_z_priority_parent import verify_parent,near
from audit_front_loaded_z_priority_applied_row import verify_applied
from front_loaded_z_priority_audit_geometry import sweep
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=S/'JOINT_CHAIN_CHECK.json';assert not out.exists()
ep=W/'front_corridor_midpoint_physical_r1/case_840020/layout_840020_push_box_to_bin'
E=EpisodeInputs(ep);assert E.side=='right'
t=next(t for t,r in E.rows.items() if r['mode']=='top_push' and r.get('cop_slip_following',{}).get('override'));assert t==181
row=copy.deepcopy(E.rows[t]);previous_row=E.rows[t-1];c=copy.deepcopy(E.coords[t]);q=E.q[t];prev=E.u[t-1];guard=ClearanceGuard(ROOT,S)
assert previous_row['mode']!='top_push' and c['contact_normal_tracking'] is not None
with np.load(ep/'parcel_orientation.npz') as z:R=recorded_rotation(z['box'][t]);OR=recorded_rotation(z['mailer'][t])
# Verify archived execution before using its observations as an unissued proposal.
E.R[t]=R;E.OR[t]=OR;E.geometry=RuntimeGapRepresentation(E.geometry)
oldproof=verify_record(**E.arguments(t,c['front_loaded_z_priority']));E.verify_actual_final_guard(t)
f=row['cop_slip_following'];goal=f['diagonal_entry_control']['goal_xy'];assert row['front_diagonal_entry']['selected']
packet=E.packets[t-1];normal=0.
for contact in packet['parcel_contacts']:
 slots=[i for i,x in enumerate(contact['shapes']) if '/parcel_box/' in x]
 if len(slots)!=1 or not any('right_wrist' in x for x in contact['shapes']):continue
 force=np.asarray(contact['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(force@R[:,2])
 if load>.05:normal+=load
assert normal>=.3
previous_xy=np.asarray(previous_row['target_xyz'][:2]);np.testing.assert_allclose(previous_xy,f['previous_command_xy'],atol=2e-6,rtol=0)
event=MaterialPreload().update(enabled=True,selected=True,side='right',mode=row['mode'],route_stage=row['route_stage'],recontacts=row['recontacts'],parent_guard=False,object_xyz=E.xyz[t],object_rotation=R,observed_support_xyz=row['observed_support_xyz'],previous_command_xy=previous_xy,goal_xy=goal,normal_load_n=normal,cop_valid=True,drive_step_m=f['edge_speed']['drive_step_m'])
assert event['override'];parent_xyz=list(row['target_xyz']);event.update(parent_xyz=parent_xyz,emitted_xy=list(event['command_xy']),preserved_cross_axis=None,preserved_z=parent_xyz[2]);row['front_box_material_preload']=event;row['target_xyz']=[*event['command_xy'],parent_xyz[2]]
independent=MaterialPreloadAudit(True,'right');independent.before_row(row);xy=independent.verify(row,object_xyz=E.xyz[t],rotation=R,observed_support=row['observed_support_xyz'],previous=previous_xy,goal=goal,normal_load_n=normal,drive_step_m=f['edge_speed']['drive_step_m'],parent_xy=parent_xyz[:2],diagonal=True);near(xy,row['target_xyz'][:2])
# Preserve all original task rows; change only the active RIGHT position error.
a=copy.deepcopy(c['task_inputs']);error=np.asarray(a['error'],np.float32);original_error=error.copy();assert np.asarray(a['jacobian']).shape==(9,11)
error[3:6]=np.clip(np.float32(.72)*(np.asarray(row['target_xyz'],np.float32)-np.asarray(c['control_point_positions']['right'],np.float32)),np.float32(-.035),np.float32(.035));a['error']=error.tolist();np.testing.assert_array_equal(error[:3],original_error[:3]);np.testing.assert_array_equal(error[6:],original_error[6:])
parent,solved=solve(enabled=True,geometry=guard.geometry,**a);assert solved['accepted']
parent=np.asarray(parent,np.float32);parent[0]=np.clip(parent[0],-.98,.98);parent=np.clip(parent,prev.astype(np.float32)-np.float32(.055),prev.astype(np.float32)+np.float32(.055));parent=np.clip(parent,np.asarray(U1_JOINT_LIMIT_LO)[12:23],np.asarray(U1_JOINT_LIMIT_HI)[12:23]).astype(np.float32)
c.pop('front_loaded_z_priority',None);c.pop('unexecuted_parent_waist_target_rad',None);c.update(task_inputs=a,self_clearance_task=solved,waist_target_rad=float(parent[0]),front_loaded_z_priority_side='right')
expert=dict(E.experts[t],mode='top_push',target_xyz=row['target_xyz'])
parent_proof=verify_parent(coordinate=c,row=row,expert=expert,current=q,previous_actual=prev,parent=parent,side='right',elbows=E.elbows,bounded_solver=E.solver)
command,metadata=FrontLoadedZPriority(guard).refine(step=t,selected=True,row=row,coordinate=c,current=q,previous=prev,parent_command=parent,target_rotation=R,other_xyz=E.oxy[t],other_rotation=OR,other_size=E.size)
final=guard.command(command,q,prev);assert final['accepted'];proof=None
if metadata['applied']:
 c['unexecuted_parent_waist_target_rad']=c['waist_target_rad'];c['waist_target_rad']=float(command[0])
c['front_loaded_z_priority']=metadata
kwargs=E.arguments(t,metadata,unissued_output=command);kwargs.update(coordinate=c,row=row,expert=expert);proof=verify_record(**kwargs)
size=np.maximum(E.size,np.nextafter(np.asarray(E.size,np.float32),np.float32(np.inf)).astype(float));paths={side:sweep(E.geometry.original,E.hand,q,command,side,E.oxy[t],OR,size) for side in ['left','right']};assert all(v['certified'] for v in paths.values())
# Run the exact native coordinator tail on retained measured tasks, then compare
# its bounded/precise solution and collector slew clipping to parent_command.
coordinator=ast.parse((S/'waist_coordination_clearance.py').read_text());fn=next(n for n in coordinator.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step');start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='jac' for v in n.targets));tail=copy.deepcopy(fn.body[start:])
import torch
joints=torch.zeros((1,23),dtype=torch.float32);joints[0,12:23]=torch.tensor(q,dtype=torch.float32)
env=dict(np=np,torch=torch,rows=[torch.tensor(a['jacobian'],dtype=torch.float32)],errors=[torch.tensor(a['error'],dtype=torch.float32)],robot=SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=joints))),joint_ids=list(range(12,23)),waist_preference=c['waist_preference_rad'],waist_limit=1.,bounded=True,clearance_geometry=guard.geometry,previous_command=prev,precise_task_ik=True,action=np.zeros(23,dtype=np.float32),default=np.zeros(23,dtype=np.float32),indices=list(range(12,23)),palms=c['palm_positions'],points=c['control_point_positions'],active_point_offset=c['active_point_offset_local'],anchor={'left':c['inactive_anchor']},state=SimpleNamespace(side='right'),active_support_reference=c['active_support_reference'],normal_record=c['contact_normal_tracking'],yaw_record=c['contact_bout_yaw_tracking'],trace_jacobian=False)
f=ast.FunctionDef(name='native_tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=tail,decorator_list=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<exact native coordinator tail>','exec'),env);native=env['native_tail']();assert not native.get('no_verified_command')
actual=np.clip(env['action'][12:23],prev.astype(np.float32)-np.float32(.055),prev.astype(np.float32)+np.float32(.055));np.testing.assert_array_equal(actual,parent)
# Full independent final-joint reconstruction loop; hypothetical u181 only,
# never changing actual u180 or any raw trajectory.
source=W/'audit_front_box_material_v1_stage_self_clearance.py';tree=ast.parse(source.read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.target)=='c' and ast.unparse(n.iter)=='coordinates');program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<entire native command audit loop>','exec')
from audit_front_box_material_v1_stage_self_clearance import bounded_damped_step
lo=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98
base=dict(np=np,near=near,bounded_damped_step=bounded_damped_step,U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,count=1200,failure=None,verified_events={},verified_front_events={},q={t:q.astype(np.float32)},u={t:np.asarray(command,np.float32),t-1:prev.astype(np.float32)},lo=lo,hi=hi,limits=np.r_[.015,np.full(10,.04)],fk=lambda q:q,gap=E.elbows.gap,terminals={},priority_records={t:metadata},controller_frames=0,overrides=0,intersection_rows=[],coordinates=[c])
exec(program,base);assert base['controller_frames']==1;near(base['target'],command,0)
negative=[]
for label in ['previous_action','upstream_error','parent_command','raw_output','normal_task_dropped']:
 test=dict(base);test['coordinates']=[copy.deepcopy(c)];test['u']={k:v.copy() for k,v in base['u'].items()};test['priority_records']={t:copy.deepcopy(metadata)};test['controller_frames']=0
 if label=='previous_action':test['u'][t-1][0]+=.001
 elif label=='upstream_error':test['coordinates'][0]['task_inputs']['error'][3]+=.001
 elif label=='parent_command':test['priority_records'][t]['context']['parent_command'][0]+=.001
 elif label=='raw_output':test['u'][t][0]+=.001
 else:test['coordinates'][0]['task_inputs']['jacobian']=test['coordinates'][0]['task_inputs']['jacobian'][:6];test['coordinates'][0]['task_inputs']['error']=test['coordinates'][0]['task_inputs']['error'][:6]
 try:exec(program,test)
 except (AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError(('corruption accepted',label))
sources=dict(E.sources)
for p in [Path(__file__),source,S/'collect_paired_sorting.py',S/'waist_coordination_clearance.py',S/'material_preload_v2.py',S/'front_box_material_preload_route_v2.py',S/'front_loaded_z_priority.py',S/'task_ik_precision.py',W/'audit_front_box_material_preload_rows_v2.py']:sources[str(p)]=sha(p)
report=dict(passed=True,scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),step=t,unissued=True,actual_previous_action=True,actual_normal_and_task_rows=True,original_execution_proof=oldproof,parent_proof=parent_proof,material_event=event,new_cartesian_target=row['target_xyz'],original_cartesian_target=parent_xyz,candidate_command=np.asarray(command).tolist(),metadata=metadata,independent_record_proof=proof,native_coordinator_tail_verified=True,entire_command_audit_loop_verified=True,original_final_guard=final,additional_direct_matrix_non_target_paths=paths,negative_cases_rejected=negative,source_sha256=sources,physical_started=False,full_episode_or_dynamic_path_verified=False,training_ready=False)
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,step=t,unissued=True,z_applied=metadata['applied'],negative=len(negative),training_ready=False)))
