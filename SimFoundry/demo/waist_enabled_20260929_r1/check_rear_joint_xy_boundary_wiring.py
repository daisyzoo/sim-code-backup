"""Boundary perturbations through real collector hook and physical-limit auditor."""
from pathlib import Path
import ast,copy,hashlib,json,sys,types
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom,UsdPhysics,Gf
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_rear_joint_xy';sys.path[:0]=[str(stage),str(repo),str(w)]
from region_approach_lifecycle import RegionApproachLifecycle
from region_top_contact import TopContactBypassState
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
from audit_region_measured_bounds_live import verify_bound_record
from audit_region_causal_xy_live import inspect_geometry
tree=ast.parse((stage/'collect_paired_sorting.py').read_text());selection=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.region_top_approach and ') and 'RegionApproachLifecycle' in ast.unparse(n));hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='region_approach is not None and projected_support_context is not None');override=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'region_step.get' in ast.unparse(n.test) and 'joint_override' in ast.unparse(n.test));execute=lambda n,ns:exec(compile(ast.Module(body=[n],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec'),ns)
chosen=json.loads((w/'staged_measured_bounds_probe/REAL_GEOMETRY_CHECK.json').read_text())['counterfactuals'][0];ep=w/chosen['run']/f"case_840001/{chosen['episode']}";t=chosen['source_step'];fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];size=np.array([.14,.09,.045]);osize=(.15,.145,.04);scale=np.array(plan['region_causal_response']['core_scale']);coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};anchor=coords[t]['inactive_anchor']
with np.load(ep/'raw.npz') as z:rawq=z['q'].astype(float);rawu=z['action'].astype(float)
with np.load(ep/'trace.npz') as z:target=z['box'][t].astype(float);obstacle=z['mailer'][t].astype(float)
with np.load(ep/'parcel_orientation.npz') as z:quat=z['box'][t].astype(float);oquat=z['mailer'][t].astype(float)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');usd=Usd.Stage.CreateInMemory();root='/World/envs/env_0/parcel_box';UsdGeom.Xform.Define(usd,root);cube=UsdGeom.Cube.Define(usd,root+'/geometry/mesh');cube.GetSizeAttr().Set(1.);UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3d(*(size*scale)));UsdPhysics.CollisionAPI.Apply(cube.GetPrim());stub=types.ModuleType('isaaclab.sim.utils.stage');stub.get_current_stage=lambda:usd;sys.modules['isaaclab.sim.utils.stage']=stub;env=types.SimpleNamespace(scene={'parcel_box':types.SimpleNamespace(cfg=types.SimpleNamespace(spawn=types.SimpleNamespace(size=tuple(size*scale))))})
lo=np.array(U1_JOINT_LIMIT_LO)[12:23].copy();hi=np.array(U1_JOINT_LIMIT_HI)[12:23].copy();lo[0]=-.98;hi[0]=.98;ml=lo.copy();mu=hi.copy();ml[0]=-1.;mu[0]=1.;reports=[];negative=[]
for excess in [4.710674285890448e-5,.001,.005]:
 q=rawq[t,12:23].astype(np.float32);q[0]=.98+excess;prevq=rawq[t-1,12:23];prevu=rawu[t-1,12:23];bodies=[];rotations=[]
 for side in ['left','right']:
  T,_,_=model.fk(side,q);bodies.append(T[:3,3]);rotations.append(Rotation.from_matrix(T[:3,:3]).as_quat())
 wrap=lambda v:types.SimpleNamespace(torch=torch.tensor(np.asarray(v)[None],dtype=torch.float32));robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=wrap(np.r_[np.zeros(12),q]),body_pos_w=wrap(bodies),body_quat_w=wrap(rotations)))
 args=types.SimpleNamespace(rear_joint_xy_progress=True,rear_coupled_progress=True,front_cop_drive_step_m=.002,front_cop_edge_speed=True,rear_core_slice_feedback=True,rear_cop_centering=True,region_top_approach=True,region_causal_response=True,region_causal_xy_response=True,region_separate_measured_bounds=True,waist_limit_rad=1.)
 ns=dict(args=args,front_route_selected=False,initial_top_selected=False,side='right',env=env,target_size=size,task_id='push_box_to_bin',ROOT=repo,STAGE=stage,np=np,json=json,hashlib=hashlib,frontal_plan={},top_extra={});execute(selection,ns);life=ns['region_approach'];life.active=True
 state=ns['top_cls'](FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),'right',tuple(size),**ns['top_extra'],guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True);state.load.desired_n=5.;state.top_mode='top_cross'
 geom=model.scene_geometry('right',q,target_xyz=target,target_quat=quat,other_xyz=obstacle,other_quat=oquat,other_size=osize);ref=projected_support_reference(geom['vertices'],geom['hand_rotation'],geom['target_rotation'][:,2]);tip=geom['hand_xyz']+geom['hand_rotation']@ref['reference_local'];waypoint=state.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=ref['reference_local'],load_n=0.,hand_obstacle_gap_m=geom['hand_other_gap_m']);positions={'parcel_box':target,'mailer':obstacle}
 ns.update(robot=robot,ordered_ids=list(range(23)),hands={'left':0,'right':1},region_model=model,frontal_state=state,reference=ref,projected_support_context={},previous=np.r_[np.zeros(12),prevu],default=np.zeros(23),qs=[np.r_[np.zeros(12),prevq]],obs={'policy':torch.tensor(np.r_[np.zeros(12),q][None],dtype=torch.float32)},parcel_xyz=lambda env,a:positions[a],target_actor='parcel_box',obstacle_actor='mailer',target_quat=quat,obstacle_quat=oquat,obstacle_size=osize,U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,inactive_anchor={'left':anchor},top_contact_normal_anchor=None,load_n=0.,waypoint=waypoint,point_kwargs={},region_log=[],step=t)
 execute(hook,ns);s=ns['region_step'];assert s['joint_override'] and not s['handover'];assert not verify_bound_record(s['measured_state_bounds'],q,s['next_q'],lo,hi,ml,mu,joint_override=True,handover=False)
 cr=s['causal_response'];cmd=np.array(s['next_q'])
 for v in [cmd,np.array(cr['gain'])*cmd+cr['offset']]:assert not inspect_geometry(model,'right',v,target,quat,obstacle,oquat,size,osize)['errors']
 ns.update(action=np.full(23,.123),coordination_log=[{'waist_target_rad':.123}]);execute(override,ns);assert np.array_equal(ns['action'][12:23],cmd) and np.all(ns['action'][:12]==.123)
 reports.append(dict(waist_excess_rad=excess,waist_command_rad=cmd[0],actual_hook_inward_command=True,handover=False))
 for kind in ['physical_state','outside_handover','outside_command','declared_physical','declared_command','missing_record']:
  rq=q.copy();rc=cmd.copy();rr=copy.deepcopy(s['measured_state_bounds']);h=False
  if kind=='physical_state':rq[0]=1.001
  elif kind=='outside_handover':h=True
  elif kind=='outside_command':rc[0]=.981
  elif kind=='declared_physical':rr['measured_upper'][0]=1.01
  elif kind=='declared_command':rr['command_upper'][0]=1.
  else:rr={}
  assert verify_bound_record(rr,rq,rc,lo,hi,ml,mu,joint_override=True,handover=h);negative.append(kind)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();out=dict(passed=True,rows=reports,negative_auditor_cases=negative,source_step=t,episode=str(ep),source_sha256={f:sha(ep/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','coordination.json','frontal_bypass.json']},candidate_source_sha256={n:sha(stage/n) for n in ['collect_paired_sorting.py','region_approach_lifecycle.py','contact_patch_approach.py']},auditor_sha256=sha(w/'audit_region_measured_bounds_live.py'),checker_sha256=sha(Path(__file__)),physical_started=False,training_ready=False,scope='Three explicit waist perturbations of a real near-bound geometry through actual collector hook and emitted-action AST using in-memory USD/torch sensors; no real physical recovery. Independent unchanged geometry/command/forecast audit and18 malformed domains/states/commands rejected.')
(stage/'BOUNDARY_WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,boundary_fixtures=len(reports),negative_cases=len(negative)))
