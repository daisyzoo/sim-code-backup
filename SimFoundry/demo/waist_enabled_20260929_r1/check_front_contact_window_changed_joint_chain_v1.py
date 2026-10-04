"""Three changed native bout endpoints: task IK and actual post-IK collector chain.
Fixed measured state and original preceding executed action; candidates unissued.
Not subsequent dynamics, whole episode/source audit or training-admission proof.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,json,hashlib,sys,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';D=W/'front_contact_window_preparation_r2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from task_ik_precision import solve
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();guard=ClearanceGuard(ROOT,S)
bout=read(D/'NATIVE_LOADED_BOUT_CHECK_V4.json');assert bout['passed']
for p,h in bout['source_sha256'].items():assert sha(p)==h
selected=[(b['episode'],r) for b in bout['bouts'] for r in b['records'] if r['candidate_mode']!=r['parent_mode']];assert [r['step'] for _,r in selected]==[790,885,981]
# Reuse only actual AST compilation/Tensor adapter definitions, never run old fixtures.
p=W/'check_front_loaded_z_quarter_native_chain_v1.py';module=ast.parse(p.read_text());start=next(n.lineno for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='priority' for t in n.targets));end=next(n.lineno for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='guard' for t in n.targets));definitions=[n for n in module.body if start<=n.lineno<end];tree=ast.parse((S/'collect_paired_sorting.py').read_text());exec(compile(ast.fix_missing_locations(ast.Module(body=definitions,type_ignores=[])),str(p),'exec'),globals())
ep=W/'front_loaded_z_quarter_physical_r2/case_840023/layout_840023_nudge_mailer_to_bin';coords={r['step']:r for r in read(ep/'coordination.json')};original={r['step']:r for r in read(ep/'frontal_bypass.json')['rows']}
with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
records=[]
for name,r in selected:
 t=r['step'];assert name==ep.name;co=coords[t];old=co['front_loaded_z_priority'];tc=co['joint_transport_clearance']['collector_context'];sc=tc['scene'];assert not co.get('terminal_joint_hold') and not co.get('contact_bout_yaw_tracking');assert not any(k in co for k in ['front_initial_center_override','front_recontact_center_override','recontact_pose_override','region_joint_override','joint_edge_refinement']);assert sc['side']=='left'
 for enabled in [False,True]:
  row=copy.deepcopy(r['candidate_native_row'] if enabled else r['parent_native_row']);row['step']=t
  c=copy.deepcopy(co)
  for key in ['front_loaded_z_priority','joint_transport_clearance','joint_transport_unexecuted_parent_waist_target_rad','unexecuted_parent_waist_target_rad']:c.pop(key,None)
  inp=copy.deepcopy(c['task_inputs']);np.testing.assert_array_equal(inp['current'],q[t,12:23]);np.testing.assert_array_equal(inp['previous'],u[t-1,12:23]);errors=[]
  for side in ['left','right']:
   target=row['target_xyz'] if side=='left' else c['inactive_anchor'];errors.extend(np.clip(np.float32(.72)*(np.asarray(target,dtype=np.float32)-np.asarray(c['control_point_positions'][side],dtype=np.float32)),np.float32(-.035),np.float32(.035)).tolist())
  if not enabled:np.testing.assert_array_equal(errors,inp['error'][:6])
  inp['error'][:6]=errors;c['task_inputs']=inp
  command,ik=solve(enabled=True,geometry=guard.geometry,**inp);assert command is not None,(t,enabled,'native IK rejected',ik);c['self_clearance_task']=ik
  command[0]=np.clip(command[0],-.98,.98);a=u[t].copy();a[12:23]=command;c['waist_target_rad']=float(command[0])
  a=np.clip(a,u[t-1]-np.float32(.055),u[t-1]+np.float32(.055));a=np.clip(a,np.asarray(U1_JOINT_LIMIT_LO),np.asarray(U1_JOINT_LIMIT_HI));a[12]=np.clip(a[12],-1.,1.);a=a.astype(np.float32)
  if not enabled:np.testing.assert_array_equal(a[12:23],old['context']['parent_command'])
  xyz={k:np.asarray(sc[v],np.float32) for k,v in [('mailer','target_xyz'),('box','other_xyz')]};quat={k:np.asarray(sc[v],np.float32) for k,v in [('mailer','target_quat'),('box','other_quat')]};scene={n:NS(data=NS(root_quat_w=Tensor(quat[k][None]))) for n,k in [('parcel_box','box'),('mailer','mailer')]}
  env=dict(args=NS(front_loaded_z_priority=True,front_loaded_z_quarter=True,joint_transport_clearance=True),front_loaded_z_priority_controller=None,joint_transport_controller=None,clearance_guard=guard,default=np.zeros(23,np.float32),front_initial_runtime=NS(center_local=np.asarray(c['active_support_reference']['center_local'])),front_recontact_runtime=None,frontal_log=[row],coordination_log=[c],front_loaded_z_priority_log=[],joint_transport_log=[],side='left',step=t,robot=NS(data=NS(joint_pos=Tensor(q[t][None]))),ordered_ids=list(range(23)),previous=u[t-1].copy(),action=a.copy(),env=NS(scene=scene),parcel_xyz=lambda unused,actor:xyz['box' if actor=='parcel_box' else 'mailer'],obstacle_size=sc['other_size'],edge_size=sc['core_size'],parameters=dict(tasks={'nudge_mailer_to_bin':dict(decay=tc['decay'])}),task_id='nudge_mailer_to_bin',qs=[q[t-1].copy()],clearance_rows=[],clearance_failure=None,reached_after_final_guard=False,ROOT=ROOT,STAGE=S,np=np)
  exec(program,env);accepted=bool(env['reached_after_final_guard'] and env['clearance_failure'] is None)
  if not enabled:assert accepted;np.testing.assert_array_equal(env['action'][12:23],u[t,12:23])
  if accepted:np.testing.assert_array_equal(env['previous'],env['action']);np.testing.assert_array_equal(env['action'][:12],u[t,:12])
  else:np.testing.assert_array_equal(env['previous'],u[t-1])
  record=dict(step=t,enabled=enabled,accepted=accepted,native_ik=ik,command=env['action'][12:23].tolist(),change_from_original_max_rad=float(np.max(abs(env['action'][12:23]-u[t,12:23]))),priority=env['front_loaded_z_priority_log'],transport=env['joint_transport_log'],final_guard=env['clearance_rows'],failure=env['clearance_failure'],unissued=True);records.append(record);print(json.dumps({k:record[k] for k in ['step','enabled','accepted','change_from_original_max_rad']}),flush=True)
source_files=[Path(__file__),p,D/'NATIVE_LOADED_BOUT_CHECK_V4.json',ep/'coordination.json',ep/'frontal_bypass.json',ep/'raw.npz',*[p for p in S.iterdir() if p.is_file()]]
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=all(r['accepted'] for r in records),cases=records,source_sha256={str(p):sha(p) for p in source_files},native_parent_commands_exact=True,physics_verified=False,training_ready=False)
with (D/'CHANGED_JOINT_CHAIN_CHECK_V1.json').open('x') as f:json.dump(report,f,indent=2)
print('ALL_ACCEPTED',report['passed'])
