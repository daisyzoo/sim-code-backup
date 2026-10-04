"""Actual parser/default-off AST identity and native collector wiring.
Executes collector factory, observation/update logging, metadata and source nodes.
Synthetic geometry/force input only; no full robot loop or new physics.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,contextlib,io,sys,json,hashlib,datetime,inspect,tempfile
W=Path(__file__).resolve().parent;ROOT=W.parents[1];P=W/'staged_front_loaded_z_quarter_v1';S=W/'staged_front_contact_window_v1';D=W/'front_contact_window_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from front_initial_center_cop_route import FrontCopRouteState
from front_window_native_v3 import WindowFrontCopRouteState
from peak_load_update_trace import TracedPeakLoadControl
from simfoundry.data.top_contact_bypass import support_vertex
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());tree=ast.parse((S/'collect_paired_sorting.py').read_text());old=ast.parse((P/'collect_paired_sorting.py').read_text())
class RemoveNew(ast.NodeTransformer):
 def visit_If(self,n):
  if 'args.front_contact_window' in ast.unparse(n.test):return None
  return self.generic_visit(n)
 def visit_Expr(self,n):
  v=n.value
  if isinstance(v,ast.Call) and ast.unparse(v.func)=='parser.add_argument' and v.args and isinstance(v.args[0],ast.Constant) and v.args[0].value=='--front-contact-window':return None
  return self.generic_visit(n)
assert ast.dump(RemoveNew().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(old,include_attributes=False)
def parsed(path,cli):
 before=list(sys.path)
 try:
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):return parser_namespace(path,cli,full=True)[0]
 finally:sys.path[:]=before
protocol=read(W/'front_loaded_z_quarter_physical_r2/PROTOCOL.json');parsers=[]
for c in protocol['plan']['commands']:
 base=parsed(P/'collect_paired_sorting.py',c['args']);off=parsed(S/'collect_paired_sorting.py',c['args']);assert off.pop('front_contact_window') is False and off==base
 on=parsed(S/'collect_paired_sorting.py',c['args']+['--front-contact-window']);assert on.pop('front_contact_window') is True and on==base;parsers.append(dict(layout_id=c['layout_id'],wait=c['wait'],default_exact=True,enabled_only_one_flag=True))
base=protocol['plan']['commands'][0]['args'];negative=[]
for name,cli in [('missing_quarter',[x for x in base if x!='--front-loaded-z-quarter']),('missing_peak',[x for x in base if x!='--peak-load-bias-guard']),('missing_substeps',[x for x in base if x!='--trace-substep-contacts']),('missing_initial',[x for x in base if x!='--front-initial-center-landing']),('hysteresis',base+['--expert-frontal-top-support-hysteresis-m','.001']),('policy',base+['--policy-port','8000']),('idle',base+['--idle']),('pilot',base+['--role','pilot'])]:
 try:parsed(S/'collect_paired_sorting.py',cli+['--front-contact-window'])
 except SystemExit as e:assert e.code!=0;negative.append(name)
 else:raise AssertionError(name)
nodes=[n for n in ast.walk(tree) if isinstance(n,ast.If) and 'args.front_contact_window' in ast.unparse(n.test)]
def find(fragment):return next(n for n in nodes if fragment in ast.unparse(n) and not 'parser.error' in ast.unparse(n))
def execute(n,env):exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(n)],type_ignores=[])),'<actual collector node>','exec'),env)
factory=find('top_cls = WindowFrontCopRouteState');before=find('frontal_state.observe_contact_window');after=find('front_contact_window_log.append');meta=find("episode.collect_meta['front_contact_window']");archive=find('paths.extend');dump=find("folder / 'front_contact_window.json'");init=find('front_contact_window_log = []')
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='waypoint' for t in n.targets) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='frontal_state.update')
assert before.lineno<call.lineno<after.lineno
factory_cases=[]
for enabled in [False,True]:
 env=dict(args=NS(front_contact_window=enabled),top_cls=FrontCopRouteState,top_extra={},frontal_plan={});execute(factory,env)
 assert env['top_cls'] is (WindowFrontCopRouteState if enabled else FrontCopRouteState)
 assert Path(inspect.getfile(env['top_cls'])).parent==S
 state=env['top_cls'](rear=NS(plan=dict(direction=1,initial_target_xyz=[.4,-.09,.77],obstacle_initial_xyz=[.6,.1,.77],margin=.012)),side='left',size=(.15,.145,.04),obstacle_size=(.15,.145,.04),mode='top_push',top_mode='top_push',command=(.4,-.08,.79),start=(.4,-.08,.79),guarded_descent=True,continuous_drag=True,front_inset_fraction=1.,recontact_travel_z=.86,tilt_recontact_rad=.03,confirm_terminal_release=True,route_report=dict(goal_y=.4),route_x=.4,route_stage='lateral_y',edge_core_size=(.135,.1276,.04),**env['top_extra'])
 state.load=TracedPeakLoadControl(5.,min_bias_m=-.006);state.load.bind_owner(state)
 tip=(.4,-.08,.79);quat=(0.,0.,0.,1.);vertex=support_vertex('left',quat,quat);hand_xyz=[tip[i]-vertex[i] for i in range(3)];values=[1.]*17+[0.]*7
 env.update(frontal_state=state,front_route_selected=True,hand_xyz=hand_xyz,hand_quat=quat,load_n=0.,side='left',hands={'left':0},robot=None,env=None,target_actor='mailer',obstacle_actor='parcel_box',target_size=(.15,.145,.04),obstacle_size=(.15,.145,.04),target_quat=quat,obstacle_quat=quat,palm_xyz=lambda *a:(.4,-.08,.86),parcel_xyz=lambda env,name:tip if name=='mailer' else (.6,.1,.77),extent_x_from_quat=lambda size,quat:size[0]/2,peak_observation=dict(vertical_load_n=values))
 # Use actual observed center z, independent of the supporting point height.
 env['parcel_xyz']=lambda env,name:(.4,-.08,.77) if name=='mailer' else (.6,.1,.77)
 execute(init,env)
 for step in range(1,4):
  env['step']=step;env['point_kwargs']=dict(tip=tip,quat=quat,obstacle_quat=quat,control_offset_local=(0.,0.,0.),load_n=0.,hand_obstacle_gap_m=.05)
  state.load.observe(action_step=step,after_action_step=step-1,vertical_load_n=values);execute(before,env);execute(call,env);execute(after,env)
 assert state.top_mode==('top_push' if enabled else 'top_lift')
 if enabled:assert len(env['front_contact_window_log'])==3 and all(r['step']==r['action_step'] for r in env['front_contact_window_log'])
 else:assert 'front_contact_window_log' not in env
 factory_cases.append(dict(enabled=enabled,native_steps=3,mode=state.top_mode,logged_intervals=len(env.get('front_contact_window_log',[]))))
 for selected in [False,True]:
  env.update(front_route_selected=selected,episode=NS(collect_meta={}),paths=[],STAGE=S,qs=[0,1,2,3],json=json)
  if enabled and not selected:env['front_contact_window_log']=[]
  execute(meta,env);execute(archive,env)
  with tempfile.TemporaryDirectory(prefix='window-wiring-') as tmp:
   env['folder']=Path(tmp);execute(dump,env);out=Path(tmp)/'front_contact_window.json'
   if enabled:
    assert out.exists();r=read(out);assert r['selected_front'] is selected and r['executed_frames']==4;assert env['episode'].collect_meta['front_contact_window']['selected_front'] is selected
    assert {p.name for p in env['paths']}==set(read(D/'STAGE_PREPARATION.json')['helpers'])
   else:assert not out.exists() and not env['paths'] and not env['episode'].collect_meta
sources={str(p):sha(p) for p in S.iterdir() if p.is_file()};sources.update({str(p):sha(p) for p in [Path(__file__),D/'STAGE_PREPARATION.json',P/'collect_paired_sorting.py',W/'front_loaded_z_quarter_physical_r2/PROTOCOL.json',W/'prepare_closed_peak_trial.py']})
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,default_exact_parent_ast=True,parser_cases=parsers,invalid_parser_rejections=negative,native_factory_and_loop_cases=factory_cases,actual_metadata_and_archive=True,source_sha256=sources,full_runtime_chain_pending=True,physical_launch_ready=False,physics_started=False,training_ready=False)
with (D/'COLLECTOR_WIRING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,parser_commands=len(parsers),negative_rejections=len(negative),native_factory_cases=len(factory_cases))))
