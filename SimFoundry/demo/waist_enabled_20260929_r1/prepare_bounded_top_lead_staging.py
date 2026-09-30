"""Isolate post-guard calibrated object-relative top waypoint; live frozen."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;repo=root.parents[1];run=root/'contact_center_groups_r1';stage=root/'staged_bounded_top_lead';stage.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((run/'PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
s=(repo/'scripts/collect_paired_sorting.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("parser.add_argument('--expert-top-contact-center-calibration',", "parser.add_argument('--expert-top-object-relative-lead-m', type=float, default=0., help='Diagnostic calibrated top desired XY lead in metres;0 disables, .012..030. Original guards and3mm slew retained; no claim of realized contact lead.')\nparser.add_argument('--expert-top-contact-center-calibration',")
replace("if args.expert_top_contact_center_calibration and not", "if args.expert_top_object_relative_lead_m and not (.012 <= args.expert_top_object_relative_lead_m <= .030 and args.expert_top_contact_center_calibration and not args.expert_front_object_relative_lead):\n    parser.error('Bounded top lead requires calibrated contact reference, .012..030m and no competing front lead')\nif args.expert_top_contact_center_calibration and not")
replace('    contact_center_log = []', '''    contact_center_log = []
    bounded_top_lead = None
    if args.expert_top_object_relative_lead_m and task_id != 'wait_no_package':
        from simfoundry.data.bounded_top_lead import BoundedTopLead
        bounded_top_lead = BoundedTopLead(args.expert_top_object_relative_lead_m)''')
replace("                if args.expert_frontal_top_recontact:\n                    waypoint['observed_support_offset_local']", '''                if bounded_top_lead is not None:
                    from simfoundry.data.bounded_top_lead import route_goal
                    bounded_goal = route_goal(frontal_state,waypoint)
                    if bounded_goal is None or contact_center_calibration.center_local is None:
                        bounded_top_lead.previous = None
                    else:
                        lead_record = bounded_top_lead.update(waypoint['mode'],parcel_xyz(env,target_actor)[:2],bounded_goal,waypoint['observed_support_xyz'][:2],step_m=frontal_state.drag_step_m)
                        waypoint['target_xyz'] = (*lead_record['command_xy'],waypoint['target_xyz'][2])
                        frontal_state.command = waypoint['target_xyz']
                        waypoint['bounded_top_object_lead'] = dict(lead_record,goal_xy=bounded_goal)
                if args.expert_frontal_top_recontact:
                    waypoint['observed_support_offset_local']''')
replace("    paths.append(ROOT / 'simfoundry/data/contact_center_calibration.py')", "    paths.append(ROOT / 'simfoundry/data/contact_center_calibration.py')\n    paths.append(ROOT / 'simfoundry/data/bounded_top_lead.py')")
replace("                frontal_plan['contact_center_calibration'] = dict(", "                frontal_plan['bounded_top_object_lead'] = dict(enabled=bool(args.expert_top_object_relative_lead_m),desired_axis_lead_m=args.expert_top_object_relative_lead_m,requires_calibrated_reference=True,original_guard_priority=True,scope='Desired waypoint bound; slew lag after abrupt object motion is logged, not assumed bounded realized contact.')\n                frontal_plan['contact_center_calibration'] = dict(")
compile(s,str(stage/'collect_paired_sorting.py'),'exec');(stage/'collect_paired_sorting.py').write_text(s);(stage/'bounded_top_lead.py').write_text((root/'bounded_top_lead_candidate.py').read_text())
(stage/'MANIFEST.json').write_text(json.dumps(dict(parent_protocol_sha256=sha(run/'PROTOCOL.json'),source_sha256=protocol['source_sha256'],candidate_sha256={n:sha(stage/n) for n in ('collect_paired_sorting.py','bounded_top_lead.py')},scope='Unapplied isolated post-guard waypoint candidate, requires contact-center calibration. Actual CLI/AST/solver and physical validation pending.',training_ready=False),indent=2));print(stage)
