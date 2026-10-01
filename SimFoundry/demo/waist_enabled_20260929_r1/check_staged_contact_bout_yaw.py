"""Actual staged parser/lifecycle and CPU robot-API solver fixtures."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,types,ast,json,hashlib,io,contextlib,importlib.util
import numpy as np,torch
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_bout_yaw';sys.path[:0]=[str(stage),str(repo)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text())
for name,h in manifest['candidate_sha256'].items():assert sha(stage/name)==h
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
base=json.loads((root/'y_path_nearhalf_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/bout_yaw_parser_no_output'];flag='--expert-top-contact-bout-yaw-hold';cli=[]
variants=[('off',base,True),('on',base+[flag],True)]
for missing in ['--expert-top-contact-normal-hold','--expert-top-projected-support','--trace-solved-contact-forces','--bounded-coupled-ik']:
 variants.append(('missing_'+missing,[x for x in base if x!=missing]+[flag],False))
for label,args,expected in variants:
 sys.argv=['candidate',*args];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'staged_parser','exec'),{'__file__':str(repo/'scripts/collect_paired_sorting.py')})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue());cli.append(dict(case=label,accepted=accepted))
# Reuse independently validated CPU robot observation fixture (URDF FK and
# finite-difference spatial Jacobians); no old manifests or old parser execution.
old=(root/'check_staged_contact_normal.py').read_text();fixture=old.split('# Load only actual literal joint metadata, avoiding simulation startup.')[1].split("ep=root/'terminal_hold_front09_groups_r1")[0]
fixture=fixture.replace("stage/'contact_normal_constraint.py'","repo/'simfoundry/data/contact_normal_constraint.py'")
exec(compile(fixture,'<cpu_robot_fixture>','exec'))
spec=importlib.util.spec_from_file_location('simfoundry.data.contact_bout_yaw',stage/'contact_bout_yaw.py');yawmod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=yawmod;spec.loader.exec_module(yawmod)
results=[];first_fixture=None
for ep in sorted((root/'y_path_nearhalf_groups_r1').glob('case_*/layout_*')):
 if not (ep/'quality.json').exists():continue
 side='right' if 'push_box' in ep.name else 'left';inactive='left' if side=='right' else 'right';coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};ctrl={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};push=[t for t,r in ctrl.items() if r['mode']=='top_push']
 if not push:continue
 with np.load(ep/'raw.npz') as z:qs=z['q']
 for t in sorted(set([push[0],push[len(push)//2],push[-1]])):
  c=coords[t];q=qs[t,12:].astype(float);robot=robot_at(q);common=dict(state=NS(side=side,last_target_xyz=ctrl[t]['target_xyz']),anchor={inactive:c['inactive_anchor']},default=np.zeros(23),waist_limit=1.,bounded=True,active_point_offset=c['active_point_offset_local'],active_support_reference=c['active_support_reference'],active_normal_anchor_local=c['contact_normal_tracking']['target_local_up'],trace_jacobian=True);a=np.zeros(23);b=np.zeros(23);live(robot,{'left':1,'right':2},a,**common);off=candidate(robot,{'left':1,'right':2},b,**common);np.testing.assert_allclose(a,b,atol=1e-12,rtol=0);assert off['contact_bout_yaw_tracking'] is None
  rot=transform(side,q)[:3,:3];ys=yawmod.ContactBoutYaw();anchor=ys.update('top_push',Rotation.from_euler('z',.02).as_matrix()@rot);on=candidate(robot,{'left':1,'right':2},b,active_bout_yaw_anchor=anchor,**common)
  assert np.asarray(on['control_jacobian_world']).shape==(6,11);assert np.asarray(on['contact_normal_tracking']['jacobian']).shape==(3,11);assert np.asarray(on['contact_bout_yaw_tracking']['jacobian']).shape==(1,11)
  assert np.max(abs(b[12:]-q))<=.0400001 and abs(b[12]-q[0])<=.0150001 and not b[:12].any()
  results.append(dict(episode=ep.name,frame=t,off_exact=True,enabled_command_delta_rad=float(np.max(abs(a-b))),heading_error_rad=on['contact_bout_yaw_tracking']['heading_error_rad']))
  if first_fixture is None:first_fixture=(robot,q,side)
# Execute collector's actual lifecycle AST and reject stale anchors.
block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.expert_top_contact_bout_yaw_hold and frontal_plan'))
code=compile(ast.Module(body=[block],type_ignores=[]),'collector_yaw_lifecycle','exec');robot,q,side=first_fixture
scope=dict(np=np,args=NS(expert_top_contact_bout_yaw_hold=True),frontal_plan={'initial_top_selected':True},top_contact_bout_yaw=None,robot=robot,hands={'left':1,'right':2},side=side);life=[]
for mode in ['top_cross','top_press','top_push','top_push','top_lift','top_push','initial_top_guard_lift','front_guard_lift','top_release','idle']:
 scope.update(active_bout_yaw_anchor=None,expert=NS(mode=mode));exec(code,scope);assert (scope['active_bout_yaw_anchor'] is not None)==(mode=='top_push');life.append(dict(mode=mode,active=scope['active_bout_yaw_anchor'] is not None))
for p,h in manifest['source_sha256'].items():assert sha(p)==h,p
out=dict(passed=True,cli=cli,solver_fixtures=results,lifecycle=life,candidate_sha256=manifest['candidate_sha256'],live_sources_unchanged=True,scope='Actual staged parser and collector lifecycle AST plus actual staged coordinated_step; CPU observation fixture uses URDF FK/finite-difference body Jacobians and real bounded solver/literal joint metadata. Not Isaac/contact physics.',training_ready=False)
(stage/'WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(passed=True,cli=len(cli),solver_fixtures=len(results),lifecycle=len(life),live_sources_unchanged=True)))
