"""Run actual staged parser and extracted collector admission/stop statements.
No simulator or counterfactual rollout. Unchanged parent source is proved by
reversing the recorded edits; first changed commands use recorded observations.
"""
from pathlib import Path
from types import SimpleNamespace
import ast,contextlib,copy,datetime,hashlib,inspect,io,json,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_loaded_reference';A=W/'staged_front_initial_center';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from front_loaded_reference_adapter import admit
assert Path(inspect.getfile(admit)).parent==S
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'PREPARATION.json').read_text());out=W/'FRONT_LOADED_REFERENCE_STAGE_CHECK.json';assert not out.exists()
report=dict(status='running',scope=__doc__,parser=[],admission=[],negative=[],source_sha256={str(S/'PREPARATION.json'):sha(S/'PREPARATION.json'),str(Path(__file__)):sha(__file__)},simulation_started=False,training_ready=False)
def save():out.write_text(json.dumps(report,indent=2))
try:
 save()
 for n,h in prep['stage_sha256'].items():assert sha(S/n)==h
 s=(S/'collect_paired_sorting.py').read_text();restored=s
 for e in reversed(prep['edits']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(A/'collect_paired_sorting.py').read_text()
 for n,h in prep['parent_stage_sha256'].items():
  assert sha(A/n)==h
  if n!='collect_paired_sorting.py':assert sha(S/n)==h
 proto=W/'front_initial_physical_r1/PROTOCOL.json';protocol=json.loads(proto.read_text());report['source_sha256'][str(proto)]=sha(proto)
 for item in protocol['plan']['commands']:
  cli=item['args']
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
   before,_=parser_namespace(A/'collect_paired_sorting.py',cli,full=True);off,_=parser_namespace(S/'collect_paired_sorting.py',cli,full=True);on,_=parser_namespace(S/'collect_paired_sorting.py',cli+['--front-loaded-reference-cap'],full=True)
  assert off.pop('front_loaded_reference_cap') is False and off==before
  assert on.pop('front_loaded_reference_cap') is True and on==before
  report['parser'].append(dict(layout_id=item['layout_id'],disabled_identical=True,enabled_only_new_flag=True))
 base=protocol['plan']['commands'][0]['args']
 for missing in ['--front-initial-center-landing','--terminal-release-margin','--front-cop-edge-speed','--trace-substep-contacts','--peak-load-bias-guard','--expert-top-contact-normal-hold']:
  assert missing in base;rejected=False
  try:
   with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',[x for x in base if x!=missing]+['--front-loaded-reference-cap'],full=True)
  except (SystemExit,ValueError):rejected=True
  assert rejected;report['negative'].append(dict(case='missing_'+missing,rejected=True))
 tree=ast.parse(s);block=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='args.front_loaded_reference_cap and front_initial_runtime is not None')
 capture=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='cap_previous_xy' for x in n.targets))
 update=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.unparse(n.value).startswith('frontal_state.update('))
 initial=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='front_initial_runtime is not None' and 'center_poses' in ast.unparse(n))
 assert capture.lineno<update.lineno<initial.lineno<block.lineno
 report['collector_statement_order']=[capture.lineno,update.lineno,initial.lineno,block.lineno]
 loop=ast.For(target=ast.Name(id='_once',ctx=ast.Store()),iter=ast.List(elts=[ast.Constant(value=0)],ctx=ast.Load()),body=[block,ast.Assign(targets=[ast.Name(id='reached_next_statement',ctx=ast.Store())],value=ast.Constant(value=True))],orelse=[])
 program=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),'<actual staged collector cap branch>','exec')
 probe=W/'FRONT_INITIAL_LOADED_REFERENCE_CAP_PROBE.json';records=json.loads(probe.read_text())['records'];report['source_sha256'][str(probe)]=sha(probe)
 for rec in records:
  if rec['first_intervention'] is None:continue
  ep=next((W/'front_initial_physical_r1').glob('case_*/'+rec['episode']));fr=json.loads((ep/'frontal_bypass.json').read_text());events=json.loads((ep/'front_initial_center.json').read_text());first=rec['first_intervention'];t=first['step'];row=next(r for r in fr['rows'] if r['step']==t);event=next(r for r in events['rows'] if r['kind']=='handover');runtime=SimpleNamespace(center_local=np.array(event['captured_center_local']),rows=[event]);previous=next(r for r in fr['rows'] if r['step']==t-1)['target_xyz'][:2]
  for p in [ep/'frontal_bypass.json',ep/'front_initial_center.json']:report['source_sha256'][str(p)]=sha(p)
  for case in ['enabled','disabled','no_front_runtime','empty_window','parent_guard']:
   waypoint=copy.deepcopy(row);state=SimpleNamespace(command=tuple(row['target_xyz']),last_emitted_xy=tuple(row['target_xyz'][:2]))
   if case=='empty_window':waypoint['parcel_top_xyz'][0]+=1.
   if case=='parent_guard':waypoint['route_stop_reason']='explicit_guard_fixture'
   env=dict(args=SimpleNamespace(front_loaded_reference_cap=case!='disabled'),front_initial_runtime=None if case=='no_front_runtime' else runtime,frontal_state=state,waypoint=waypoint,cap_previous_xy=previous,point_kwargs={'slip_contact':dict(valid=True,normal_load_n=first['observed_normal_load_N'])},step=t,reached_next_statement=False,clearance_failure=None)
   exec(program,env)
   if case=='empty_window':assert not env['reached_next_statement'] and env['clearance_failure']['kind']=='stop' and state.command==tuple(row['target_xyz'])
   else:
    assert env['reached_next_statement'] and env['clearance_failure'] is None
    if case=='enabled':
     assert np.allclose(env['waypoint']['target_xyz'][:2],first['advice']['command_xy'],rtol=0,atol=1e-12)
     assert env['waypoint']['target_xyz'][2]==row['target_xyz'][2] and state.last_emitted_xy==tuple(env['waypoint']['target_xyz'][:2])
    else:assert env['waypoint']['target_xyz']==row['target_xyz'] and state.command==tuple(row['target_xyz'])
   report['admission'].append(dict(episode=ep.name,step=t,case=case,reached_next_statement=env['reached_next_statement'],passed=True))
 report.update(status='complete',passed=True,updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save();print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope']},indent=2))
except Exception as e:report.update(status='failed',error=repr(e));save();raise
