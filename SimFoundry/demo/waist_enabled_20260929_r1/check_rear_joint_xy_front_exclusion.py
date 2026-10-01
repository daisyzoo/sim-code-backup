"""Actual collector AST selection/hook/update with both tasks and raw prior COP."""
from pathlib import Path
import ast,types,copy,json,hashlib,sys
import numpy as np
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom,UsdPhysics,Gf
w=Path(__file__).resolve().parent;stage=w/'staged_rear_joint_xy';repo=w.parents[1];sys.path[:0]=[str(stage),str(repo)]
from front_cop_route import FrontCopRouteState
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
from simfoundry.data.top_contact_load_geometry import loaded_forward_margin
from simfoundry.data.contact_load_control import hand_target_vertical_load
from simfoundry.data.tabletop_route_candidates import footprint_radii
source=stage/'collect_paired_sorting.py';tree=ast.parse(source.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selection=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='front_route_selected' and 'from simfoundry.data.front_top_route import FrontTopRouteState' in ast.unparse(n))
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_cop_slip_following and front_route_selected')
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='waypoint' for t in n.targets) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='frontal_state.update')
def execute(node,ns):exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
checks=[]
for cid,task in [(840001,'nudge_mailer_to_bin'),(840004,'push_box_to_bin')]:
 ep=w/'rear_core_slice_groups_r1'/f'case_{cid}/layout_{cid}_{task}';fr=json.loads((ep/'frontal_bypass.json').read_text());cfg=json.loads((ep.parent/'provenance.json').read_text())['args'];cfg['rear_coupled_progress']=True;key='box' if 'push_box' in task else 'mailer';other='mailer' if key=='box' else 'box';side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer';other_actor='mailer' if key=='box' else 'parcel_box';size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);osize=np.array([.15,.145,.04] if key=='box' else [.14,.09,.045])
 core_size=size*np.array([.96,.96,1.] if key=='box' else [.9,.88,1.])
 usd=Usd.Stage.CreateInMemory();root='/World/envs/env_0/'+actor;UsdGeom.Xform.Define(usd,root);cube=UsdGeom.Cube.Define(usd,root+'/geometry/mesh');cube.GetSizeAttr().Set(1.);UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3d(*core_size));UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
 stub=types.ModuleType('isaaclab.sim.utils.stage');stub.get_current_stage=lambda:usd;sys.modules['isaaclab.sim.utils.stage']=stub
 env=types.SimpleNamespace(scene={actor:types.SimpleNamespace(cfg=types.SimpleNamespace(spawn=types.SimpleNamespace(size=tuple(core_size))))})
 for selected,enabled,phase,axis,drive,edge in [(True,False,False,False,.001,False),(True,True,False,False,.001,False),(True,True,True,False,.001,False),(True,True,True,True,.001,False),(True,True,True,True,.002,False),(True,True,True,True,.003,False),(False,True,True,True,.002,False),(True,True,True,True,.002,True),(False,True,True,True,.002,True)]:
  args=types.SimpleNamespace(**dict(cfg,front_cop_slip_following=enabled,front_cop_phase_anchor=phase,front_cop_route_axis=axis,front_cop_drive_step_m=drive,front_cop_edge_speed=edge));ns=dict(np=np,side=side,env=env,target_size=size,args=args,front_route_selected=selected,obstacle_size=osize,frontal_plan={},top_cls=object,top_extra={});execute(selection,ns)
  assert 'rear_coupled_progress' not in ns['frontal_plan']
  if not selected:assert ns['top_cls'] is object and ns['top_extra']=={} and ns['frontal_plan']=={}
  elif not enabled:assert ns['top_cls'] is FrontTopRouteState and 'cop_drive_step_m' not in ns['top_extra'] and 'front_cop_slip_following' not in ns['frontal_plan']
  else:
   assert ns['top_cls'] is FrontCopRouteState and ns['top_extra']['cop_drive_step_m']==drive
   p=ns['frontal_plan']['front_cop_slip_following'];assert p['drive_step_m']==drive and p['feedback_gain']==.05 and p['max_step_m']==.003 and p['max_reference_lead_m']==.03
   assert bool(ns['top_extra'].get('route_axis_only'))==axis and bool(ns['top_extra'].get('reset_cop_on_route_change'))==phase
  if selected and edge:
   assert ns['top_extra']['edge_speed_enabled'] and np.max(abs(np.array(ns['top_extra']['edge_core_size'])-core_size))<1e-7
   assert ns['frontal_plan']['front_cop_slip_following']['edge_speed']['enabled']
  checks.append(dict(episode=ep.name,edge_enabled=edge,check='actual_selection',selected=selected,cop_enabled=enabled,phase=phase,axis=axis,drive_m=drive))
 args=types.SimpleNamespace(**dict(cfg,front_cop_drive_step_m=.002,front_cop_edge_speed=True));ns=dict(np=np,side=side,env=env,target_size=size,args=args,front_route_selected=True,obstacle_size=osize,frontal_plan={});execute(selection,ns)
 state=ns['top_cls'](FrontalBypassState(fr['plan'],staging_z=.92,press_z=.822,feedback_rear_endpoint=True,follow_target_y=True),side,tuple(size),**ns['top_extra'],guarded_descent=True,continuous_drag=True,drag_step_m=.003,alignment_tolerance_m=.01,tilt_recontact_rad=.03,confirm_terminal_release=True,front_inset_fraction=.9);state.load.desired_n=5.
 with np.load(ep/'trace.npz') as z:tr={k:z[k] for k in z.files}
 with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k] for k in z.files}
 packets={p['after_action_step']:p for p in json.loads((ep/'solved_contact_forces.json').read_text())['rows']};count=0;reduced=0
 for row in fr['rows']:
  t=row['step'];packet=packets.get(t-1);kw=dict(tip=row['observed_support_xyz'],quat=ori[key][t],obstacle_quat=ori[other][t],control_offset_local=row.get('control_offset_local') or (.2,0,.007),load_n=hand_target_vertical_load(packet,side,actor),hand_obstacle_gap_m=row['hand_obstacle_gap_m']);positions={actor:tr[key][t],other_actor:tr[other][t]}
  callns=dict(args=args,front_route_selected=True,solved_contact_forces=[] if packet is None else [packet],side=side,target_actor=actor,obstacle_actor=other_actor,env=None,parcel_xyz=lambda env,a:positions[a],target_quat=ori[key][t],obstacle_quat=ori[other][t],frontal_state=state,point_kwargs=kw,robot=None,hands={side:side},palm_xyz=lambda robot,hand:tr['palm_'+side][t],target_size=size,obstacle_size=osize,extent_x_from_quat=lambda sz,q:footprint_radii(sz,q)[0]);execute(hook,callns);contact=kw['slip_contact']
  points=[];weights=[];rot=Rotation.from_quat(ori[key][t]).as_matrix()
  if packet:
   assert np.max(abs(np.array(packet['post_action_pose'][key])-tr[key][t]))<1e-6
   for c in packet['parcel_contacts']:
    slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
    if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
    force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rot[:,2])
    if normal>.05:points.append(c['position_world']);weights.append(normal)
  assert contact['valid']==bool(weights) and abs(contact['normal_load_n']-sum(weights))<1e-5
  if weights:assert np.max(abs(np.array(contact['weighted_contact_local'])-rot.T@(np.average(points,axis=0,weights=weights)-tr[key][t])))<1e-7
  execute(call,callns);out=callns['waypoint'];f=out['cop_slip_following']
  if f['override']:
   gy=out['clearance_progress']['front_hold_y'] if out['route_stage']=='front_x' else state.route_report['goal_y'];error=np.array([out['route_goal_x'],gy])-tr[key][t,:2];distance=np.linalg.norm(error);half=core_size[:2]/2;local=np.array(contact['weighted_contact_local']);axis=0 if out['route_stage']=='front_x' else 1;sign=-1 if axis==0 or side=='right' else 1;ray=sign*rot[axis];ends=[((half[j] if ray[j]>0 else -half[j])-local[j])/ray[j] for j in range(2) if abs(ray[j])>1e-10] if np.all(abs(local[:2])<=half) else [];edge_distance=max(0,min(ends)) if ends else 0;step=.001+.001*min(1,edge_distance/.01);drive=error*min(step,distance)/distance if distance else np.zeros(2);assert np.max(abs(drive-f['drive_xy']))<1e-9;count+=1;reduced+=step<.002-1e-10
   checks.append(dict(episode=ep.name,check='actual_hook_and_update',step=t,drive_norm_m=float(np.linalg.norm(f['drive_xy'])),normal_load_n=contact['normal_load_n']))
   if count>=3 and reduced>=3:break
 assert count>=3 and reduced>=3
 for enabled,selected in [(False,True),(True,False)]:
  off=dict(callns,args=types.SimpleNamespace(front_cop_slip_following=enabled),front_route_selected=selected,point_kwargs={});execute(hook,off);assert off['point_kwargs']=={}
  checks.append(dict(episode=ep.name,check='inactive_hook',enabled=enabled,selected=selected))
out=dict(passed=True,checks=checks,collector_sha256=sha(source),wrapper_sha256=sha(stage/'front_cop_route.py'),helper_sha256=sha(stage/'contact_slip_following.py'),edge_helper_sha256=sha(stage/'front_edge_speed.py'),checker_sha256=sha(Path(__file__)),scope='Actual collector AST18selectionfixtures using actual USD collision reader, real prior contact hook and full update through3reduced drive steps per class; independent raw COP/core-edge drive math and4inactive hook checks. No physics or efficacy claim.',training_ready=False)
p=stage/'FRONT_COLLECTOR_WIRING_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print('PASSED',len(checks))
