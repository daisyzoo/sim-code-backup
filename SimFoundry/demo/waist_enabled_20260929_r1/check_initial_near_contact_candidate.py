"""Actual staged parser/factory default equivalence and scoped near contact."""
from pathlib import Path
import sys,types,json,hashlib,ast,math,contextlib,io,copy
from types import SimpleNamespace as NS
import torch
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_initial_near_contact';sys.path.insert(0,str(repo));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=json.loads((stage/'MANIFEST.json').read_text())
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
base=json.loads((root/'initial_top_short_recovery_depth_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/near_contact_parser_only']
source=(stage/'collect_paired_sorting.py').read_text();live=(repo/'scripts/collect_paired_sorting.py').read_text()
def parse(source,argv):
 sys.argv=['collector',*argv];scope={'__file__':str(repo/'scripts/collect_paired_sorting.py')};err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'actual_prefix','exec'),scope)
 except SystemExit as exc:assert exc.code==2;return None,err.getvalue().splitlines()[-1]
 return scope['args'],None
cases=[('off',base,True),('on',base+['--expert-initial-top-near-inset-fraction','.7'],True),('no_initial',[x for x in base if x!='--expert-initial-top-route']+['--expert-initial-top-near-inset-fraction','.7'],False),('no_projected',[x for x in base if x!='--expert-top-projected-support']+['--expert-initial-top-near-inset-fraction','.7'],False)]
for v in ['.49','1.01','nan']:cases.append((v,base+['--expert-initial-top-near-inset-fraction',v],False))
cli=[];args_by={}
for label,argv,expected in cases:
 args,error=parse(source,argv);assert (args is not None)==expected,(label,error);cli.append(dict(case=label,accepted=args is not None,error=error));args_by[label]=args
live_args,error=parse(live,base);assert error is None

def factory(source):
 nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.expert_frontal_bypass and task_id != 'wait_no_package'"];assert len(nodes)==1;return compile(ast.Module(body=nodes,type_ignores=[]),'actual_factory','exec')
oldfactory=factory(live);newfactory=factory(source);results=[]
for identifier in range(62000,62016):
 layout=json.loads((root/f'development_layouts/{identifier}.json').read_text());scene={actor:NS(data=NS(root_quat_w=NS(torch=torch.tensor([[0.,0.,math.sin(layout[key+'_yaw']/2),math.cos(layout[key+'_yaw']/2)]],dtype=torch.float64)))) for actor,key in [('parcel_box','box'),('mailer','mailer')]}
 for key,side,task in [('box','right','push_box_to_bin'),('mailer','left','nudge_mailer_to_bin')]:
  def execute(args,code):
   ctx=dict(args=copy.deepcopy(args),task_id=task,layout=layout,side=side,target=layout[key+'_xyz'],initial={'box':layout['box_xyz'],'mailer':layout['mailer_xyz']},env=NS(scene=scene),front_route_selected=False,initial_top_selected=False,frontal_state=None,frontal_plan=None,inactive_anchor={'left':[.3,.23,.89],'right':[.3,-.23,.89]});exec(code,ctx);return ctx
  a=execute(live_args,oldfactory);b=execute(args_by['off'],newfactory);c=execute(args_by['on'],newfactory)
  def record(ctx):
   st=ctx['frontal_state'];return dict(controller=type(st).__name__,initial=ctx['initial_top_selected'],front=ctx['front_route_selected'],fraction=getattr(st,'front_inset_fraction',None),height=getattr(st,'recontact_travel_z',None),plan=copy.deepcopy(ctx['frontal_plan']))
  ra,rb,rc=record(a),record(b),record(c);rb['plan'].pop('initial_top_contact_location',None);assert ra==rb,(identifier,key,'default changed')
  expect=bool(c['initial_top_selected'] and layout[key+'_xyz'][0]<.48)
  if c['frontal_state'] is not None:
   metadata=c['frontal_plan']['initial_top_contact_location'];assert metadata['override_applied']==expect;assert metadata['effective_top_fraction']==getattr(c['frontal_state'],'front_inset_fraction',None)
  assert rc['fraction']==(.7 if expect else ra['fraction'])
  assert (ra['controller'],ra['initial'],ra['front'],ra['height'])==(rc['controller'],rc['initial'],rc['front'],rc['height'])
  results.append(dict(layout_id=identifier,task=key,applied=expect,old_fraction=ra['fraction'],new_fraction=rc['fraction']))
assert any(x['applied'] and x['task']=='box' for x in results) and any(x['applied'] and x['task']=='mailer' for x in results)
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
assert sha(stage/'collect_paired_sorting.py')==manifest['candidate_sha256']
report=dict(cli=cli,rows=results,default_equivalent_conditions=len(results),near_conditions=sum(x['applied'] for x in results),candidate_sha256=manifest['candidate_sha256'],live_sources_unchanged=True,scope='Actual collector parser/factory AST with CPU reset geometry and quaternion observations; default state/config equivalence except added truthful metadata, scoped near-only override, original route/height retained. No physical or data admission proof.',training_ready=False);(stage/'WIRING_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(cli=cli,default_equivalent_conditions=len(results),near_conditions=report['near_conditions']),indent=2))
