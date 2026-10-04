"""Isolate box finite-preload collector from closed71-source midpoint parent.
Explicit default-off flag; only right-hand front route gets the wrapper.
All original source/controller branches remain unchanged when flag is off.
Full native source/audit integration is still pending; no physical launch.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;P=W/'staged_front_corridor_midpoint_integrated';D=W/'front_box_material_preload_draft_r1';S=W/'staged_front_box_material_preload';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not S.exists()
for name in ['REPLAY_CHECK.json','ROUTE_BRANCH_V2_CHECK.json','CONTROL_HISTORY_V2_CHECK.json']:
 proof=json.loads((D/name).read_text());assert proof['passed']
 for p,h in proof['source_sha256'].items():assert sha(p)==h,p
parent=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());assert len(parent['stage_sha256'])==71
spec=dict(enabled=True,version='front_box_material_preload_v1',side='right',phase='loaded_front_top_push_only',preload_limit_m=.012,increment='original_current_edge_advice_1_to_2mm',reference='measured_support_captured_object_local_at_push_entry',max_xy_step_m=.003,max_reference_lead_m=.030,preserve_parent_z=True,preserve_non_diagonal_cross_axis=True,parent_guards_first=True,reset_on_nonpush_or_invalid_cop_or_route_or_counter=True,training_ready=False)
s=(P/'collect_paired_sorting.py').read_text();edits=[]
def change(a,b):
 global s
 assert s.count(a)==1,(a[:70],s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b))
line=next(x for x in s.splitlines() if x.startswith("parser.add_argument('--front-corridor-midpoint-replan'"));change(line,line+"\nparser.add_argument('--front-box-material-preload',action='store_true',help='Diagnostic finite object-relative support preload for right-hand front box only; default off.')")
line=next(x for x in s.splitlines() if x.startswith('if args.front_corridor_midpoint_replan and not'))
change(line,"if args.front_box_material_preload and not (args.role=='diagnostic' and args.front_corridor_midpoint_replan and args.front_loaded_z_priority and args.front_initial_center_landing and args.front_cop_edge_speed and args.front_cop_drive_step_m==.002):\n    parser.error('Box finite preload requires complete original2mm midpoint/edge/initial/loadedZ diagnostic')\n"+line)
a='                        top_cls=CenterFrontState';b=a+"\n                        if args.front_box_material_preload and side=='right':\n                            from front_box_material_preload_route_v2 import FrontBoxMaterialPreloadState\n                            top_cls=FrontBoxMaterialPreloadState\n                            top_extra['material_preload_enabled']=True\n                            frontal_plan['front_box_material_preload']="+repr(spec);change(a,b)
a='    if args.front_corridor_midpoint_replan:\n        episode.collect_meta';b="    if args.front_box_material_preload:\n        episode.collect_meta['front_box_material_preload']="+repr(spec)+"\n        episode.collect_meta['front_box_material_preload_applied_frames']=sum(bool(r.get('front_box_material_preload',{}).get('override')) for r in frontal_log)\n"+a;change(a,b)
a="        paths.extend([STAGE/name for name in ['minimum_motion_recontact.py','recontact_scene.py','causal_response_parameters.json']])";b=a+"\n    if args.front_box_material_preload:\n        paths.extend([STAGE/'material_preload_v2.py',STAGE/'front_box_material_preload_route_v2.py'])";change(a,b)
ast.parse(s);back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(P/'collect_paired_sorting.py').read_text();S.mkdir()
for n,h in parent['stage_sha256'].items():
 assert sha(P/n)==h,n
 with (S/n).open('x') as f:f.write(s if n=='collect_paired_sorting.py' else (P/n).read_text())
helpers=['material_preload_v2.py','front_box_material_preload_route_v2.py']
for n in helpers:
 with (S/n).open('x') as f:f.write((D/n).read_text())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256={n:sha(S/n) for n in [*parent['stage_sha256'],*helpers]},collector_edits=edits,unchanged_parent_files=[n for n in parent['stage_sha256'] if n!='collect_paired_sorting.py'],runtime_helpers=helpers,specification=spec,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',D/'REPLAY_CHECK.json',D/'ROUTE_BRANCH_V2_CHECK.json',D/'CONTROL_HISTORY_V2_CHECK.json',*[D/n for n in helpers]]},collector_integrated=True,native_audit_family_ready=False,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(dict(sources=len(report['stage_sha256']),unchanged_parent_sources=len(report['unchanged_parent_files']),new_helpers=helpers,physics_started=False))
