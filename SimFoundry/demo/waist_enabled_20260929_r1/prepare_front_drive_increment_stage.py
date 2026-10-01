"""Isolate optional front drive increment on closed core-slice parent, no motion FF."""
from pathlib import Path
import json,hashlib,ast
w=Path(__file__).resolve().parent;parent=w/'staged_rear_cop_core_slice';probe=w/'staged_front_drive_increment_probe';dst=w/'staged_front_drive_increment';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((parent/'MANIFEST.json').read_text());check=json.loads((probe/'DRIVE_INCREMENT_REPLAY_CHECK.json').read_text());audit=json.loads((probe/'DRIVE_INCREMENT_AUDITOR_CHECK.json').read_text())
assert check['passed'] and audit['passed'] and check['source_sha256']['front_cop_route.py']==sha(probe/'front_cop_route.py') and audit['counterfactual_fixture_sha256']==sha(probe/'DRIVE_INCREMENT_REPLAY_CHECK.json') and audit['auditor_sha256']==sha(w/'audit_front_drive_increment_live.py')
for n,h in m['source_sha256'].items():assert sha(parent/n)==h
# Probe used a newer stage's front files; they are byte-identical to this parent.
prep=json.loads((probe/'PREPARATION.json').read_text());assert prep['parent_wrapper_sha256']==sha(parent/'front_cop_route.py') and prep['unchanged_helper_sha256']==sha(parent/'contact_slip_following.py')
dst.mkdir(exist_ok=False)
for n in m['source_sha256']:(dst/n).write_bytes((parent/n).read_bytes())
(dst/'front_cop_route.py').write_bytes((probe/'front_cop_route.py').read_bytes())
p=dst/'collect_paired_sorting.py';s=p.read_text()
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
rep("parser.add_argument('--front-cop-route-axis',", "parser.add_argument('--front-cop-drive-step-m',type=float,default=.001,help='Diagnostic front-only COP drive increment1..3mm; changed value requires front route-axis control.')\nparser.add_argument('--front-cop-route-axis',")
rep('args = parser.parse_args()',"args = parser.parse_args()\nif not .001<=args.front_cop_drive_step_m<=.003:\n    parser.error('Front COP drive increment must be finite1..3mm')\nif args.front_cop_drive_step_m!=.001 and not args.front_cop_route_axis:\n    parser.error('Changed front COP drive increment requires route-axis control')")
rep("                        top_extra['cop_slip_enabled']=True", "                        top_extra['cop_slip_enabled']=True\n                        top_extra['cop_drive_step_m']=args.front_cop_drive_step_m")
rep("feedback_projection='orthogonal_to_current_goal_direction',drive_step_m=.001,feedback_gain=.05", "feedback_projection='orthogonal_to_current_goal_direction',drive_step_m=args.front_cop_drive_step_m,feedback_gain=.05")
p.write_text(s)
for p in dst.glob('*.py'):ast.parse(p.read_text())
unchanged=[n for n in m['source_sha256'] if n not in ['collect_paired_sorting.py','front_cop_route.py']]
for n in unchanged:assert sha(dst/n)==m['source_sha256'][n]
(dst/'PREPARATION.json').write_text(json.dumps(dict(parent_stage=str(parent.resolve()),parent_manifest_sha256=sha(parent/'MANIFEST.json'),probe_replay_sha256=sha(probe/'DRIVE_INCREMENT_REPLAY_CHECK.json'),probe_auditor_sha256=sha(probe/'DRIVE_INCREMENT_AUDITOR_CHECK.json'),source_sha256={n:sha(dst/n) for n in m['source_sha256']},unchanged_parent_helpers=unchanged,default_step_m=.001,planned_candidate_step_m=.002,collector_wired_in_source=True,cli_checked=False,collector_wiring_checked=False,physical_started=False,training_ready=False,scope='Baseline is fully closed rear_core_slice_groups_r1, not currently running unsuccessful moving-slice experiment. Front helper bytes unchanged, wrapper passes explicit drive parameter. Rear moving-slice FF is absent. Complete CLI/source/wiring and unchanged rear checks plus independent audits before freezing/run.'),indent=2));print(dst)
