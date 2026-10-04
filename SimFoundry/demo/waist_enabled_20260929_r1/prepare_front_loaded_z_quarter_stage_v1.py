"""Prepare an isolated default-off quarter-Z collector; do not launch physics."""
from pathlib import Path
import ast,json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;P=W/'staged_front_corridor_lateral_v1';D=W/'staged_front_loaded_z_quarter_v1';C=W/'front_loaded_z_fraction_candidate_v1';R=W/'front_loaded_z_quarter_preparation_r1';D.mkdir(exist_ok=False);R.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};copies=[]
for p in P.iterdir():
 if p.is_file():shutil.copy2(p,D/p.name);copies.append(p.name);sources[str(p)]=sha(p)
shutil.copy2(C/'front_loaded_z_fraction.py',D/'front_loaded_z_fraction.py');sources[str(C/'front_loaded_z_fraction.py')]=sha(C/'front_loaded_z_fraction.py')
p=D/'collect_paired_sorting.py';s=p.read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
anchor="parser.add_argument('--front-loaded-z-priority',action='store_true',help='Diagnostic certified nominal loadedZ refinement after actual front capture; default off.')"
replace(anchor,anchor+"\nparser.add_argument('--front-loaded-z-quarter',action='store_true',help='Diagnostic quarter interpolation of captured-front loaded Z target; original guards, default off.')")
anchor='if args.front_loaded_z_priority and not ('
line=next(line for line in s.splitlines() if line.startswith(anchor));replace(line,"if args.front_loaded_z_quarter and not (args.front_loaded_z_priority and args.joint_transport_clearance and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Quarter Z requires diagnostic original loaded priority and joint transport; no policy or training collection')\n"+line)
anchor='            if front_loaded_z_priority_controller is None:front_loaded_z_priority_controller=FrontLoadedZPriority(clearance_guard)'
replace(anchor,"            if args.front_loaded_z_quarter and front_loaded_z_priority_controller is None:\n                from front_loaded_z_fraction import FrontLoadedZFraction\n                front_loaded_z_priority_controller=FrontLoadedZFraction(clearance_guard,fraction=.25)\n"+anchor)
anchor="    if args.front_loaded_z_priority:\n        episode.collect_meta['front_loaded_z_priority']=True"
replace(anchor,"    if args.front_loaded_z_quarter:\n        episode.collect_meta['front_loaded_z_quarter']=dict(version='front_loaded_z_quarter_v1',fraction=.25,z_target='parent_linear_achieved_to_original_requested',original_task_retained=True,training_ready=False)\n"+anchor)
anchor="    if args.front_loaded_z_priority:\n        paths.extend(STAGE/name for name in ['front_loaded_z_priority.py','loaded_z_priority_solver.py','loaded_z_priority_checks.py','loaded_z_priority_stationarity.py'])"
replace(anchor,anchor+"\n    if args.front_loaded_z_quarter:\n        paths.append(STAGE/'front_loaded_z_fraction.py')")
ast.parse(s);p.write_text(s)
# Exact byte restoration independently establishes all text edits are additive.
reverse=s
for edit in reversed(edits):assert reverse.count(edit['new'])==1;reverse=reverse.replace(edit['new'],edit['old'])
assert reverse==(P/'collect_paired_sorting.py').read_text()
for name in copies:
 if name!='collect_paired_sorting.py':assert sha(D/name)==sha(P/name)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),stage=str(D),parent_files=len(copies),new_helper='front_loaded_z_fraction.py',collector_edits=edits,reverse_exact_parent=True,other_parent_files_unchanged=True,source_sha256=sources,candidate_sha256={str(p):sha(p) for p in D.iterdir() if p.is_file()},collector_wired=True,parser_runtime_checked=False,independent_record_audit_pending=True,physical_launch_ready=False,physics_started=False,training_ready=False)
with (R/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stage=str(D),parent_files=len(copies),collector_edits=len(edits),reverse_exact_parent=True,physical_launch_ready=False)))
