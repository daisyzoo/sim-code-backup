"""Actual staged CLI, controller transition AST, reference and bounded solver checks."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,json,hashlib,ast,types,io,contextlib,importlib.util,pickle,copy,unittest
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_center';sys.path[:0]=[str(root),str(repo)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text())
for name,h in manifest['candidate_sha256'].items():assert sha(stage/name)==h
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
module=types.ModuleType('isaaclab.app');module.AppLauncher=AppLauncher;sys.modules[module.__name__]=module
base=json.loads((root/'normal_contact_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/contact_center_no_output'];flag='--expert-top-contact-center-calibration';cases=[('off',base,True),('on',base+[flag],True)]
for label,removed in [('no_normal','--expert-top-contact-normal-hold'),('no_projected','--expert-top-projected-support'),('no_guarded','--expert-frontal-top-guarded-descent'),('no_force','--trace-solved-contact-forces'),('no_bounded','--bounded-coupled-ik')]:
 assert removed in base;cases.append((label,[x for x in base if x!=removed]+[flag],False))
cases.append(('corner_conflict',base+[flag,'--expert-frontal-top-visible-corner'],False));cli=[]
for label,args,expected in cases:
 sys.argv=['candidate',*args];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'actual_center_parser','exec'),{'__file__':str(repo/'scripts/collect_paired_sorting.py')})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue());cli.append(dict(case=label,accepted=accepted))
from simfoundry.data.projected_support_reference import projected_support_reference as original_reference
for name in ['projected_support_reference','contact_center_calibration']:
 spec=importlib.util.spec_from_file_location('simfoundry.data.'+name,stage/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian
from simfoundry.data.contact_center_calibration import ContactCenterCalibration,apply_contact_center_step
from simfoundry.data.top_contact_bypass import TopContactBypassState,support_mesh
from simfoundry.data.front_top_route import FrontTopRouteState
from simfoundry.data.frontal_bypass import FrontalBypassState
# Execute the existing projected-support tests against the staged module.
suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_projected_support_reference');result=unittest.TextTestRunner(stream=sys.stdout).run(suite);assert result.wasSuccessful()
# Reuse independent FK/finite-difference robot API and actual current solver.
setup=(root/'check_staged_contact_normal.py').read_text();a=setup.index('# Load only actual literal joint metadata');b=setup.index("ep=root/'terminal_hold_front09")
setup_scope=dict(__file__=str(__file__),root=root,repo=repo,stage=root/'staged_contact_normal',np=np,NS=NS,sys=sys,types=types,ast=ast,json=json,importlib=__import__('importlib'),Rotation=Rotation)
exec('import torch\n'+setup[a:b],setup_scope);transform=setup_scope['transform'];robot_at=setup_scope['robot_at'];solver=setup_scope['live']
ep=root/'normal_contact_groups_r1/case_62013/layout_62013_nudge_mailer_to_bin';front_data=json.loads((ep/'frontal_bypass.json').read_text());front={r['step']:r for r in front_data['rows']};coord={r['step']:r for r in json.loads((ep/'coordination.json').read_text())}
with np.load(ep/'raw.npz') as z:qs=z['q'].copy()
with np.load(ep/'trace.npz') as z:tr={k:z[k].copy() for k in z.files}
with np.load(ep/'parcel_orientation.npz') as z:ori={k:z[k].copy() for k in z.files}
mesh=np.asarray(support_mesh()['left']);shadow=json.loads((ep/'CONTACT_CENTER_CALIBRATION_SHADOW.json').read_text());center=np.array(shadow['proposed_local_center']);q=qs[106,12:].astype(float);mat=transform('left',q);n=Rotation.from_quat(ori['mailer'][106]).as_matrix()[:,2]
for t in [101,106,178,179]:
 rot=transform('left',qs[t,12:])[:3,:3];a=original_reference(mesh,rot,n);b=projected_support_reference(mesh,rot,n)
 for k in a:np.testing.assert_array_equal(a[k],b[k])
# Correct Jacobian of the calibrated tangent reference, independent finite differences.
rng=np.random.default_rng(931);jl=rng.normal(size=(3,11));jw=rng.normal(size=(3,11));ref=projected_support_reference(mesh,mat[:3,:3],n,center_local=center);jac=projected_support_jacobian(jl,jw,mat[:3,:3],ref);fd=np.empty_like(jac);eps=1e-7
for j in range(11):
 values=[]
 for sign in [-1,1]:
  rot=Rotation.from_rotvec(sign*eps*jw[:,j]).as_matrix()@mat[:3,:3];r=projected_support_reference(mesh,rot,n,center_local=center);values.append(sign*eps*jl[:,j]+rot@r['reference_local'])
 fd[:,j]=(values[1]-values[0])/(2*eps)
assert np.max(abs(fd-jac))<1e-6

def state():
 rear=FrontalBypassState(copy.deepcopy(front_data['plan']))
 st=FrontTopRouteState(rear,'left',tuple(front_data['plan']['top_recontact']['contact_size_xyz']),obstacle_size=(.14,.09,.045),route_clearance_m=.012,recover_clearance=True,confirm_nominal_clearance=True,recovery_hysteresis_m=.0005,object_relative_lead=True,recontact_travel_z=.86,guarded_descent=True,continuous_drag=True,front_inset_fraction=.9,tilt_recontact_rad=.03,confirm_terminal_release=True)
 st.top_mode='top_push';st.mode='top_push';st.recontacts=0;st.command=tuple(front[106]['target_xyz']);st.push_x_anchor=.4;st.relative_contact_anchor=(.01,.02);st.load.desired_n=5.;return st

def calibration():
 c=ContactCenterCalibration(mesh);c.pending=center.copy();return c
row=copy.deepcopy(front[106]);reference={k:np.array(v) for k,v in row['projected_support_reference'].items()};st=state();c=calibration()
common=dict(vertices=mesh,hand_xyz=mat[:3,3],hand_rotation=mat[:3,:3],object_xyz=tr['mailer'][106],object_quat=ori['mailer'][106],reference=reference)
new,newref,info=apply_contact_center_step(st,row,c,{'ready':True},**common)
point=mat[:3,3]+mat[:3,:3]@newref['reference_local'];np.testing.assert_allclose(new['target_xyz'][:2],point[:2],atol=1e-12);assert new['target_xyz'][2]==.86
assert st.mode==st.top_mode=='top_lift' and st.front_inset_fraction==1 and st.recontacts==1 and st.push_x_anchor is None and st.relative_contact_anchor is None
assert new['contact_load']['applied_z_bias_m']==0 and st.load.bias_m==0 and info['committed_now'];assert np.linalg.norm(info['reference_switch_world_delta_m'])>.02
# Guard/release and already calibrated cases preserve output/state exactly.
for mode in ['front_guard_lift','top_lift','top_release']:
 ss=state();cc=calibration();rr=dict(row,mode=mode);before=pickle.dumps(ss);out,r,ii=apply_contact_center_step(ss,rr,cc,{'ready':True},**common);assert out is rr and r is reference and before==pickle.dumps(ss) and cc.center_local is None
before=pickle.dumps(st);out,r,ii=apply_contact_center_step(st,new,c,{'ready':False},**dict(common,reference=newref));assert out is new and before==pickle.dumps(st)
ss=state();cc=ContactCenterCalibration(mesh);out,_,ii=apply_contact_center_step(ss,row,cc,{'ready':False},**common);assert out['mode']=='top_press' and ss.command is None and ii['waiting_for_contact_center'];np.testing.assert_allclose(out['target_xyz'][:2],row['parcel_top_xyz'][:2])
# Re-run the actual front guard at the recorded failure, with a ready proposal.
ss=state();ss.route_report=copy.deepcopy(front_data['plan']['front_route_candidates']);ss.route_x=next(r['waypoints_xy'][1][0] for r in ss.route_report['candidates'] if r['route']=='front')-.003
f=front[179];rr=ss.update((0,0,0),tr['mailer'][179],tr['box'][179],.075,.07,tip=f['observed_support_xyz'],quat=ori['mailer'][179],obstacle_quat=ori['box'][179],control_offset_local=f['control_offset_local'],load_n=0.,hand_obstacle_gap_m=f['hand_obstacle_gap_m'])
assert rr['mode']=='front_guard_lift' and rr['route_stop_reason']=='front_corridor_no_table_margin'
cc=calibration();before=pickle.dumps(ss);out,_,ii=apply_contact_center_step(ss,rr,cc,{'ready':True},**common);assert out is rr and before==pickle.dumps(ss) and cc.center_local is None
# Actual collector measurement block: previous solved packet, current pose.
measurement_block=next(node for node in ast.walk(tree) if isinstance(node,ast.If) and ast.unparse(node.test)=='contact_center_calibration is not None' and any(isinstance(v,ast.Attribute) and v.attr=='observe' for v in ast.walk(node)))
measurement_code=compile(ast.Module(body=[measurement_block],type_ignores=[]),'actual_collector_contact_measurement','exec')
control={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};packets={r['after_action_step']:r for r in json.loads((ep/'solved_contact_forces.json').read_text())['rows']}
measured_calibration=ContactCenterCalibration(mesh);measurement_rows=[]
for t in range(101,107):
 m=transform('left',qs[t,12:]);ms=dict(np=np,contact_center_calibration=measured_calibration,solved_contact_forces=[packets[t-1]],step=t,frontal_state=NS(top_mode=control[t-1]['mode']),side='left',target_actor='mailer',robot=robot_at(qs[t,12:]),hands={'left':1,'right':2},hand_quat=Rotation.from_matrix(m[:3,:3]).as_quat(),target_quat=ori['mailer'][t],env=None,parcel_xyz=lambda env,actor,t=t:tr['mailer'][t])
 exec(measurement_code,ms);measurement_rows.append(dict(step=t,**ms['center_measurement']))
assert measurement_rows[-1]['ready'] and all(not r['ready'] for r in measurement_rows[:-1]);np.testing.assert_allclose(measured_calibration.pending,center,atol=1e-7)
# Execute the actual collector transition block, including point/log binding.
block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='contact_center_calibration is not None and projected_support_context is not None')
scope=dict(np=np,contact_center_calibration=measured_calibration,projected_support_context=row['projected_support_reference'],frontal_state=state(),waypoint=copy.deepcopy(row),center_measurement=ms['center_measurement'],support_mesh=support_mesh,side='left',robot=robot_at(q),hands={'left':1,'right':2},env=None,target_actor='mailer',parcel_xyz=lambda env,actor:tr['mailer'][106],target_quat=ori['mailer'][106],reference=reference,point_kwargs={'control_offset_local':reference['reference_local']},contact_center_log=[],step=106)
from simfoundry.data.top_contact_bypass import rotation_xyzw
scope.update(rotation_xyzw=rotation_xyzw,hand_quat=Rotation.from_matrix(mat[:3,:3]).as_quat())
exec(compile(ast.Module(body=[block],type_ignores=[]),'actual_collector_center_transition','exec'),scope)
np.testing.assert_allclose(scope['point_kwargs']['control_offset_local'],scope['waypoint']['control_offset_local']);np.testing.assert_allclose(scope['projected_support_context']['center_local'],center);assert scope['contact_center_log'][0]['committed_now']
action=np.zeros(23);solver(scope['robot'],scope['hands'],action,state=NS(side='left',last_target_xyz=scope['waypoint']['target_xyz']),anchor={'right':coord[106]['inactive_anchor']},default=np.zeros(23),waist_limit=1.,bounded=True,active_point_offset=scope['point_kwargs']['control_offset_local'],active_support_reference=scope['projected_support_context'],active_normal_anchor_local=coord[106]['contact_normal_tracking']['target_local_up'],trace_jacobian=True)
assert np.max(abs(action[12:]-q))<=.04000001 and abs(action[12]-q[0])<=.01500001 and not action[:12].any()
for path,h in manifest['source_sha256'].items():assert sha(path)==h,path
out=dict(cli=cli,original_projection_tests=result.testsRun,default_reference_exact_four_poses=True,calibrated_jacobian_max_error=float(np.max(abs(fd-jac))),actual_transition_ast=True,actual_measurement_ast_rows=measurement_rows,commit_lift_xy_matches_new_actual_reference=True,guards_release_and_latched_no_mutation=True,actual_front_guard_precedence=True,uncalibrated_push_returns_to_press=True,bounded_solver_command_limit_passed=True,candidate_sha256=manifest['candidate_sha256'],checker_sha256=sha(__file__),scope='Actual staged parser/transition AST, calibrated reference math and current bounded solver with independent URDF observation API. No live Isaac or physical data approval. Full state update/measurement timing and changed path still require separate verification.',training_ready=False)
(stage/'WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
