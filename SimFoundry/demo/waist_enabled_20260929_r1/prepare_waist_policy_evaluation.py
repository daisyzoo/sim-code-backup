"""Prepare explicit policy-only extended waist evaluation; never modify live sources."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;repo=W.parents[1];live=repo/'scripts/collect_paired_sorting.py';stage=W/'staged_waist_policy_evaluation'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=W/'bounded_top_lead24_groups_r1/PROTOCOL.json'
frozen=json.loads(protocol.read_text())['source_sha256']
for p,h in frozen.items():assert sha(p)==h,p
text=live.read_text()
def replace_once(old,new):
 global text
 assert text.count(old)==1,old
 text=text.replace(old,new)
replace_once("parser.add_argument('--extended-waist-diagnostic',", "parser.add_argument('--waist-policy-evaluation', action='store_true', help='Explicit h10 policy diagnostic with enabled waist up to1rad; model/processor/budget must be frozen separately. Never expert data admission.')\nparser.add_argument('--extended-waist-diagnostic',")
replace_once("if args.extended_waist_diagnostic and (", "if args.waist_policy_evaluation and not (args.role == 'diagnostic' and args.motion_protocol == 'waist_yaw_enabled_v1' and 0 < args.policy_port < 65536 and args.horizon == 10 and args.environment_seed is not None and not args.extended_waist_diagnostic and not args.waist_coordinated_expert and not args.waist_probe and not args.idle and not args.policy_max_action_step and not args.wait_force_n and not args.push_force_n and args.prompt_variant == 'short'):\n    parser.error('Waist policy evaluation requires explicit enabled h10 policy, environment seed, original prompts, no expert/probe/force/slew changes')\nif args.extended_waist_diagnostic and (")
replace_once('(1.0 if args.extended_waist_diagnostic else .80)', '(1.0 if (args.extended_waist_diagnostic or args.waist_policy_evaluation) else .80)')
replace_once("'extended_waist_diagnostic': args.extended_waist_diagnostic,", "'extended_waist_diagnostic': args.extended_waist_diagnostic, 'waist_policy_evaluation': args.waist_policy_evaluation,")
compile(text,str(stage/'collect_paired_sorting.py'),'exec')
stage.mkdir(exist_ok=False);(stage/'collect_paired_sorting.py').write_text(text)
(stage/'MANIFEST.json').write_text(json.dumps(dict(live_collector_sha256=sha(live),candidate_collector_sha256=sha(stage/'collect_paired_sorting.py'),source_protocol_sha256=sha(protocol),source_sha256=frozen,preparer_sha256=sha(__file__),applied=False,physics_validated=False,training_ready=False),indent=2))
print(stage)
