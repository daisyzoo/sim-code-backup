"""Execute actual parser and collector projection branch without simulation.
Actual failure records prove command arithmetic only; stop archive serialization
uses explicitly synthetic poses, never invented physical stop observations.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,contextlib,copy,datetime,hashlib,inspect,io,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_projection';A=W/'staged_front_loaded_reference';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from front_loaded_reference_adapter import admit
assert Path(inspect.getfile(admit)).parent==S
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=W/'FRONT_LOADED_PROJECTION_STAGE_CHECK.json';assert not out.exists()
report=dict(status='running',scope=__doc__,parser=[],negative=[],admission=[],source_sha256={},simulation_started=False,training_ready=False)
def bind(p):report['source_sha256'][str(p)]=sha(p)
def read(p):bind(p);return json.loads(p.read_text())
def save():out.write_text(json.dumps(report,indent=2))
try:
 bind(Path(__file__));prep=read(S/'PREPARATION.json');math=read(W/'FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json');assert math['passed']
 for p,h in math['source_sha256'].items():assert sha(p)==h;report['source_sha256'][p]=h
 for n,h in prep['stage_sha256'].items():assert sha(S/n)==h;bind(S/n)
 for n,h in prep['parent_stage_sha256'].items():
  assert sha(A/n)==h;bind(A/n);restored=(S/n).read_text()
  for e in reversed(prep['edits']):
   if e['file']==n:assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(A/n).read_text(),n
 proto=read(W/'front_loaded_physical_r1/PROTOCOL.json')
 for item in proto['plan']['commands']:
  cli=item['args'];assert '--front-loaded-reference-cap' in cli
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   before,_=parser_namespace(A/'collect_paired_sorting.py',cli,full=True)
   off,_=parser_namespace(S/'collect_paired_sorting.py',cli,full=True)
   on,_=parser_namespace(S/'collect_paired_sorting.py',cli+['--front-loaded-material-projection'],full=True)
  assert off.pop('front_loaded_material_projection') is False and off==before
  assert on.pop('front_loaded_material_projection') is True and on==before
  report['parser'].append(dict(layout_id=item['layout_id'],disabled_identical=True,enabled_only_new_flag=True))
 base=proto['plan']['commands'][0]['args']
 for missing in ['--front-loaded-reference-cap','--front-initial-center-landing','--terminal-release-margin','--front-cop-edge-speed','--trace-substep-contacts','--peak-load-bias-guard','--expert-top-contact-normal-hold']:
  assert missing in base;rejected=False
  try:
   with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',[x for x in base if x!=missing]+['--front-loaded-material-projection'],full=True)
  except (ValueError,SystemExit):rejected=True
  assert rejected,missing;report['negative'].append(dict(case=missing,rejected=True))
 # Prefix imports may alter sys.path. Restore and assert the exact tested module.
 sys.path[:0]=[str(S),str(W),str(ROOT)]
 import front_loaded_reference_adapter as adapter
 assert Path(adapter.__file__).resolve()==S/'front_loaded_reference_adapter.py'
 tree=ast.parse((S/'collect_paired_sorting.py').read_text())
 block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_reference_cap and front_initial_runtime is not None')
 capture=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='cap_previous_xy' for x in n.targets))
 update=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n.value).startswith('frontal_state.update('))
 initial=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='front_initial_runtime is not None' and 'center_poses' in ast.unparse(n))
 assert capture.lineno<update.lineno<initial.lineno<block.lineno
 report['collector_statement_order']=[capture.lineno,update.lineno,initial.lineno,block.lineno]
 loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[block,ast.Assign(targets=[ast.Name(id='reached_next_statement',ctx=ast.Store())],value=ast.Constant(value=True))],orelse=[])
 program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual projection collector branch>','exec')
 for caseid,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
  ep=W/'front_loaded_physical_r1'/f'case_{caseid}'/f'layout_{caseid}_{task}'
  failure=read(ep/'self_clearance.json')['failure'];r=failure['record'];t=failure['step'];diag=read(ep/'LOADED_CAP_EMPTY_INTERSECTION_V2_DIAGNOSTIC.json')
  event=next(e for e in read(ep/'front_initial_center.json')['rows'] if e['kind']=='handover');runtime=SimpleNamespace(center_local=np.array(event['captured_center_local']),rows=[event])
  # Reference Z does not enter projection; use a declared synthetic placeholder.
  original=dict(target_xyz=r['parent_target_xyz'],observed_support_xyz=[*r['reference_xy'],0.],parcel_top_xyz=[*r['material_surface_xy'],0.],mode='top_push')
  for case in ['projection_on','projection_off','cap_disabled','no_runtime','parent_guard','release','unloaded','non_push','no_capture','genuine_empty']:
   row=copy.deepcopy(original);state=SimpleNamespace(command=tuple(row['target_xyz']),last_emitted_xy=tuple(row['target_xyz'][:2]));rt=runtime
   if case=='no_runtime':rt=None
   if case=='no_capture':rt=SimpleNamespace(center_local=None,rows=[])
   if case=='parent_guard':row['route_stop_reason']='synthetic_guard'
   if case=='release':row['release_reason']='synthetic_release'
   if case=='non_push':row['mode']='top_descend'
   if case=='genuine_empty':row['parcel_top_xyz'][0]+=1.
   target='box' if task.startswith('push_box') else 'mailer';other='mailer' if target=='box' else 'box'
   xyz={target:[.41,.13,.8],other:[.51,-.12,.8]};poses={'left':np.eye(4),'right':np.eye(4)}
   env=dict(args=SimpleNamespace(front_loaded_reference_cap=case!='cap_disabled',front_loaded_material_projection=case!='projection_off'),front_initial_runtime=rt,frontal_state=state,waypoint=row,cap_previous_xy=r['previous_command_xy'],point_kwargs={'slip_contact':dict(valid=True,normal_load_n=0. if case=='unloaded' else r['normal_load_n'])},step=t,reached_next_statement=False,clearance_failure=None,center_q=np.arange(11)*.01,center_poses=poses,qs=[None]*t,solved_contact_forces=[{'after_action_step':t-1}],previous=np.arange(23)*.001,default=np.arange(23)*.002,target_actor=target,obstacle_actor=other,target_quat=[0.,0.,0.,1.],obstacle_quat=[0.,0.,0.,1.],projected_support_context={'reference_local':[.01,.02,.03]},parcel_xyz=lambda unused,name:xyz[name],env=None)
   exec(program,env)
   if case in ['projection_off','genuine_empty']:
    assert not env['reached_next_statement'] and state.command==tuple(original['target_xyz'])
    stop=env['clearance_failure'];assert stop['reason']=='empty_original_slew_lead_material_intersection'
    if case=='projection_off':assert stop['record']['lower']==r['lower'] and stop['record']['upper']==r['upper'] and 'stop_observation' not in stop
    else:
     obs=stop['stop_observation'];assert obs['timing']=='current_pre_action_no_action_issued' and obs['recorded_frames']==t and obs['previous_solved_action_step']==t-1
     assert obs['upper_q_waist_left_right']==env['center_q'].tolist() and obs['previous_upper_command']==(env['previous'][12:23]+env['default'][12:23]).tolist()
     assert obs['target_xyz']==xyz[target] and obs['other_xyz']==xyz[other] and obs['target_quat_xyzw']==env['target_quat'] and obs['other_quat_xyzw']==env['obstacle_quat']
     assert obs['hand_pose_world']=={k:v.tolist() for k,v in poses.items()} and obs['projected_support_context']==env['projected_support_context'];json.dumps(stop)
   else:
    assert env['reached_next_statement'] and env['clearance_failure'] is None
    if case=='projection_on':
     got=env['waypoint']['target_xyz'];assert np.allclose(got[:2],diag['unissued_geometric_alternative_xy'],rtol=0,atol=1e-15)
     assert got[2]==original['target_xyz'][2] and state.command==tuple(got) and state.last_emitted_xy==tuple(got[:2])
    else:assert env['waypoint']['target_xyz']==original['target_xyz'] and state.command==tuple(original['target_xyz'])
   report['admission'].append(dict(episode=ep.name,step=t,case=case,passed=True,reached_next_statement=env['reached_next_statement'],archive_context='synthetic_serialization_only' if case=='genuine_empty' else None))
 report.update(status='complete',passed=True,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),physical_success_proven=False,remaining=['Independent projected-command and stop-pose auditor','Original full batch audit closure','Matched full physical comparison including stagnation'])
 save();print(json.dumps(dict(passed=True,parser_commands=len(report['parser']),negative_parser_cases=len(report['negative']),actual_collector_cases=len(report['admission']),simulation_started=False),indent=2))
except Exception as e:report.update(status='failed',error=repr(e));save();raise
