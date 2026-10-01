"""Actual collector AST must trace every selected rear push; other routes unchanged."""
from pathlib import Path
import ast,types,sys,itertools,json,hashlib
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_rear_joint_xy';parent=w/'staged_front_edge_speed';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def block(path):
 tree=ast.parse(path.read_text());return next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.waist_coordinated_expert' and 'coordinated_step' in ast.unparse(n))
new=block(stage/'collect_paired_sorting.py');old=block(parent/'collect_paired_sorting.py');records=[]
def call(node,ns):
 captured={}
 def spy(robot,hands,action,**kw):
  assert kw['state'] is ns['expert'] and kw['state'].last_target_xyz==(.6,.1,.8);captured.update(kw);return dict(trace_requested=kw['trace_jacobian'])
 stub=types.ModuleType('simfoundry.data.waist_coordination');stub.coordinated_step=spy;sys.modules[stub.__name__]=stub
 exec(compile(ast.Module(body=[node],type_ignores=[]),'collector_trace_hook','exec'),ns);return captured
for freq,step,enabled,plan_kind,mode,coordinated in itertools.product([0,20],[1,20],[False,True],['none','front','rear'],['top_press','top_push','top_lift','top_release'],[False,True]):
 plan=None if plan_kind=='none' else {} if plan_kind=='front' else {'rear_coupled_progress':{'enabled':True}}
 args=types.SimpleNamespace(waist_coordinated_expert=coordinated,bounded_coupled_ik=True,waist_limit_rad=1.,trace_control_jacobian_every=freq,rear_coupled_progress=enabled)
 ns=dict(args=args,step=step,robot=None,hands={},action=np.zeros(23),expert=types.SimpleNamespace(mode=mode,last_target_xyz=(.6,.1,.8)),inactive_anchor={},default=np.zeros(23),active_control_offset=None,projected_support_context=None,waist_preference=None,active_normal_anchor=None,active_bout_yaw_anchor=None,coordination_log=[],frontal_plan=plan)
 a=call(old,dict(ns,coordination_log=[]));b=call(new,dict(ns,coordination_log=[]));wanted=bool((freq and step%freq==0) or (enabled and plan_kind=='rear' and mode=='top_push'))
 if coordinated:
  assert b['trace_jacobian']==wanted
  assert {k:v for k,v in a.items() if k not in ['trace_jacobian','default']}=={k:v for k,v in b.items() if k not in ['trace_jacobian','default']}
  if not (enabled and plan_kind=='rear' and mode=='top_push'):assert b['trace_jacobian']==a['trace_jacobian']
 else:assert not a and not b
 records.append(dict(freq=freq,step=step,enabled=enabled,plan=plan_kind,mode=mode,coordinated=coordinated,trace=wanted if coordinated else None))
(stage/'EXECUTION_TRACE_WIRING_CHECK.json').write_text(json.dumps(dict(passed=True,cases=len(records),rows=records,collector_sha256=sha(stage/'collect_paired_sorting.py'),parent_collector_sha256=sha(parent/'collect_paired_sorting.py'),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual collector call AST with spy coordinator verifies state goal is passed and full rear top_push logging, default/front/nonpush unchanged. Exact real solver-to-raw replay is separately checked; this fixture itself does not run physics or solve IK.'),indent=2));print('PASSED',len(records))
