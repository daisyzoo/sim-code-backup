"""Execute actual collector priority -> transport -> final guard statements.
Archived state/history and recorded objects are immutable. Proposed actions are
unissued; no hypothetical subsequent state, contact force, or success is claimed.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,copy,datetime,hashlib,json,sys,inspect
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_effective_height_v1';D=W/'front_effective_height_preparation_r1';sys.path[:0]=[str(S),str(W),str(ROOT)]
from clearance_runtime import ClearanceGuard
from joint_transport_parent_coordinate_v1 import parent_coordinate
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();tree=ast.parse((S/'collect_paired_sorting.py').read_text())
priority=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_z_priority' and 'priority_command' in ast.unparse(n));transport=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.joint_transport_clearance' and 'transport_command' in ast.unparse(n));guardblock=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='clearance_guard is not None' and 'final_clearance' in ast.unparse(n));previous=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()' and n.lineno>guardblock.lineno)
assert priority.lineno<transport.lineno<guardblock.lineno<previous.lineno
loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.Call(func=ast.Name(id='range',ctx=ast.Load()),args=[ast.Constant(1)],keywords=[]),body=[priority,transport,guardblock,previous,ast.Assign(targets=[ast.Name(id='reached_after_final_guard',ctx=ast.Store())],value=ast.Constant(True))],orelse=[]);program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual native quarter command chain>','exec')
class Tensor:
 def __init__(self,value):self.value=np.asarray(value);self.torch=self
 def __getitem__(self,key):return Tensor(self.value[key])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.value
class Invalid:
 def refine(self,**kwargs):
  x=np.asarray(kwargs['parent_command']).copy();x[0]=10.
  return x,dict(step=kwargs['step'],selected=kwargs['selected'],applied=True,output_command=x.tolist(),synthetic_invalid=True)
guard=ClearanceGuard(ROOT,S);rows=[];sources={}
expected_runtime=read(W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_RUNTIME_CHECK_V1.json')
for case,task,step in [(840023,'nudge_mailer_to_bin',165),(840020,'push_box_to_bin',181)]:
 ep=W/f'front_loaded_z_quarter_physical_r2/case_{case}/layout_{case}_{task}';co=next(r for r in read(ep/'coordination.json') if r['step']==step);fr=next(r for r in read(ep/'frontal_bypass.json')['rows'] if r['step']==step);old=co['front_loaded_z_priority'];tc=co['joint_transport_clearance']['collector_context'];sc=tc['scene'];side=sc['side'];target='mailer' if side=='left' else 'box';other='box' if side=='left' else 'mailer';expected=next(r['enabled_result'] for r in expected_runtime['rows'] if r['step']==step and r['episode']==ep.name)
 with np.load(ep/'raw.npz') as z:q=z['q'].copy();u=z['action'].copy()
 def environment(enabled,invalid=False):
  c=copy.deepcopy(parent_coordinate(co,old['output_command'],u[step,12:23]));c.pop('front_loaded_z_priority');c.pop('joint_transport_clearance');c.pop('joint_transport_unexecuted_parent_waist_target_rad',None);c.pop('unexecuted_parent_waist_target_rad',None);c['waist_target_rad']=old['context']['parent_command'][0]
  a=u[step].copy();a[12:23]=old['context']['parent_command'];xyz={target:np.asarray(sc['target_xyz'],np.float32),other:np.asarray(sc['other_xyz'],np.float32)};quat={target:np.asarray(sc['target_quat'],np.float32),other:np.asarray(sc['other_quat'],np.float32)};scene={n:NS(data=NS(root_quat_w=Tensor(quat[k][None]))) for n,k in [('parcel_box','box'),('mailer','mailer')]}
  return dict(args=NS(front_loaded_z_priority=True,front_loaded_z_quarter=True,joint_transport_clearance=True,joint_transport_effective_quarter_height=enabled),front_loaded_z_priority_controller=None,joint_transport_controller=Invalid() if invalid else None,clearance_guard=guard,default=np.zeros(23,np.float32),front_initial_runtime=NS(center_local=np.asarray(c['active_support_reference']['center_local'])),front_recontact_runtime=None,frontal_log=[copy.deepcopy(fr)],coordination_log=[c],front_loaded_z_priority_log=[],joint_transport_log=[],side=side,step=step,robot=NS(data=NS(joint_pos=Tensor(q[step][None]))),ordered_ids=list(range(23)),previous=u[step-1].copy(),action=a.copy(),env=NS(scene=scene),parcel_xyz=lambda unused,actor:xyz['box' if actor=='parcel_box' else 'mailer'],obstacle_size=sc['other_size'],edge_size=sc['core_size'],parameters=dict(tasks={task:dict(decay=tc['decay'])}),task_id=task,qs=[q[step-1].copy()],clearance_rows=[],clearance_failure=None,reached_after_final_guard=False,ROOT=ROOT,STAGE=S,np=np)
 for enabled in [False,True]:
  env=environment(enabled);exec(program,env);assert env['reached_after_final_guard'] and env['clearance_failure'] is None;assert env['clearance_rows'][-1]['accepted'];np.testing.assert_array_equal(env['action'][:12],u[step,:12]);np.testing.assert_array_equal(env['previous'],env['action']);assert env['front_loaded_z_priority_log'][-1]==old
  wanted=expected['output_command'] if enabled else u[step,12:23];np.testing.assert_array_equal(env['action'][12:23],wanted);record=copy.deepcopy(env['joint_transport_log'][-1]);context=record.pop('collector_context');assert context==tc
  assert record==(expected if enabled else {k:v for k,v in co['joint_transport_clearance'].items() if k!='collector_context'})
  source=Path(inspect.getfile(type(env['joint_transport_controller']))).resolve();assert source==S/('joint_transport_effective_height_runtime_v1.py' if enabled else 'joint_transport_runtime.py')
  coordinate=env['coordination_log'][-1];assert coordinate['waist_target_rad']==float(wanted[0])
  if enabled:assert coordinate['joint_transport_unexecuted_parent_waist_target_rad']==float(old['output_command'][0])
  rows.append(dict(episode=ep.name,step=step,enabled=enabled,exact_priority_and_transport=True,exact_final_action=True,guard_accepted=True));print(json.dumps(rows[-1]),flush=True)
 bad=environment(True,invalid=True);exec(program,bad);assert not bad['reached_after_final_guard'] and bad['clearance_failure']['reason']=='final_override_not_verified';np.testing.assert_array_equal(bad['previous'],u[step-1]);rows.append(dict(episode=ep.name,step=step,synthetic_invalid_transport=True,stopped_before_history_update=True))
 for name in ['raw.npz','coordination.json','frontal_bypass.json']:sources[str(ep/name)]=sha(ep/name)
for p in S.iterdir():
 if p.is_file():sources[str(p)]=sha(p)
for p in [Path(__file__),W/'joint_transport_parent_coordinate_v1.py',W/'front_loaded_z_quarter_physical_r2/EFFECTIVE_HEIGHT_RUNTIME_CHECK_V1.json']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,statement_order=[priority.lineno,transport.lineno,guardblock.lineno,previous.lineno],source_sha256=sources,passed=True,full_episode_source_audit_pending=True,physics_started=False,training_ready=False)
with (D/'NATIVE_COMMAND_CHAIN_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,cases=len(rows),physics_started=False)))
