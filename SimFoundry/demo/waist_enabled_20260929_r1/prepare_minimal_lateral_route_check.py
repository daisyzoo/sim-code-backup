"""Real parser and recorded reset geometry check; no simulation or new data."""
from pathlib import Path
import sys,types,json,hashlib,contextlib,io
import numpy as np
root=Path(__file__).resolve().parent;repo=root.parents[1];sys.path.insert(0,str(repo))
from simfoundry.data.front_top_route import select_front_route
p=root/'fresh_lateral_00_pilot_r1';protocol=json.loads((p/'PROTOCOL.json').read_text());contract=json.loads(Path(protocol['contract_path']).read_text())
args=protocol['commands'][0]['args'];base=args[:args.index('--waist-pilot-contract')];base[base.index('--role')+1]='diagnostic';base+=['--extended-waist-diagnostic','--out-dir','/tmp/lateral_parser_only_no_output']
class AppLauncher:
 @staticmethod
 def add_app_launcher_args(parser):
  parser.add_argument('--device',default='cuda');parser.add_argument('--headless',action='store_true');parser.add_argument('--viz',default='none')
app=types.ModuleType('isaaclab.app');app.AppLauncher=AppLauncher;sys.modules['isaaclab.app']=app
source=(repo/'scripts/collect_paired_sorting.py').read_text();cli=[]
for label,settings,expected in [('parent',base,True),('front_only',base+['--expert-front-top-route'],True),('front_plus_10mm_without_projected',base+['--expert-front-top-route','--expert-top-alignment-tolerance-m','.010'],False)]:
 sys.argv=['collector',*settings];accepted=True;err=io.StringIO()
 try:
  with contextlib.redirect_stderr(err):exec(compile(source.split('app = AppLauncher(args, enable_cameras=True).app')[0],'actual_parser','exec'),{'__file__':str(repo/'scripts/collect_paired_sorting.py')})
 except SystemExit as exc:assert exc.code==2;accepted=False
 assert accepted==expected,(label,err.getvalue());cli.append(dict(variant=label,accepted=accepted,parser_error=err.getvalue().splitlines()[-1] if not accepted else None))
rows=[]
for ep in sorted(p.glob('case_84000*/layout_*')):
 with np.load(ep/'trace.npz') as tr,np.load(ep/'parcel_orientation.npz') as ori:
  key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';size=(.14,.09,.045) if key=='box' else (.15,.145,.04);other_size=(.15,.145,.04) if key=='box' else (.14,.09,.045)
  chosen,report=select_front_route(tr[key][0],tr[other][0],size,other_size,ori[key][0],ori[other][0],-1 if key=='box' else 1,margin=.02)
  rows.append(dict(episode=ep.name,selected_front=chosen is not None,chosen=chosen,candidates=report,raw_sha256=hashlib.sha256((ep/'raw.npz').read_bytes()).hexdigest()))
result=dict(cli=cli,reset_routes=rows,parent_protocol_sha256=hashlib.sha256((p/'PROTOCOL.json').read_bytes()).hexdigest(),collector_sha256=hashlib.sha256(source.encode()).hexdigest(),proposed_settings=base[:-2]+['--expert-front-top-route'],source_unchanged=True,queued=False,training_ready=False,scope='Only front-route enabling currently admissible as minimal legacy-profile ablation.10mm requires projected support and is NOT an independent legacy tolerance change. Parent/source exact hashes must be refreshed before future physical trial; full original swapped4 conditions retained. No physical result or data admission. Does not fix known box approach stall by itself.')
(root/'MINIMAL_LATERAL_ROUTE_PRECHECK.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item()))
print(json.dumps(dict(cli=cli,reset_routes=[dict(episode=x['episode'],front=x['selected_front']) for x in rows]),indent=2))
