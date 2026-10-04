"""Isolated quarter-height contract repair; unchanged parent with flag off.
No camera/contact-window change, no physical launch, no training admission.
"""
from pathlib import Path
import ast,json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent;P=W/'staged_front_loaded_z_quarter_v1';S=W/'staged_front_effective_height_v1';D=W/'front_effective_height_preparation_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();S.mkdir(exist_ok=False);D.mkdir(exist_ok=False);sources={};copies=[]
for p in P.iterdir():
 if p.is_file():shutil.copy2(p,S/p.name);copies.append(p.name);sources[str(p)]=sha(p)
helpers=['effective_loaded_contact_task_v1.py','joint_transport_effective_height_solver_v1.py','joint_transport_effective_height_certificate_v1.py','joint_transport_effective_height_runtime_v1.py']
for n in helpers:shutil.copy2(W/n,S/n);sources[str(W/n)]=sha(W/n)
p=S/'collect_paired_sorting.py';s=p.read_text();edits=[]
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--front-loaded-z-quarter',action='store_true',help='Diagnostic quarter interpolation of captured-front loaded Z target; original guards, default off.')"
replace(a,a+"\nparser.add_argument('--joint-transport-effective-quarter-height',action='store_true',help='Diagnostic bind transport contact height to verified quarter-loaded parent; full task objective and original gates retained, default off.')")
a='if args.front_loaded_z_quarter and not (';line=next(v for v in s.splitlines() if v.startswith(a));replace(line,"if args.joint_transport_effective_quarter_height and not (args.front_loaded_z_quarter and args.front_loaded_z_priority and args.joint_transport_clearance and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Effective quarter transport height requires explicit diagnostic quarter-loaded joint transport; no policy or training collection')\n"+line)
a='            if joint_transport_controller is None:joint_transport_controller=JointTransportRuntime(clearance_guard,ROOT,STAGE,enabled=True)'
replace(a,"            if args.joint_transport_effective_quarter_height and joint_transport_controller is None:\n                from joint_transport_effective_height_runtime_v1 import JointTransportRuntime as EffectiveHeightTransportRuntime\n                joint_transport_controller=EffectiveHeightTransportRuntime(clearance_guard,ROOT,STAGE,enabled=True,effective_quarter_height=True)\n"+a)
a='        from joint_transport_runtime import SPEC as JOINT_TRANSPORT_SPEC'
replace(a,a+"\n        if args.joint_transport_effective_quarter_height:\n            JOINT_TRANSPORT_SPEC=dict(JOINT_TRANSPORT_SPEC,version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True,contact_height_target='verified_effective_quarter_task',original_full_task_objective=True,original_height_tolerance_m=2e-7)\n            episode.collect_meta['joint_transport_effective_quarter_height']=True")
a="        paths.extend(STAGE/name for name in ['joint_transport_solver.py','joint_transport_certificate.py','joint_transport_paths.py','joint_transport_paths_original.py','bounded_support_paths_v1.py','support_cache_probe.py','SUPPORT_ERROR_BOUND.md','joint_transport_runtime.py','audit_front_recontact_center_events.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py'])"
replace(a,a+"\n    if args.joint_transport_effective_quarter_height:\n        paths.extend(STAGE/name for name in "+repr(helpers)+")")
ast.parse(s);p.write_text(s);reverse=s
for e in reversed(edits):assert reverse.count(e['new'])==1;reverse=reverse.replace(e['new'],e['old'])
assert reverse==(P/'collect_paired_sorting.py').read_text()
for n in copies:
 if n!='collect_paired_sorting.py':assert sha(S/n)==sha(P/n)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),stage=str(S),parent_files=len(copies),helpers=helpers,collector_edits=edits,reverse_exact_parent=True,source_sha256=sources,candidate_sha256={str(p):sha(p) for p in S.iterdir() if p.is_file()},physical_launch_ready=False,training_ready=False)
with (D/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(parent_files=len(copies),new_helpers=len(helpers),collector_edits=len(edits),reverse_exact_parent=True,physical_launch_ready=False)))
