"""Actual isolated parser, lifecycle AST and solver against measured CPU fixtures."""
from pathlib import Path
from types import SimpleNamespace as NS
import sys,types,ast,json,hashlib,io,contextlib,importlib.util
import numpy as np,torch
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_normal';sys.path[:0]=[str(root),str(repo)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text())
for name,h in manifest['candidate_sha256'].items():assert sha(stage/name)==h,name
source=(stage/'collect_paired_sorting.py').read_text();tree=ast.parse(source)
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
base=json.loads((root/'terminal_hold_front09_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/normal_candidate_no_output'];cli=[]
for label,args,expected in [('off',base,True),('on',base+['--expert-top-contact-normal-hold'],True),('no_force',[x for x in base if x!='--trace-solved-contact-forces']+['--expert-top-contact-normal-hold'],False),('no_top',[x for x in base if x!='--expert-frontal-top-recontact']+['--expert-top-contact-normal-hold'],False),('no_bounded',[x for x in base if x!='--bounded-coupled-ik']+['--expert-top-contact-normal-hold'],False)]:
 sys.argv=['candidate',*args];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'actual_parser','exec'),{'__file__':str(repo/'scripts/collect_paired_sorting.py')})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue());cli.append(dict(case=label,accepted=accepted))
# Load only actual literal joint metadata, avoiding simulation startup.
g1=types.ModuleType('simfoundry.robots.g1_assets')
for node in ast.parse((repo/'simfoundry/robots/g1_assets.py').read_text()).body:
 if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ('G1_U1_23DOF_JOINT_NAMES','U1_JOINT_LIMIT_LO','U1_JOINT_LIMIT_HI'):setattr(g1,node.target.id,ast.literal_eval(node.value))
sys.modules[g1.__name__]=g1
spec=importlib.util.spec_from_file_location('simfoundry.data.contact_normal_constraint',stage/'contact_normal_constraint.py');helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
from simfoundry.data.sorting_quality import PALM_OFFSET
src=(root/'audit_terminal_reach.py').read_text();exec(compile(src.split("p=root/'contact_x_ablation")[0],'<cached_fk>','exec'))

def transform(side,q):
 m=np.eye(4);m[:3,3]=[.08,0,.793]
 for name,origin,axis in chains[side]:
  m=m@origin
  if axis is not None:
   a=np.eye(4);a[:3,:3]=Rotation.from_rotvec(axis*q[names.index(name)]).as_matrix();m=m@a
 return m

def robot_at(q):
 ms={s:transform(s,q) for s in ('left','right')};pos=np.zeros((1,3,3));quat=np.zeros((1,3,4));jac=np.zeros((1,2,6,23));eps=1e-7
 for b,s in enumerate(('left','right'),1):
  pos[0,b]=ms[s][:3,3];quat[0,b]=Rotation.from_matrix(ms[s][:3,:3]).as_quat()
  for k in range(11):
   dq=np.zeros(11);dq[k]=eps;plus=transform(s,q+dq);minus=transform(s,q-dq)
   jac[0,b-1,:3,12+k]=(plus[:3,3]-minus[:3,3])/(2*eps)
   jac[0,b-1,3:,12+k]=Rotation.from_matrix(plus[:3,:3]@minus[:3,:3].T).as_rotvec()/(2*eps)
 full=np.zeros((1,23));full[0,12:]=q
 return NS(joint_names=list(g1.G1_U1_23DOF_JOINT_NAMES),num_base_dofs=0,is_fixed_base=True,data=NS(body_pos_w=NS(torch=torch.tensor(pos)),body_quat_w=NS(torch=torch.tensor(quat)),body_link_jacobian_w=NS(torch=torch.tensor(jac)),joint_pos=NS(torch=torch.tensor(full))))
def quat_apply(q,v):return torch.tensor(Rotation.from_quat(q.numpy()).apply(v.numpy()),dtype=v.dtype)
def function(path):
 t=ast.parse(path.read_text());ns=dict(np=np,torch=torch,quat_apply=quat_apply,PALM_OFFSET=PALM_OFFSET,G1_U1_23DOF_JOINT_NAMES=g1.G1_U1_23DOF_JOINT_NAMES);exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step'],type_ignores=[]),str(path),'exec'),ns);return ns['coordinated_step']
live=function(repo/'simfoundry/data/waist_coordination.py');candidate=function(stage/'waist_coordination.py')
ep=root/'terminal_hold_front09_groups_r1/case_62013/layout_62013_nudge_mailer_to_bin'
with np.load(ep/'raw.npz') as z:qs=z['q']
coords={r['step']:r for r in json.loads((ep/'coordination.json').read_text())};ctrl={r['step']:r for r in json.loads((ep/'expert_control.json').read_text())};results=[]
for t in (101,106,180,251,365,532,551):
 c=coords[t];robot=robot_at(qs[t,12:].astype(float));common=dict(state=NS(side='left',last_target_xyz=ctrl[t]['target_xyz']),anchor={'right':c['inactive_anchor']},default=np.zeros(23),waist_limit=1.,bounded=True,active_point_offset=c['active_point_offset_local'],active_support_reference=c['active_support_reference'],trace_jacobian=True);a=np.zeros(23);b=np.zeros(23);x=live(robot,{'left':1,'right':2},a,**common);y=candidate(robot,{'left':1,'right':2},b,**common)
 np.testing.assert_allclose(a,b,atol=1e-12,rtol=0);np.testing.assert_allclose(x['control_jacobian_world'],y['control_jacobian_world'],atol=1e-12);assert y['contact_normal_tracking'] is None;default_error=float(np.max(abs(a-b)))
 normal=transform('left',qs[101,12:])[:3,:3].T@np.array([0.,0.,1.]);n=candidate(robot,{'left':1,'right':2},b,active_normal_anchor_local=normal,**common)
 assert np.asarray(n['control_jacobian_world']).shape==(6,11) and np.asarray(n['contact_normal_tracking']['jacobian']).shape==(3,11)
 assert np.max(abs(b[12:]-qs[t,12:]))<=.0400001 and abs(b[12]-qs[t,12])<=.0150001 and not b[:12].any()
 results.append(dict(frame=t,default_max_command_error_rad=default_error,normal_error_rad=n['contact_normal_tracking']['angle_error_rad'],normal_command_diff_rad=float(np.max(abs(a-b)))))
# Execute actual collector anchor lifecycle, not a reimplementation.
block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.expert_top_contact_normal_hold and frontal_plan'))
code=compile(ast.Module(body=[block],type_ignores=[]),'actual_anchor_lifecycle','exec');scope=dict(np=np,args=NS(expert_top_contact_normal_hold=True),frontal_plan={'front_route_selected':True},top_contact_normal_anchor=None,expert=NS(mode='top_cross'),robot=robot_at(qs[101,12:]),hands={'left':1,'right':2},side='left')
lifecycle=[]
for mode,frame,expected in [('top_cross',101,False),('top_press',101,True),('top_push',106,True),('top_lift',182,True),('top_descend',245,True),('front_guard_lift',551,False),('top_release',551,False)]:
 scope.update(active_normal_anchor=None,robot=robot_at(qs[frame,12:]),expert=NS(mode=mode));exec(code,scope);assert (scope['active_normal_anchor'] is not None)==expected
 if expected:np.testing.assert_allclose(scope['active_normal_anchor'],normal,atol=1e-12)
 lifecycle.append(dict(mode=mode,normal_active=expected))
for enabled,has_plan in [(False,True),(True,False)]:
 scope.update(args=NS(expert_top_contact_normal_hold=enabled),frontal_plan={} if has_plan else None,expert=NS(mode='top_press'),active_normal_anchor=None);exec(code,scope);assert scope['active_normal_anchor'] is None
scope.update(args=NS(expert_top_contact_normal_hold=True),frontal_plan={'front_route_selected':False,'initial_top_selected':True},expert=NS(mode='top_press'),active_normal_anchor=None);exec(code,scope);assert scope['active_normal_anchor'] is not None
for p,h in manifest['source_sha256'].items():assert sha(p)==h,p
out=dict(checker_sha256=sha(__file__),cli=cli,measured_solver_fixtures=results,lifecycle=lifecycle,off_and_no_plan_inactive=True,nonfront_top_active=True,candidate_sha256=manifest['candidate_sha256'],live_source_unchanged=True,scope='Actual staged parser/collector anchor AST and coordinated_step with CPU torch. Independent URDF positions and finite-difference spatial Jacobians substitute robot observation API; real bounded solver and literal live joint limits used. Default equivalence, normal task dimensions and command bounds checked. Not Isaac or physical contact proof.',training_ready=False)
(stage/'WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
