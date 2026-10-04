"""Bind the unchanged collector entry/options/archive to one repaired guard file.
No physics and no replacement of independent event/command admission checks.
"""
from pathlib import Path
import json,hashlib,datetime,sys,ast,contextlib,io
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_trailing_v2';D=W/'front_box_trailing_admission_preparation_r2';P=W/'front_box_trailing_physical_preparation_r2';sys.path[:0]=[str(W),str(ROOT)];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
from front_box_trailing_stage_source_binding_v2 import verify_preparation,verify_settings
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
def verify_prelaunch(args):
 # Parser output precedes the collector's documented runtime resolution.
 # Compare the original prelaunch contract, not already-resolved provenance.
 prelaunch=dict(args);assert type(prelaunch.pop('front_box_trailing_landing')) is bool
 assert prelaunch.pop('joint_transport_clearance') is True and prelaunch.pop('inactive_transport_clearance') is False and prelaunch.pop('front_box_recenter') is True
 settings=semantic_settings(prelaunch)
 for key in ['front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
 assert settings==read(W/'staged_closed_peak_trial/TRIAL_PROFILE.json')['prelaunch_settings']
used,bound=verify_preparation();assert len(used)==98;plan=read(P/'PLAN.json');old=read(W/'front_box_trailing_physical_preparation_r1/PLAN.json');assert plan['groups']==old['groups'] and plan['parent_run']==old['parent_run'] and len(plan['commands'])==6
parent=W/'staged_front_box_trailing_v1';assert sha(S/'collect_paired_sorting.py')==sha(parent/'collect_paired_sorting.py');rows=[]
for item,base in zip(plan['commands'],old['commands']):
 expected=list(base['args']);expected[expected.index('--out-dir')+1]=item['args'][item['args'].index('--out-dir')+1];assert item==dict(base,args=expected)
 for enabled in [False,True]:
  args=list(item['args'])
  if not enabled:args.remove('--front-box-trailing-landing')
  with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):newargs,_=parser_namespace(S/'collect_paired_sorting.py',args,full=True);oldargs,_=parser_namespace(parent/'collect_paired_sorting.py',args,full=True)
  assert newargs==oldargs and newargs['front_box_trailing_landing'] is enabled;verify_prelaunch(newargs);assert newargs['role']=='diagnostic' and newargs['steps']==1200 and newargs['wait_steps']==70 and newargs['push_assist'] is False
  rows.append(dict(layout_id=item['layout_id'],enabled=enabled,full_parser_exact_parent=True))
text=(S/'collect_paired_sorting.py').read_text();tree=ast.parse(text);guards=[n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module=='waist_coordination_clearance'];assert len(guards)==1 and any(a.name=='coordinated_step' for a in guards[0].names)
archive=next(n for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='paths.extend' and 'waist_coordination_clearance.py' in ast.unparse(n));env=dict(STAGE=S,paths=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[archive],type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec'),env);assert S/'waist_coordination_clearance.py' in env['paths'] and all(p.is_file() for p in env['paths'])
for p in [Path(__file__),P/'PLAN.json',W/'front_box_trailing_physical_preparation_r1/PLAN.json',D/'STAGE_PREPARATION.json',*[S/n for n in used]]:bound[str(p)]=sha(p)
report=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=6,parser_cases=rows,active_sources=98,collector_entry_exact_parent=True,default_off_parameter_and_metadata_code_unchanged=True,changed_guard_archived=True,source_sha256=bound,physical_started=False,training_ready=False)
with (D/'COLLECTOR_BINDING_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,parser_cases=len(rows),sources=98,changed_guard_archived=True)))
