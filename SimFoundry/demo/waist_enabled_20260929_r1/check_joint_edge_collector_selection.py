"""Execute actual collector class-selection and contact-input AST with USD fixtures."""
from pathlib import Path
import ast,hashlib,json,sys,types
import numpy as np
from scipy.spatial.transform import Rotation
from pxr import Usd,UsdGeom,UsdPhysics,Gf
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_joint_edge_command'
sys.path[:0]=[str(stage),str(repo)]
from rear_cop_route import RearCopRouteState
from region_top_contact import TopContactBypassState as RegionParent
source=stage/'collect_paired_sorting.py';tree=ast.parse(source.read_text())
selection=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.region_top_approach and (not front_route_selected) and (not initial_top_selected)')
hook=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.rear_cop_centering and region_approach is not None')
def execute(node,scope):exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin')]:
 ep=w/'region_causal_xy_groups_r2'/f'case_{cid}/layout_{cid}_{task}';key='box' if 'push_box' in task else 'mailer';actor='parcel_box' if key=='box' else 'mailer';side='right' if key=='box' else 'left'
 fr=json.loads((ep/'frontal_bypass.json').read_text());core=fr['plan']['region_causal_response']['actual_core'];size=np.array(fr['plan']['top_recontact']['contact_size_xyz']);core_size=np.array(core['collision_core_size_xyz'])
 usd=Usd.Stage.CreateInMemory();root='/World/envs/env_0/'+actor;UsdGeom.Xform.Define(usd,root);cube=UsdGeom.Cube.Define(usd,root+'/geometry/mesh');cube.GetSizeAttr().Set(1.);UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3d(*core_size));UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
 stub=types.ModuleType('isaaclab.sim.utils.stage');stub.get_current_stage=lambda:usd;sys.modules['isaaclab.sim.utils.stage']=stub
 env=types.SimpleNamespace(scene={actor:types.SimpleNamespace(cfg=types.SimpleNamespace(spawn=types.SimpleNamespace(size=tuple(core_size))))})
 for flag,slice_flag,progress,joint,front,initial in [(True,True,True,False,False,False),(True,True,True,True,False,False),(True,True,False,False,False,False),(True,False,False,False,False,False),(False,False,False,False,False,False),(True,True,True,True,True,False),(True,True,True,True,False,True)]:
  args=types.SimpleNamespace(region_top_approach=True,region_separate_measured_bounds=True,region_causal_response=True,region_causal_xy_response=True,rear_cop_centering=flag,rear_core_slice_feedback=slice_flag,rear_coupled_progress=progress,rear_joint_xy_progress=joint,rear_joint_edge_command=joint,waist_limit_rad=1.)
  ns=dict(args=args,front_route_selected=front,initial_top_selected=initial,side=side,env=env,target_size=size,task_id=task,ROOT=repo,STAGE=stage,np=np,json=json,hashlib=hashlib,frontal_plan={},top_cls=object,top_extra={},region_approach=None)
  execute(selection,ns)
  if front or initial:assert ns['top_cls'] is object and ns['region_approach'] is None and not ns['top_extra']
  elif flag:
   assert ns['top_extra']['rear_core_slice_enabled'] is slice_flag
   assert bool(ns['frontal_plan']['rear_cop_centering'].get('core_slice_feedback',False)) is slice_flag
   assert ns['top_cls'] is RearCopRouteState and ns['top_extra']['rear_cop_enabled'] is True
   assert ns['region_approach'].separate_measured_bounds and ns['frontal_plan']['region_measured_state_bounds']['enabled']
   assert np.max(abs(np.array(ns['top_extra']['rear_cop_core_size'])-core_size))<1e-7
   assert ns['frontal_plan']['rear_cop_centering']['parent_yz_unchanged']
   assert bool(ns['top_extra'].get('rear_coupled_progress_enabled')) is progress
   assert bool(ns['frontal_plan'].get('rear_coupled_progress',{}).get('enabled')) is progress
   assert bool(ns['top_extra'].get('rear_joint_xy_enabled')) is joint
   assert bool(ns['frontal_plan'].get('rear_joint_xy_progress',{}).get('enabled')) is joint
   if joint:
    assert ns['frontal_plan']['rear_joint_edge_command']['requires_joint_xy_override'] and ns['frontal_plan']['rear_joint_edge_command']['first_loaded_preserved']
    cfg=ns['frontal_plan']['rear_joint_xy_progress'];assert cfg['parent_z_unchanged'] and cfg['full_push_ik_trace'] and cfg['core_inset_m']==.01 and cfg['max_x_step_m']==.002 and cfg['max_reference_x_lead_m']==.03 and cfg['infeasible_fallback']=='parent_Y_governor'
   if progress:
    cfg=ns['frontal_plan']['rear_coupled_progress'];assert cfg['parent_xz_unchanged'] and cfg['full_push_ik_trace'] and cfg['core_inset_m']==.01 and cfg['infeasible_fallback']=='preserve_parent'
  else:assert ns['top_cls'] is RegionParent and ns['top_extra']=={} and 'rear_cop_centering' not in ns['frontal_plan']
  rows.append(dict(task=task,flag=flag,slice_flag=slice_flag,front=front,initial=initial,selection_checked=True))
 with np.load(ep/'trace.npz') as z:xyz=z[key].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key].astype(float)
 packets=json.loads((ep/'solved_contact_forces.json').read_text())['rows'];packet_by={p['after_action_step']:p for p in packets}
 sampled=[r['step'] for r in fr['rows'] if r['mode']=='top_push'][::10]
 for t in sampled:
  packet=packet_by[t-1];rot=Rotation.from_quat(quat[t]).as_matrix();points=[];weights=[]
  assert np.max(abs(np.array(packet['post_action_pose'][key])-xyz[t]))<1e-6
  for c in packet['parcel_contacts']:
   slots=[i for i,label in enumerate(c['shapes']) if '/'+actor+'/' in label]
   if len(slots)!=1 or not any(side+'_wrist' in label for label in c['shapes']):continue
   force=np.array(c['force_world_N'])*(1 if slots[0]==1 else -1);normal=-float(force@rot[:,2])
   if normal>.05:weights.append(normal);points.append(rot.T@(np.array(c['position_world'])-xyz[t]))
  ns=dict(args=types.SimpleNamespace(rear_cop_centering=True),region_approach=object(),point_kwargs={},solved_contact_forces=[packet],side=side,target_actor=actor,env=env,parcel_xyz=lambda env,actor:xyz[t],target_quat=quat[t],frontal_state=types.SimpleNamespace(size=tuple(size)))
  execute(hook,ns);contact=ns['point_kwargs']['slip_contact'];assert contact['valid']==bool(weights)
  assert abs(contact['normal_load_n']-sum(weights))<1e-5
  if weights:assert np.max(abs(np.array(contact['weighted_contact_local'])-np.average(points,axis=0,weights=weights)))<1e-7
  for enabled,selected in [(False,True),(True,False)]:
   excluded=dict(ns,args=types.SimpleNamespace(rear_cop_centering=enabled),region_approach=object() if selected else None,point_kwargs={});execute(hook,excluded);assert excluded['point_kwargs']=={}
  rows.append(dict(task=task,step=t,previous_packet_exact=True,measured_cop_independent=True))
report=dict(passed=True,rows=rows,selection_fixtures=14,contact_fixtures=len(rows)-14,
 source_sha256={n:sha(stage/n) for n in ['collect_paired_sorting.py','rear_cop_route.py','rear_cop_centering.py','region_top_contact.py','rear_coupled_progress.py','rear_joint_xy_progress.py']},
 checker_sha256=sha(Path(__file__)),physical_started=False,training_ready=False,
 scope='Actual collector selection/contact hook AST, in-memory USD geometry fixture and real recorded prior contact packets. Front/initial/off exclusion and independent force-weighted COP checked. No Isaac physics or future-contact success claim; actual-command auditor still required.')
(stage/'COLLECTOR_WIRING_CHECK.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['rows','source_sha256']})
