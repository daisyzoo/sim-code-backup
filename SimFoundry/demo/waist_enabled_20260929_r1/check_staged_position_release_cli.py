"""Run real staged parser/validation prefix with only AppLauncher option stub."""
from pathlib import Path
import json,sys,types,io,contextlib,hashlib
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_position_release'
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
base=json.loads((root/'projected_hysteresis_mirror1200_r1/PROTOCOL.json').read_text())['settings']+['--out-dir','/tmp/staged_cli_no_creation']
source=(stage/'collect_paired_sorting.py').read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]
trials=[('default_off',base,True),('explicit_on',base+['--expert-top-confirmed-release'],True)]
for option in ('--expert-top-projected-support','--expert-frontal-top-guarded-descent','--expert-frontal-top-continuous-drag'):
 removed={option}
 if option=='--expert-top-projected-support':removed.add('--expert-top-nearer-far-contact')
 trials.append(('missing_'+option,[x for x in base if x not in removed]+['--expert-top-confirmed-release'],False))
pilot=list(base);pilot[pilot.index('--role')+1]='pilot';trials.append(('pilot_not_enabled',pilot+['--expert-top-confirmed-release'],False))
rows=[]
for label,args,expected in trials:
 sys.argv=['staged_collector',*args];err=io.StringIO();accepted=True
 try:
  with contextlib.redirect_stderr(err):
   scope={'__file__':str(repo/'scripts/collect_paired_sorting.py'),'__name__':'staged_validation_only'}
   exec(compile(source,str(stage/'collect_paired_sorting.py'),'exec'),scope)
 except SystemExit as exc:
  assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue())
 if not accepted:assert 'Confirmed top release requires' in err.getvalue(),(label,err.getvalue())
 rows.append(dict(case=label,accepted=accepted))
for p,h in json.loads((stage/'MANIFEST.json').read_text())['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
(stage/'CLI_CHECK.json').write_text(json.dumps(dict(cases=rows,candidate_collector_sha256=hashlib.sha256((stage/'collect_paired_sorting.py').read_bytes()).hexdigest(),scope='Real staged parser/validation prefix, AppLauncher options stub. No simulation/data writes or live-source edits.',training_ready=False),indent=2))
print(json.dumps(rows,indent=2))
