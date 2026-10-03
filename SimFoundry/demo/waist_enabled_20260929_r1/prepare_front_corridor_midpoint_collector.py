"""Create a new isolated collector stage; preserve the bound route draft and Z run."""
from pathlib import Path
import datetime,hashlib,json,shutil
W=Path(__file__).resolve().parent;D=W/'staged_front_corridor_midpoint';S=W/'staged_front_corridor_midpoint_integrated';P=W/'staged_front_loaded_z_priority'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[D/'DRAFT_CHECK.json',D/'SINGLE_STEP_JOINT_PROPOSAL_CHECK.json'];sources={}
for p in checks:
 d=json.loads(p.read_text());assert d['passed']
 for n,h in d['source_sha256'].items():assert sha(n)==h,n
 sources[str(p)]=sha(p)
assert not S.exists();S.mkdir()
manifest=json.loads((P/'VALIDATED_PREPARATION.json').read_text())['source_sha256']
# Use the parent's declared dependency set, replacing only the already-checked
# draft route and adding its pure midpoint selector. No stale validation copied.
for name,h in manifest.items():
 p=Path(name)
 if not p.is_absolute():p=P/p
 assert p.exists() and sha(p)==h,(name,p)
 src=D/p.name;assert src.is_file(),src
 if p.name!='front_initial_center_route.py':assert sha(src)==h
 shutil.copy2(src,S/src.name);sources[str(src)]=sha(src)
shutil.copy2(D/'front_corridor_midpoint_runtime.py',S/'front_corridor_midpoint_runtime.py');sources[str(D/'front_corridor_midpoint_runtime.py')]=sha(D/'front_corridor_midpoint_runtime.py')
p=S/'collect_paired_sorting.py';text=p.read_text();edits=[]
def change(old,new):
 global text
 assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new);edits.append(dict(old=old,new=new))
old="parser.add_argument('--front-loaded-z-priority',action='store_true',help='Diagnostic certified nominal loadedZ refinement after actual front capture; default off.')"
change(old,old+"\nparser.add_argument('--front-corridor-midpoint-replan',action='store_true',help='Diagnostic midpoint recovery of an invalid front-X route; preserves original table/parcel/hand and latched guards; default off.')")
old="if args.front_loaded_z_priority and not (args.front_initial_center_landing"
change(old,"if args.front_corridor_midpoint_replan and not (args.front_loaded_z_priority and args.front_initial_center_landing and args.front_diagonal_entry and args.front_micro_repair_retention):\n    raise ValueError('Front corridor midpoint requires loadedZ, initial center, diagonal entry and original micro repair guards')\n"+old)
old="                        top_cls=CenterFrontState\n"
change(old,old+"                        if args.front_corridor_midpoint_replan:\n                            top_extra['corridor_midpoint_replan']=True\n                            frontal_plan['front_corridor_midpoint']=dict(enabled=True,phase='front_x_only',trigger='original_goal_violates_table_margin_and_positive_safe_interval',table_margin_m=.005,parcel_planning_margin_m=args.expert_front_clearance_m,original_extra_reserve_m=.003,extra_reserve_may_be_replanned=True,require_axis_and_diagonal_paths=True,preserve_other_guards=True,preserve_latched_stop=True,training_ready=False,scope='Observed object-envelope midpoint only; actual joint/force/physics audits remain required.')\n")
old="    if args.front_loaded_z_priority:\n        episode.collect_meta['front_loaded_z_priority']=True"
change(old,"    if args.front_corridor_midpoint_replan:\n        episode.collect_meta['front_corridor_midpoint_replan']=True\n        episode.collect_meta['front_corridor_midpoint_replanned_frames']=sum(bool(r.get('front_corridor_midpoint',{}).get('changed')) for r in frontal_log)\n"+old)
old="'front_initial_center_adapter.py', 'front_initial_center_runtime.py']])"
change(old,"'front_initial_center_adapter.py', 'front_initial_center_runtime.py', 'front_corridor_midpoint_runtime.py']])")
p.write_text(text);restored=text
for e in reversed(edits):restored=restored.replace(e['new'],e['old'])
assert restored==(D/'collect_paired_sorting.py').read_text()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(P),bound_route_draft=str(D),edits=edits,collector_exact_reverse_restoration=True,source_sha256=sources,stage_sha256={p.name:sha(p) for p in S.iterdir() if p.is_file()},default_enabled=False,physical_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stage=str(S),files=len(report['stage_sha256']),edits=len(edits),default_enabled=False,physical_started=False),indent=2))
