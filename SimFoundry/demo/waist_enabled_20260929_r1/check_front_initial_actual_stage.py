"""Actual parser, collector transition and coordinator/final-action AST checks.
Real starting q/scene and separately declared endpoint fixtures; no physics.
Expensive static/preflight results are reused only after exact source binding.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,sys,json,hashlib,copy,datetime,contextlib,io,inspect
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_initial_center';A=W/'staged_terminal_release_margin';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from clearance_runtime import ClearanceGuard
from front_initial_center_runtime import FrontInitialCenterRuntime
from front_initial_center_cop_route import FrontCopRouteState
from front_initial_center_top_contact import support_mesh
from simfoundry.data.projected_support_reference import projected_support_reference
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text())
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
assert Path(inspect.getfile(FrontInitialCenterRuntime)).parent==S
restored=(S/'collect_paired_sorting.py').read_text()
for e in reversed(prep['edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(A/'collect_paired_sorting.py').read_text()
coord=(S/'waist_coordination_clearance.py').read_text();e=prep['coordination_edits'];assert coord.count(e['added_branch'])==1
assert coord.replace(e['added_branch'],'').replace(e['signature_new'],e['signature_old'])==(A/'waist_coordination_clearance.py').read_text()
assert support_mesh()==__import__('simfoundry.data.top_contact_bypass',fromlist=['support_mesh']).support_mesh()
base=json.loads((W/'terminal_margin_physical_preparation_r1/PLAN.json').read_text())['commands'][0]['args'];parser_rows=[]
cases=[('off',base,True),('on',base+['--front-initial-center-landing'],True)]
for flag in ['--terminal-release-margin','--front-micro-repair-retention','--peak-load-bias-guard','--expert-top-projected-support','--expert-top-contact-normal-hold']:
 assert flag in base;cases.append(('missing_'+flag,[x for x in base if x!=flag]+['--front-initial-center-landing'],False))
cases.append(('conflicting_center',base+['--front-initial-center-landing','--expert-top-contact-center-calibration'],False))
for label,args,expected in cases:
 try:
  with contextlib.redirect_stderr(io.StringIO()):namespace,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True)
  ok=True
 except (ValueError,SystemExit):ok=False
 assert ok==expected,(label,ok);parser_rows.append(dict(case=label,accepted=ok))
 if label=='on':enabled_args=SimpleNamespace(**namespace)
# All helper references must resolve to the staged implementation.
for name in ['front_initial_center_lifecycle_v3','front_initial_center_lifecycle_v2','front_initial_center_plan','front_initial_center_tracking','front_initial_center_selection','front_initial_center_adapter','front_initial_center_cop_route','front_initial_center_top_contact']:
 assert Path(inspect.getfile(sys.modules[name])).parent==S,name
collector=ast.parse((S/'collect_paired_sorting.py').read_text());coordinator=ast.parse(coord)
def module_code(body):return compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),'<actual staged collector>','exec')
select=next(n for n in ast.walk(collector) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_initial_center_landing' and any(isinstance(v,ast.Name) and v.id=='CenterFrontState' for v in ast.walk(n)))
block=next(n for n in ast.walk(collector) if isinstance(n,ast.If) and ast.unparse(n.test)=='front_initial_runtime is not None' and any(isinstance(v,ast.Name) and v.id=='center_poses' for v in ast.walk(n)))
program=module_code([ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[block],orelse=[])])
branches=[n for n in coordinator.body if isinstance(n,ast.FunctionDef) and n.name=='coordinated_step'][0].body
front=[n for n in branches if isinstance(n,ast.If) and 'front_initial_override' in ast.unparse(n.test)]
assert len(front)==2
function=ast.FunctionDef(name='actual_command',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=front+[ast.Return(value=ast.Constant(value=None))],decorator_list=[])
command_program=module_code([function])
# Include the exact collector slew/range/waist/refinement/final-guard chain.
slew=next(n for n in ast.walk(collector) if isinstance(n,ast.Assign) and ast.unparse(n)=='action = np.clip(action, previous - 0.055, previous + 0.055)')
loop=next(n for n in ast.walk(collector) if isinstance(n,ast.For) and any(isinstance(x,ast.Assign) and ast.unparse(x).startswith('action = np.clip(default + action,') for x in n.body))
start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n).startswith('action = np.clip(default + action,'));end=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n)=='previous = action.copy()')
final_program=module_code([ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[slew]+loop.body[start:end],orelse=[])])
class Tensor:
 def __init__(self,x):self.x=np.asarray(x)
 def __getitem__(self,index):return Tensor(self.x[index])
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.x
fixture=W/'FRONT_INITIAL_ACTUAL_CORE_CHECK.json';data=json.loads(fixture.read_text());assert data['status']=='complete'
for path,h in data['source_sha256'].items():assert sha(path)==h,path
guard=ClearanceGuard(ROOT,S);records=[];negatives=[];sample=None
for original in data['records']:
 p=original['plan'];z=p['scene'];side=z['side'];inactive='right' if side=='left' else 'left';q=np.array(p['start']);step=p['step'];context=original['live_first_event']['context'];decay=np.array(context['decay'])
 ep=next((W/'fresh_closed_peak_trials_r1').glob('case_*/'+original['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());row=copy.deepcopy(next(x for x in fr['rows'] if x['step']==step));row.pop('step');saved_row=copy.deepcopy(row)
 edge_core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core']
 assert edge_core==original['actual_core'] and z['core_size']==edge_core['collision_core_size_xyz']
 selection=dict(args=enabled_args,np=np,json=json,hashlib=hashlib,STAGE=S,side=side,task_id='push_box_to_bin' if side=='right' else 'nudge_mailer_to_bin',edge_size=np.array(z['core_size']),edge_core=edge_core,obstacle_size=z['other_size'],clearance_guard=guard,frontal_plan=copy.deepcopy(fr['plan']),top_cls=object)
 off=dict(selection,args=SimpleNamespace(**dict(vars(enabled_args),front_initial_center_landing=False)));exec(module_code([select]),off);assert off['top_cls'] is object and 'front_initial_runtime' not in off
 exec(module_code([select]),selection);runtime=selection['front_initial_runtime'];assert selection['top_cls'] is FrontCopRouteState
 state=FrontCopRouteState(SimpleNamespace(plan=copy.deepcopy(fr['plan'])),side,tuple(fr['plan']['top_recontact']['contact_size_xyz']),obstacle_size=tuple(z['other_size']),guarded_descent=True,continuous_drag=True,drag_step_m=.003,front_inset_fraction=.9)
 state.top_mode=state.mode=row['mode'];state.load.filtered_n=row['contact_load']['filtered_vertical_load_n']
 def inputs(current,previous_q,previous_command,t,waypoint):
  poses={s:guard.model.fk(s,current)[0] for s in ('left','right')};pos=np.array([poses[s][:3,3] for s in ('left','right')]);quat=np.array([Rotation.from_matrix(poses[s][:3,:3]).as_quat() for s in ('left','right')]);robot=SimpleNamespace(data=SimpleNamespace(body_pos_w=SimpleNamespace(torch=Tensor([pos])),body_quat_w=SimpleNamespace(torch=Tensor([quat])),joint_pos=SimpleNamespace(torch=Tensor([np.r_[np.zeros(12),current]]))))
  ref=projected_support_reference(guard.model.vertices[side],poses[side][:3,:3],Rotation.from_quat(z['target_quat']).as_matrix()[:,2],center_local=runtime.center_local)
  anchors={s:(poses[s][:3,3]+poses[s][:3,:3]@np.array([.20,0,.007])).tolist() for s in poses}
  return dict(np=np,front_initial_runtime=runtime,projected_support_context={k:v.tolist() for k,v in ref.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')},region_approach=None,robot=robot,hands={'left':0,'right':1},ordered_ids=list(range(23)),side=side,waypoint=copy.deepcopy(waypoint),reference=ref,frontal_state=state,step=t,qs=[np.r_[np.zeros(12),previous_q]],previous=np.r_[np.zeros(12),previous_command],default=np.zeros(23),target_actor='target',obstacle_actor='other',parcel_xyz=lambda env,actor:z['target_xyz'] if actor=='target' else z['other_xyz'],env=None,target_quat=z['target_quat'],obstacle_quat=z['other_quat'],load_n=0.,top_contact_normal_anchor=None,inactive_anchor=anchors,point_kwargs={},front_initial_override=None,clearance_failure=None)
 def run_command(ns):
  ev=ns['front_initial_override'];current=np.array(ev['context']['current']);prev=np.array(ev['context']['previous_command']);action=np.zeros(23,dtype=np.float32)
  env=dict(np=np,front_initial_override=ev,recontact_override=None,robot=ns['robot'],joint_ids=list(range(12,23)),indices=list(range(12,23)),default=np.zeros(23),action=action,previous_command=prev,bounded=True,clearance_geometry=guard.geometry,palms={},points={},active_point_offset=None,active_support_reference=None,anchor=ns['inactive_anchor'],state=SimpleNamespace(side=side))
  exec(command_program,env);coordinate=env['actual_command']();assert coordinate['controller_kind']=='verified_unloaded_front_initial_joint_path';assert np.array_equal(action[12:23],np.array(ev['command'],dtype=np.float32))
  final=dict(ns,args=enabled_args,U1_JOINT_LIMIT_LO=U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI=U1_JOINT_LIMIT_HI,action=action,frontal_plan=selection['frontal_plan'],coordination_log=[dict(step=ns['step'],**coordinate)],frontal_log=[dict(step=ns['step'],**ns['waypoint'])],clearance_guard=guard,clearance_rows=[])
  exec(final_program,final);assert final['clearance_failure'] is None and np.array_equal(final['action'][12:23],np.array(ev['command'],dtype=np.float32))
  return env
 ns=inputs(q,np.array(context['previous_q']),np.array(context['previous_command']),step,row)
 with patch('front_initial_center_lifecycle_v3.plan',return_value=copy.deepcopy(p)):exec(program,ns)
 assert ns['clearance_failure'] is None;assert row==saved_row
 expected='command' if p['accepted'] else 'unchanged';assert runtime.rows[-1]['kind']==expected
 if p['accepted']:
  command_env=run_command(ns)
  if sample is None:sample=(command_env,copy.deepcopy(ns['front_initial_override']))
 else:
  assert ns['front_initial_override'] is None and ns['waypoint']==row and runtime.center_local is None
 # Manufacture a terminal endpoint pose to test wiring of actual 3-frame measurement.
 # Its feasibility is already separately checked; this does not assert arrival.
 if p['accepted']:
  e=np.array(p['endpoint']);runtime.lifecycle.active=True;runtime.lifecycle.plan=p;runtime.lifecycle.index=len(p['waypoints'])-1;runtime.lifecycle.last_step=step;runtime.lifecycle.ticks=0;runtime.lifecycle.ready=0
  handovers=[]
  for j in range(3):
   endrow=copy.deepcopy(row);endrow['mode']='top_cross';endrow['contact_load']['filtered_vertical_load_n']=0.;state.recontacts=0;state.load.filtered_n=0.
   ns=inputs(e,e,e,step+j+1,endrow);exec(program,ns);handovers.append(ns['front_initial_override']['kind']);run_command(ns)
  assert handovers==['command','command','handover']
  event=ns['front_initial_override'];assert np.array_equal(runtime.center_local,event['captured_center_local'])
  assert ns['top_contact_normal_anchor']==event['captured_normal_local_up'] and ns['inactive_anchor'][inactive]==event['captured_inactive_anchor_world']
  assert np.array_equal(ns['point_kwargs']['control_offset_local'],event['reference']['reference_local']) and state.top_mode=='top_press'
  # Active path failures exit the collector loop before any command override.
  runtime.lifecycle.finished=False;runtime.lifecycle.active=True;badrow=copy.deepcopy(row);badrow.pop('contact_load');ns=inputs(e,e,e,step+4,badrow);exec(program,ns)
  assert ns['clearance_failure']['phase']=='front_initial_center' and ns['front_initial_override'] is None
 records.append(dict(episode=original['episode'],actual_collision_core=z['core_size'],nominal_contact_size=list(state.size),first_event=expected,actual_collector_checked=True,command_and_final_chain_checked=p['accepted'],manufactured_handover_checked=p['accepted'],stop_propagated=p['accepted'],default_off_selection_unchanged=True))
 print(original['episode'],expected,'collector/command/final checked',flush=True)
for name in ['command','current','previous','load','filtered','guard','recontacts','phase','proposal','conflict']:
 env,event=sample;env=env.copy();event=copy.deepcopy(event);env['front_initial_override']=event;env['action']=np.zeros(23)
 if name=='command':event['command'][1]+=.01
 if name=='current':event['context']['current'][1]+=.01
 if name=='previous':event['context']['previous_command'][1]+=.01
 if name=='load':event['context']['observed_load_n']=.001
 if name=='filtered':event['context']['filtered_load_n']=.051
 if name=='guard':event['context']['guard_stop']=True
 if name=='recontacts':event['context']['recontacts']=1
 if name=='phase':event['context']['parent_mode']='top_push'
 if name=='proposal':event['proposal']['nominal_scene']['accepted']=False
 if name=='conflict':env['recontact_override']=event
 exec(command_program,env)
 try:env['actual_command']();raise AssertionError('Invalid front command admitted: '+name)
 except ValueError:pass
 assert not np.any(env['action']);negatives.append(name)
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parser=parser_rows,rows=records,rejected_command_corruptions=negatives,asset_root_matches_parent=True,source_inverse_diff_verified=True,fixture_sha256=sha(fixture),stage_sha256=prep['stage_sha256'],source_sha256={str(Path(__file__)):sha(__file__),str(fixture):sha(fixture)},simulation_started=False,training_ready=False,remaining='Independent physical event/control/source audit adapters and complete original paired-group regression still required.')
with (W/'FRONT_INITIAL_ACTUAL_STAGE_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('passed',len(records),'scenes',len(parser_rows),'parser cases',len(negatives),'command rejection cases')
