"""Real parser and collector dispatch checks for isolated finite-preload stage.
No simulation. Disabled and non-right branches preserve original class selection.
"""
from pathlib import Path
import ast,contextlib,datetime,hashlib,io,json,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_box_material_preload';P=W/'staged_front_corridor_midpoint_integrated';sys.path[:0]=[str(S),str(W),str(ROOT)]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());assert len(prep['stage_sha256'])==73
for n,h in prep['stage_sha256'].items():assert sha(S/n)==h,n
s=(S/'collect_paired_sorting.py').read_text();back=s
for e in reversed(prep['collector_edits']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(P/'collect_paired_sorting.py').read_text()
plan=json.loads((W/'front_corridor_midpoint_physical_r1/PROTOCOL.json').read_text())['plan'];configs=[];neg=[]
for c in plan['commands']:
 old,_=parser_namespace(P/'collect_paired_sorting.py',c['args'],full=True);off,_=parser_namespace(S/'collect_paired_sorting.py',c['args'],full=True);on,_=parser_namespace(S/'collect_paired_sorting.py',c['args']+['--front-box-material-preload'],full=True)
 assert off['front_box_material_preload'] is False and on['front_box_material_preload'] is True
 oldd=old;offd=dict(off);ond=dict(on);offd.pop('front_box_material_preload');ond.pop('front_box_material_preload');assert oldd==offd==ond
 assert semantic_settings(old)==semantic_settings(offd)==semantic_settings(ond)
 assert semantic_settings(off)['front_box_material_preload'] is False and semantic_settings(on)['front_box_material_preload'] is True
 configs.append(dict(layout_id=c['layout_id'],tasks=c['tasks'],default_off_identical=True,only_declared_flag_changed=True))
args=plan['commands'][0]['args']+['--front-box-material-preload']
for flag in ['--front-corridor-midpoint-replan','--front-loaded-z-priority','--front-initial-center-landing','--front-cop-edge-speed']:
 bad=list(args);bad.remove(flag)
 try:
  with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
 except (SystemExit,ValueError,AssertionError):neg.append(flag)
 else:raise AssertionError('bad config accepted '+flag)
bad=list(args);bad[bad.index('--front-cop-drive-step-m')+1]='.001'
try:
 with contextlib.redirect_stderr(io.StringIO()):parser_namespace(S/'collect_paired_sorting.py',bad,full=True)
except (SystemExit,ValueError,AssertionError):neg.append('changed_drive_step')
else:raise AssertionError('bad drive accepted')
tree=ast.parse(s);node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="args.front_box_material_preload and side == 'right'");code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(S/'collect_paired_sorting.py'),'exec');dispatch=[]
from types import SimpleNamespace
from front_box_material_preload_route_v2 import FrontBoxMaterialPreloadState
for enabled in [False,True]:
 for side in ['left','right']:
  sentinel=object();ns=dict(args=SimpleNamespace(front_box_material_preload=enabled),side=side,top_cls=sentinel,top_extra={},frontal_plan={});exec(code,ns)
  selected=enabled and side=='right';assert (ns['top_cls'] is FrontBoxMaterialPreloadState)==selected
  if selected:assert ns['top_extra']=={'material_preload_enabled':True} and ns['frontal_plan']=={'front_box_material_preload':prep['specification']}
  else:assert ns['top_cls'] is sentinel and ns['top_extra']=={} and ns['frontal_plan']=={}
  dispatch.append(dict(enabled=enabled,side=side,selected=selected))
with (S/'PARSER_DISPATCH_CHECK.json').open('x') as f:json.dump(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,configurations=configs,negative_cases=neg,dispatch=dispatch,source_sha256={str(p):sha(p) for p in [Path(__file__),S/'COLLECTOR_PREPARATION.json',S/'collect_paired_sorting.py',S/'material_preload_v2.py',S/'front_box_material_preload_route_v2.py',P/'collect_paired_sorting.py']},full_audit_family_ready=False,simulation_started=False,training_ready=False),f,indent=2)
print(json.dumps(dict(passed=True,configurations=len(configs),negative=len(neg),dispatch=len(dispatch))))
