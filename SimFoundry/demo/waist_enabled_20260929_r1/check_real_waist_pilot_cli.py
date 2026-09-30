"""Actual staged parser/admission with real contract; stop before Isaac launch.
Real AppLauncher argument registration/config resolution run without app construction. Physical evidence validator
runs unchanged, including raw original gates, snapshots and actual-review SHA.
"""
from pathlib import Path
import argparse,contextlib,io,json,sys,types,hashlib,copy,ast,inspect
W=Path(__file__).resolve().parent;REPO=W.parents[1];sys.path.insert(0,str(REPO))
p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--collector',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
c=json.loads(a.contract.read_text());source=a.collector.read_text();prefix=source.split('app = AppLauncher(args, enable_cameras=True).app')[0]
if len(prefix)==len(source):raise ValueError('Missing explicit simulator boundary')
from isaaclab.app import AppLauncher
protocol=json.loads((Path(c['feasibility'][0]['root'])/'PROTOCOL.json').read_text());base=list(protocol['settings']);base[base.index('--role')+1]='pilot'
base=[x for x in base if x!='--extended-waist-diagnostic']
base+=['--waist-pilot-contract',str(a.contract.resolve()),'--out-dir','/tmp/waist_real_cli_no_simulation','--layout-start',str(c['layouts'][0]['layout_id']),'--wait-layout-start',str(c['wait_layouts'][0]['layout_id']),'--wait-episodes','1']
trials=[('real_bound_pilot',[],True),('unregistered_layout',['--layout-start','999999'],False),('changed_environment_seed',['--environment-seed','1'],False)]
rows=[];resolved_checks=[]
for label,extra,want in trials:
 sys.argv=['actual_staged_collector',*base,*extra];name='actual_pilot_cli_'+label;module=types.ModuleType(name);sys.modules[name]=module;module.__dict__.update(__file__=str(a.collector.resolve()));accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(prefix,str(a.collector),'exec'),module.__dict__)
 except SystemExit as exc:
  if exc.code!=2:raise
  accepted=False
 if accepted!=want:raise AssertionError((label,err.getvalue()))
 if accepted:
  admission=module.waist_admission
  assert admission.contract_sha256==sha(a.contract)
  assert admission.layout(c['layouts'][0]['layout_id'])==c['layouts'][0]
  assert admission.layout(c['wait_layouts'][0]['layout_id'],wait=True)==c['wait_layouts'][0]
  # Execute real launch configuration resolution without constructing the app.
  # Then invoke the actual staged post-launch gate before any env/data exists.
  resolved=copy.deepcopy(vars(module.args));resolved['enable_cameras']=True
  launcher=AppLauncher.__new__(AppLauncher);launcher.device_id=0;launcher._deferred_cuda_device_id=None
  launcher._config_resolution(resolved)
  calls=[n for n in ast.parse(source).body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='finalize_waist_pilot']
  assert len(calls)==1
  code=compile(ast.Module(body=calls,type_ignores=[]),'actual_post_launcher_admission','exec')
  module.args=argparse.Namespace(**resolved);exec(code,module.__dict__);resolved_checks.append(dict(case='actual_resolved_launch_settings',accepted=True))
  for key,value in [('physics_gpu',1),('waist_limit_rad',.8)]:
   module.args=argparse.Namespace(**dict(resolved,**{key:value}))
   try:exec(code,module.__dict__)
   except ValueError as exc:resolved_checks.append(dict(case='changed_resolved_'+key,accepted=False,error=str(exc)))
   else:raise AssertionError('Changed post-launch setting accepted: '+key)
  assert sha(inspect.getfile(AppLauncher))==c['launcher_source']['sha256']

 rows.append(dict(case=label,accepted=accepted,error_tail=err.getvalue().splitlines()[-1:] if err.getvalue() else []))
report=dict(passed=True,cases=rows,resolved_settings_checks=resolved_checks,launcher_source_sha256=sha(inspect.getfile(AppLauncher)),contract_sha256=sha(a.contract),candidate_collector_sha256=sha(a.collector),checker_sha256=sha(__file__),scope='Actual AppLauncher argument registration and configuration resolution (no app constructed), real complete physical-evidence validator, and exact staged pre/post admission gates. Changed seed/layout/resolved physics GPU/waist limit rejected. No Isaac environment, model or pilot data created.',training_ready=False)
if a.out.exists():raise ValueError('Do not overwrite prior evidence')
a.out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
