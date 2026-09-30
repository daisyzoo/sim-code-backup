"""Execute actual isolated collector factory AST on development geometry fixtures."""
from pathlib import Path
import sys,types,json,hashlib,ast,math,contextlib,io
import torch
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_stability'
sys.path.insert(0,str(repo))
manifest=json.loads((stage/'MANIFEST.json').read_text())
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
for name in ('confirmed_position_release','top_contact_bypass','initial_top_route_candidate','initial_top_route'):
 p=stage/(name+'.py');m=types.ModuleType('simfoundry.data.'+name);m.__file__=str(repo/'simfoundry/data'/p.name);sys.modules[m.__name__]=m;exec(compile(p.read_text(),str(p),'exec'),m.__dict__)
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
source=(stage/'collect_paired_sorting.py').read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0]
base=json.loads((root/'projected_hysteresis_mirror1200_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/initial_top_factory_no_write','--expert-top-confirmed-release','--expert-initial-top-route','--expert-front-contact-inset-fraction','.7','--expert-top-tilt-recontact-rad','.03']
cli=[]
for label,argv,expected in [('enabled',base,True),('off',[v for v in base if v!='--expert-initial-top-route'],True),('bad_fraction',[('.49' if v=='.7' else v) for v in base],False),('bad_tilt',[('.21' if v=='.03' else v) for v in base],False),('nan_tilt',[('nan' if v=='.03' else v) for v in base],False),('missing_guard',[v for v in base if v!='--expert-frontal-top-guarded-descent'],False),('missing_continuous',[v for v in base if v!='--expert-frontal-top-continuous-drag'],False)]:
 sys.argv=['staged_cli',*argv];stderr=io.StringIO();valid=True;scope={'__file__':str(repo/'scripts/collect_paired_sorting.py')}
 try:
  with contextlib.redirect_stderr(stderr):exec(compile(prefix,'staged_prefix','exec'),scope)
 except SystemExit as exc:assert exc.code==2;valid=False
 assert valid==expected,(label,stderr.getvalue());cli.append(dict(case=label,accepted=valid))
 if label=='enabled':args=scope['args']
tree=ast.parse(source)
blocks=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.expert_frontal_bypass and task_id != 'wait_no_package'"]
assert len(blocks)==1;factory=compile(ast.Module(body=blocks,type_ignores=[]),'actual_staged_factory','exec')
ref=[n.test for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test).startswith('args.expert_top_projected_support and (') and any(isinstance(v,ast.Name) and v.id=='initial_top_selected' for v in ast.walk(n.test))];assert len(ref)==1
ref_code=compile(ast.Expression(body=ref[0]),'actual_reference_selection','eval')
rows=[]
from types import SimpleNamespace as NS
for identifier in range(62000,62016):
 layout=json.loads((root/f'development_layouts/{identifier}.json').read_text())
 scene={name:NS(data=NS(root_quat_w=NS(torch=torch.tensor([[0.,0.,math.sin(layout[key+'_yaw']/2),math.cos(layout[key+'_yaw']/2)]],dtype=torch.float64)))) for name,key in [('parcel_box','box'),('mailer','mailer')]}
 for key,side,task in [('box','right','push_box_to_bin'),('mailer','left','nudge_mailer_to_bin')]:
  context=dict(args=args,task_id=task,layout=layout,side=side,target=layout[key+'_xyz'],initial={'box':layout['box_xyz'],'mailer':layout['mailer_xyz']},env=NS(scene=scene),front_route_selected=False,initial_top_selected=False,frontal_state=None,frontal_plan=None,inactive_anchor={'left':[.3,.23,.89],'right':[.3,-.23,.89]})
  exec(factory,context);selected=context['initial_top_selected'];state=context['frontal_state']
  row=dict(layout_id=identifier,target=key,initial_top_selected=selected,controller=type(state).__name__,frontal_required=context['frontal_plan']['required'])
  if state is not None and hasattr(state,'tilt_recontact_rad'):
   assert state.tilt_recontact_rad==.03
   assert state.front_inset_fraction==(.7 if context['front_route_selected'] else (None if context['target'][0]>=.48 else 1.))
   row.update(front_route_selected=context['front_route_selected'],effective_fraction=state.front_inset_fraction,tilt_recontact_rad=state.tilt_recontact_rad)
  if selected:
   assert not row['frontal_required'];assert type(state).__name__=='InitialTopRouteState';assert state.top_mode is None
   assert eval(ref_code,context), 'Initial top must use projected reference on its very first update'
   row['first_update_projected_reference']=True
  rows.append(row)
assert {(r['layout_id'],r['target']) for r in rows if r['initial_top_selected']}=={(62004,'mailer'),(62005,'box'),(62007,'box')}
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
(stage/'FACTORY_CHECK.json').write_text(json.dumps(dict(rows=rows,cli=cli,candidate_sha256=manifest['candidate_sha256'],scope='Actual staged collector AST factory executed with CPU quaternion/geometry fixtures over all32developmentconditions. No Isaac, dynamics, rendered data or physical readiness. Confirms selected instances, original required flag, first-step virtual reference and CLI plumbing only.',production_frozen_sources_unchanged=True,training_ready=False),indent=2))
print(json.dumps(dict(selected=[r for r in rows if r['initial_top_selected']],cli=cli),indent=2))
