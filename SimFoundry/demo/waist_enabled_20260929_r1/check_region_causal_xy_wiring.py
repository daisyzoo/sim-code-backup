"""Actual collector selection/hook/override AST with explicit USD/torch fixtures."""
from pathlib import Path
import sys,types,ast,json,hashlib,copy
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom,UsdPhysics,Gf
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_region_causal_xy_response';sys.path[:0]=[str(stage),str(repo)]
from region_approach_lifecycle import RegionApproachLifecycle
from region_top_contact import TopContactBypassState
from articulated_hand_geometry import ArticulatedHandGeometry
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
selection=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.region_top_approach and ') and 'RegionApproachLifecycle' in ast.unparse(n))
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='region_approach is not None and projected_support_context is not None')
override=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'region_step.get' in ast.unparse(n.test) and 'joint_override' in ast.unparse(n.test))
execute=lambda node,ns:exec(compile(ast.Module(body=[node],type_ignores=[]),str(stage/'collect_paired_sorting.py'),'exec'),ns)
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');fit=json.loads((stage/'causal_response_parameters.json').read_text());history=json.loads((w/'causal_xy_objective_screen_r1/RESULT.json').read_text());cases=[r for r in history['rows'] if r['variant']=='response_centered_xy_objective'];assert len(cases)==20;reports=[];negative=[]
for ci,case in enumerate(cases):
 ep=Path(case['episode']);t=case['actual_start_frame'];task='push_box_to_bin' if 'push_box' in ep.name else 'nudge_mailer_to_bin';side='right' if task=='push_box_to_bin' else 'left';key='box' if side=='right' else 'mailer';other='mailer' if key=='box' else 'box';actor='parcel_box' if key=='box' else 'mailer';other_actor='mailer' if key=='box' else 'parcel_box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);scale=np.array([.96,.96,1.] if key=='box' else [.90,.88,1.])
 # Scale must match archived actual generator, not a free test convenience.
 cfg=ast.parse((ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py').read_text());node=next(n for n in ast.walk(cfg) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));assert np.array_equal(scale,np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body)))
 with np.load(ep/'raw.npz') as z:rawq=z['q'].astype(float);rawu=z['action'].astype(float)
 with np.load(ep/'trace.npz') as z:target=z[key][t].astype(float);obstacle=z[other][t].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key][t].astype(float);oquat=z[other][t].astype(float)
 plan=json.loads((ep/'frontal_bypass.json').read_text())['plan'];coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};anchor=coord[t]['inactive_anchor'];inactive='left' if side=='right' else 'right'
 usd=Usd.Stage.CreateInMemory();root='/World/envs/env_0/'+actor;UsdGeom.Xform.Define(usd,root);cube=UsdGeom.Cube.Define(usd,root+'/geometry/mesh');cube.GetSizeAttr().Set(1.);UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3d(*(size*scale)));UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
 stub=types.ModuleType('isaaclab.sim.utils.stage');stub.get_current_stage=lambda:usd;sys.modules['isaaclab.sim.utils.stage']=stub
 scene={actor:types.SimpleNamespace(cfg=types.SimpleNamespace(spawn=types.SimpleNamespace(size=tuple(size*scale))))};env=types.SimpleNamespace(scene=scene)
 for mode in (['actual_start','model_handover'] if ci<8 else ['model_handover']):
  if mode=='actual_start':q=rawq[t,12:23];prevq=rawq[t-1,12:23];prevu=rawu[t-1,12:23]
  else:q=np.array(case['history'][-1]['measured_q']);prevq=np.array(case['history'][-2]['measured_q']);prevu=np.array(case['history'][-1]['previous_command'])
  q=q.astype(np.float32);bodies=[];rotations=[]
  for hand in ['left','right']:
   T,_,_=model.fk(hand,q);bodies.append(T[:3,3]);rotations.append(Rotation.from_matrix(T[:3,:3]).as_quat())
  wrap=lambda v:types.SimpleNamespace(torch=torch.tensor(np.asarray(v)[None],dtype=torch.float32));robot=types.SimpleNamespace(data=types.SimpleNamespace(joint_pos=wrap(np.r_[np.zeros(12),q]),body_pos_w=wrap(bodies),body_quat_w=wrap(rotations)))
  args=types.SimpleNamespace(region_top_approach=True,region_causal_response=True,region_causal_xy_response=True,waist_limit_rad=1.);ns=dict(args=args,front_route_selected=False,initial_top_selected=False,side=side,env=env,target_size=size,task_id=task,ROOT=repo,STAGE=stage,np=np,json=json,hashlib=hashlib,frontal_plan={});execute(selection,ns);life=ns['region_approach'];assert np.allclose(life.preferred_core_scale,scale,atol=1e-7,rtol=0);assert np.array_equal(life.causal_decay,fit['tasks'][task]['decay'])
  state=ns['top_cls'](FrontalBypassState(plan,staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,tuple(size),guarded_descent=True,continuous_drag=True,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,hold_established_x=True);state.load.desired_n=5.;state.top_mode='top_cross'
  geom=model.scene_geometry(side,q,target_xyz=target,target_quat=quat,other_xyz=obstacle,other_quat=oquat,other_size=osize);ref=projected_support_reference(geom['vertices'],geom['hand_rotation'],geom['target_rotation'][:,2]);tip=geom['hand_xyz']+geom['hand_rotation']@ref['reference_local'];waypoint=state.update(tip,target,obstacle,plan['target_radius_x'],plan['obstacle_radius_x'],tip=tip,quat=quat,control_offset_local=ref['reference_local'],load_n=0.,hand_obstacle_gap_m=geom['hand_other_gap_m']);positions={actor:target,other_actor:obstacle}
  ns.update(robot=robot,ordered_ids=list(range(23)),hands={'left':0,'right':1},region_model=model,frontal_state=state,reference=ref,projected_support_context={},previous=np.r_[np.zeros(12),prevu],default=np.zeros(23),qs=[np.r_[np.zeros(12),prevq]],obs={'policy':torch.tensor(np.r_[np.zeros(12),q][None],dtype=torch.float32)},parcel_xyz=lambda env,a:positions[a],target_actor=actor,obstacle_actor=other_actor,target_quat=quat,obstacle_quat=oquat,obstacle_size=osize,U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,inactive_anchor={inactive:anchor},top_contact_normal_anchor=None,load_n=0.,waypoint=waypoint,point_kwargs={},region_log=[],step=t)
  execute(hook,ns);s=ns['region_step'];assert s and s.get('joint_override'),(ci,mode,s);assert s['handover']==(mode=='model_handover');cr=s['causal_response'];assert np.array_equal(cr['previous_q'],prevq) and np.array_equal(cr['previous_command'],prevu) and np.array_equal(cr['current_q'],q.astype(float));a=np.array(cr['decay']);assert np.max(abs(np.array(cr['gain'])-(1-a)))<1e-14;expected_offset=a*q+(q-prevu)-a*(prevq-prevu);assert np.max(abs(np.array(cr['offset'])-expected_offset))<1e-14;assert cr['command_change_damping'] and cr['response_centered_xy_objective']
  ns.update(action=np.full(23,.123),coordination_log=[{'waist_target_rad':.123}]);execute(override,ns);assert np.array_equal(ns['action'][12:23],s['next_q']);assert np.all(ns['action'][:12]==.123)
  reports.append(dict(case=ci,episode=str(ep),fixture=mode,handover=s['handover'],causal_inputs_exact=True,action_override_exact=True,actual_core_scale=life.preferred_core_scale.tolist()))
  if mode=='actual_start':
   ns['region_approach']=RegionApproachLifecycle(causal_decay=life.causal_decay,preferred_core_scale=life.preferred_core_scale);ns['obs']['policy'][0,12]+=.002
   try:execute(hook,ns)
   except ValueError as e:assert 'state ordering' in str(e);negative.append('q_recording_mismatch')
   else:raise AssertionError('Bad observed state accepted')
   ns['obs']['policy'][0,12]-=.002;ns['region_approach']=RegionApproachLifecycle(causal_decay=life.causal_decay,preferred_core_scale=life.preferred_core_scale);ns['qs']=[]
   try:execute(hook,ns)
   except ValueError as e:assert 'previous measured q' in str(e);negative.append('missing_previous_q')
   else:raise AssertionError('Missing previous state accepted')
 offxy=dict(ns,args=types.SimpleNamespace(region_top_approach=True,region_causal_response=True,region_causal_xy_response=False,waist_limit_rad=1.),front_route_selected=False,initial_top_selected=False,region_approach=None,frontal_plan={});execute(selection,offxy);assert offxy['region_approach'].response_centered_xy_objective is False
 # Default disabled and excluded front/initial routes must not enable the new lifecycle.
 for enabled,front,initial in [(False,False,False),(True,True,False),(True,False,True)]:
  off=dict(ns,args=types.SimpleNamespace(region_top_approach=True,region_causal_response=enabled),front_route_selected=front,initial_top_selected=initial,region_approach=None,frontal_plan={});execute(selection,off)
  assert off['region_approach'] is None if front or initial else off['region_approach'].causal_decay is None
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=dict(passed=True,rows=reports,negative_checks=negative,source_sha256={p.name:sha(p) for p in stage.iterdir() if p.suffix in ['.py','.json'] and p.name in ['collect_paired_sorting.py','region_approach_lifecycle.py','contact_patch_approach.py','causal_unloaded_response.py','causal_response_parameters.json']},checker_sha256=sha(__file__),scope='Exact source selection/hook/action AST with explicit in-memory USD Cube (archived core scale) and torch sensor fixtures from real8 initial states and20 model-derived handover states; XY-on record and XY-off factory checked. Stage getter is a fixture, not live Isaac. Current/previous q and previous executed action checked independently; model-handover is not new physics. Default route exclusions kept.',training_ready=False);(stage/'CAUSAL_WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(dict(passed=True,fixtures=len(reports),negative_checks=len(negative)))
