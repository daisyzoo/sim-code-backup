"""Extend isolated release candidate; production controller remains untouched."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;repo=root.parents[1];prior=root/'staged_position_release';out=root/'staged_initial_top_release'
manifest=json.loads((prior/'MANIFEST.json').read_text())
for p,h in manifest['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
for name in ('top_contact_bypass.py','confirmed_position_release.py'):(out/name).write_bytes((prior/name).read_bytes())
(out/'initial_top_route_candidate.py').write_bytes((repo/'simfoundry/data/initial_top_route_candidate.py').read_bytes())
s=(prior/'collect_paired_sorting.py').read_text()
s=s.replace("parser.add_argument('--expert-top-confirmed-release'", "parser.add_argument('--expert-initial-top-route', action='store_true', help='Diagnostic only: far direct long transfers start with measured-support top approach; full live clearance guards retained.')\nparser.add_argument('--expert-top-confirmed-release'",1)
s=s.replace("if args.expert_top_confirmed_release and not", "if args.expert_initial_top_route and not (args.role=='diagnostic' and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag):\n    parser.error('Initial top route requires projected guarded continuous diagnostic')\nif args.expert_top_confirmed_release and not",1)
s=s.replace('    front_route_selected = False\n','    front_route_selected = False\n    initial_top_selected = False\n',1)
needle="        if frontal_plan['required']:\n            frontal_state = FrontalBypassState"
replacement="""        if args.expert_initial_top_route and not frontal_plan['required']:
            from simfoundry.data.initial_top_route_candidate import initial_top_route_candidate
            target_actor = 'parcel_box' if side == 'right' else 'mailer'
            other_actor = 'mailer' if side == 'right' else 'parcel_box'
            tq = env.scene[target_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            oq = env.scene[other_actor].data.root_quat_w.torch[0].detach().cpu().numpy().tolist()
            proposal = initial_top_route_candidate(target,initial[obstacle_key],target_size,obstacle_size,tq,oq,-1 if side=='right' else 1)
            initial_top_selected = proposal['proposed']
            frontal_plan['initial_top_proposal'] = proposal
        frontal_plan['initial_top_selected'] = initial_top_selected
        if frontal_plan['required'] or initial_top_selected:
            frontal_state = FrontalBypassState"""
assert needle in s;s=s.replace(needle,replacement,1)
s=s.replace('                frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,', "                if initial_top_selected:\n                    from simfoundry.data.initial_top_route import InitialTopRouteState\n                    top_cls, top_extra = InitialTopRouteState, dict(obstacle_size=tuple(obstacle_size))\n                    frontal_plan['initial_top_live_guards'] = dict(hand_gap_m=.005,parcel_gap_m=.01,non_target_motion_m=.01,table_margin_m=.005)\n                frontal_state = top_cls(frontal_state,side,contact_size,**top_extra,",1)
s=s.replace('(front_route_selected or frontal_state.top_mode is not None)', '(front_route_selected or initial_top_selected or frontal_state.top_mode is not None)',1)
# Only the point-kwargs observation branch gets this extension; front selection itself stays separate.
s=s.replace('                    if front_route_selected:\n                        from simfoundry.data.hand_obstacle_clearance', '                    if front_route_selected or initial_top_selected:\n                        from simfoundry.data.hand_obstacle_clearance',1)
s=s.replace("    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')", "    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')\n    paths.extend([ROOT / 'simfoundry/data/initial_top_route.py', ROOT / 'simfoundry/data/initial_top_route_candidate.py'])",1)
compile(s,str(out/'collect_paired_sorting.py'),'exec');(out/'collect_paired_sorting.py').write_text(s)
manifest.update(candidate_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.py')},scope='Isolated combined candidate: optional confirmed release and optional geometric initial top. No live core changes or physics/data admission.')
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(out)
