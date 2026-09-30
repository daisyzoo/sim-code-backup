"""Actual staged parser/transition AST on completed recordings; no dynamics."""
from pathlib import Path
from types import SimpleNamespace as NS
import ast,json,sys,types,io,contextlib,copy,hashlib,importlib.util
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_bounded_top_lead';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
source=(stage/'collect_paired_sorting.py').read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0];base=json.loads((root/'contact_center_groups_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/bounded_top_lead_no_output'];on=base+['--expert-top-object-relative-lead-m','.024'];cli=[]
trials=[('off',base,True),('on',on,True),('without_calibration',[s for s in on if s!='--expert-top-contact-center-calibration'],False),('competing_front_lead',on+['--expert-front-object-relative-lead'],False),('too_low',base+['--expert-top-object-relative-lead-m','.011'],False),('too_high',base+['--expert-top-object-relative-lead-m','.031'],False),('nan',base+['--expert-top-object-relative-lead-m','nan'],False)]
for label,argv,want in trials:
 sys.argv=['staged',*argv];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(prefix,'staged_cli','exec'),{'__file__':str(stage/'collect_paired_sorting.py'),'__name__':'staged_cli'})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==want,(label,err.getvalue());cli.append(dict(case=label,accepted=accepted))
name='simfoundry.data.bounded_top_lead';spec=importlib.util.spec_from_file_location(name,stage/'bounded_top_lead.py');module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
import numpy as np
blocks=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.If) and ast.unparse(n.test)=='bounded_top_lead is not None'];assert len(blocks)==1;code=compile(ast.Module(body=blocks,type_ignores=[]),'actual_staged_transition','exec');reports=[]
for task in ('nudge_mailer_to_bin','push_box_to_bin'):
 ep=root/'contact_center_groups_r1/case_62013'/('layout_62013_'+task);fr=json.loads((ep/'frontal_bypass.json').read_text());plan=fr['plan'];cal={r['step']:r for r in json.loads((ep/'contact_center_calibration.json').read_text())['rows']};key='box' if task.startswith('push') else 'mailer';xyz=np.load(ep/'trace.npz')[key]
 state=NS(rear=NS(plan=plan),route_report=plan.get('front_route_candidates'),drag_step_m=.003,command=None);helper=module.BoundedTopLead(.024);active=protected=0
 for row in fr['rows']:
  t=row['step'];env=dict(bounded_top_lead=helper,frontal_state=state,waypoint=copy.deepcopy(row),contact_center_calibration=NS(center_local=[0,0,0] if cal.get(t,{}).get('calibrated_after',False) else None),parcel_xyz=lambda env,actor,t=t:xyz[t].tolist(),env=None,target_actor=key)
  before_command=copy.deepcopy(state.command);exec(code,env);out=env['waypoint']
  if row['mode']=='top_push' and cal.get(t,{}).get('calibrated_after',False):
   assert out['mode']==row['mode'] and out['target_xyz'][2]==row['target_xyz'][2]
   lead=out['bounded_top_object_lead'];assert max(abs(lead['desired_xy'][i]-xyz[t,i]) for i in (0,1))<=.024000001
   assert max(abs(lead['command_xy'][i]-lead['previous_xy'][i]) for i in (0,1))<=.003000001
   assert tuple(out['target_xyz'])==tuple(state.command);active+=1
  else:assert out==row and state.command==before_command and helper.previous is None;protected+=1
  disabled=dict(env,bounded_top_lead=None,waypoint=copy.deepcopy(row));exec(code,disabled);assert disabled['waypoint']==row
 reports.append(dict(episode=ep.name,active_frames=active,guard_release_unready_unchanged=protected,default_rows_exact=len(fr['rows']),raw_sha256=sha(ep/'raw.npz')))
m=json.loads((stage/'MANIFEST.json').read_text())
for p,h in m['source_sha256'].items():assert sha(p)==h,p
for n,h in m['candidate_sha256'].items():assert sha(stage/n)==h,n
import unittest
assert sha(root/'bounded_top_lead_candidate.py')==sha(stage/'bounded_top_lead.py')
result=unittest.TextTestRunner(stream=sys.stdout).run(unittest.defaultTestLoader.loadTestsFromName('test_bounded_top_lead_candidate'));assert result.wasSuccessful()
out=dict(cli=cli,actual_transition_ast=reports,candidate_sha256=m['candidate_sha256'],checker_sha256=sha(__file__),pure_tests_run=result.testsRun,scope='Actual staged CLI and post-update AST on fixed measured rows. Default/guard/release preservation, desired lead and slew. Does not replay original state dynamics or establish actual forces, collisions, executed robot response or training admission.',training_ready=False)
(stage/'WIRING_CHECK.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
