"""Prepare isolated rear-only Y governor and full loaded-IK trace, not freeze/run."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_front_edge_speed';probe=w/'staged_rear_coupled_progress_probe';dst=w/'staged_rear_coupled_progress';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((parent/'MANIFEST.json').read_text());assert not dst.exists()
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
for n in ['CHECK.json','LIFECYCLE_CHECK.json','AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json','EXECUTION_REPLAY_CHECK.json']:assert json.loads((probe/n).read_text())['passed']
assert json.loads((probe/'AUDITOR_CHECK.json').read_text())['auditor_sha256']==sha(w/'audit_rear_coupled_progress_live.py')
assert json.loads((probe/'EXECUTION_REPLAY_CHECK.json').read_text())['auditor_sha256']==sha(w/'audit_rear_coupled_execution_live.py')
dst.mkdir()
for n in m['source_sha256']:(dst/n).write_bytes((parent/n).read_bytes())
for n in ['rear_cop_route.py','rear_coupled_progress.py']:(dst/n).write_bytes((probe/n).read_bytes())
p=dst/'collect_paired_sorting.py';s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
rep("parser.add_argument('--rear-core-slice-feedback',", "parser.add_argument('--rear-coupled-progress', action='store_true', help='Diagnostic rear-only current-COP near-edge Y governor, preserving original X/Z and guards; full loaded IK trace required.')\nparser.add_argument('--rear-core-slice-feedback',")
rep('args = parser.parse_args()',"""args = parser.parse_args()
if args.rear_coupled_progress and not (args.rear_core_slice_feedback and args.waist_coordinated_expert and args.bounded_coupled_ik and args.expert_top_contact_normal_hold and not args.expert_top_contact_bout_yaw_hold and not args.policy_port and not args.idle):
    parser.error('Rear coupled progress requires core-slice rear COP, bounded normal-held coordinated expert without yaw-hold/policy/idle')""")
rep("                    region_approach = RegionApproachLifecycle(**region_extra)","""                    if args.rear_coupled_progress:
                        top_extra['rear_coupled_progress_enabled']=True
                        frontal_plan['rear_coupled_progress']=dict(enabled=True,core_inset_m=.01,parent_xz_unchanged=True,original_guard_priority=True,first_loaded_preserved=True,infeasible_fallback='preserve_parent',current_previous_packet_only=True,full_push_ik_trace=True)
                    region_approach = RegionApproachLifecycle(**region_extra)""")
rep('trace_jacobian=bool(args.trace_control_jacobian_every and step % args.trace_control_jacobian_every == 0)',"trace_jacobian=bool((args.trace_control_jacobian_every and step % args.trace_control_jacobian_every == 0) or (args.rear_coupled_progress and frontal_plan is not None and frontal_plan.get('rear_coupled_progress',{}).get('enabled') and expert.mode=='top_push'))")
rep("'rear_cop_route.py','front_edge_speed.py']])", "'rear_cop_route.py','front_edge_speed.py','rear_coupled_progress.py']])")
p.write_text(s)
for f in dst.glob('*.py'):ast.parse(f.read_text())
unchanged=[n for n in m['source_sha256'] if n not in ['collect_paired_sorting.py','rear_cop_route.py']]
for n in unchanged:assert sha(dst/n)==sha(parent/n)
report=dict(parent_stage=str(parent),parent_manifest_sha256=sha(parent/'MANIFEST.json'),source_sha256={n:sha(dst/n) for n in [*m['source_sha256'],'rear_coupled_progress.py']},unchanged_parent_helpers=unchanged,probe_checks_sha256={n:sha(probe/n) for n in ['CHECK.json','LIFECYCLE_CHECK.json','AUDITOR_CHECK.json','AUDITOR_ENTRY_CHECK.json','EXECUTION_REPLAY_CHECK.json']},auditor_sha256=sha(w/'audit_rear_coupled_progress_live.py'),execution_auditor_sha256=sha(w/'audit_rear_coupled_execution_live.py'),expected_archive_sources=57,collector_wired_in_source=True,cli_checked=False,actual_collector_checked=False,physical_started=False,training_ready=False,scope='Frozen front-edge parent copied; only collector/rear wrapper changed plus new helper. Rear current measured near-edge reference-direction Y scaling0..1, X/Z and original mode guards unchanged. Force full Jacobian/q/side logging on every selected rear top_push for exact raw action replay. Await actual CLI/source/hook/boundary tests and full current8+2closure before freeze/physics. No physical or data admission claim.')
(dst/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(str(dst),'sources',len(report['source_sha256']),'unchanged',len(unchanged))
