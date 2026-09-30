"""Prepare default-off terminal joint hold; no live frozen source changes."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_terminal_hold';stage.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();protocol=json.loads((root/'contact_stability_groups_r1/PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
shutil.copy2(root/'terminal_joint_hold_candidate.py',stage/'terminal_joint_hold.py')
s=(repo/'scripts/collect_paired_sorting.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("parser.add_argument('--expert-initial-top-route'","parser.add_argument('--expert-terminal-joint-hold', action='store_true', help='Diagnostic only: after confirmed released/clear/unloaded tracking, repeat prior11D joint target; revoke on guard or lost conditions.')\nparser.add_argument('--expert-initial-top-route'")
replace('args = parser.parse_args()',"args = parser.parse_args()\nif args.expert_terminal_joint_hold and not (args.role=='diagnostic' and args.waist_coordinated_expert and args.bounded_coupled_ik and args.trace_solved_contact_forces and not args.policy_port and not args.idle):\n    parser.error('Terminal joint hold requires coordinated bounded force-traced diagnostic expert')")
replace('    previous = np.zeros(23, dtype=np.float32)',"    previous = np.zeros(23, dtype=np.float32)\n    terminal_hold = None\n    terminal_hold_log = []\n    terminal_other_max_xy = 0.\n    if args.expert_terminal_joint_hold and task_id != 'wait_no_package':\n        from simfoundry.data.terminal_joint_hold import TerminalJointHold\n        from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease\n        terminal_hold = TerminalJointHold()\n        terminal_goal = ConfirmedPositionRelease(target[1], -1 if side=='right' else 1)")
anchor='            # The legacy expert instantly parks the inactive arm.'
block='''            if terminal_hold is not None:
                from simfoundry.data.top_contact_bypass import support_mesh, rotation_xyzw
                from simfoundry.data.contact_load_control import hand_target_vertical_load
                target_key = 'box' if side=='right' else 'mailer'
                other_key = 'mailer' if side=='right' else 'box'
                target_actor = 'parcel_box' if side=='right' else 'mailer'
                observed = snap(env,robot,hands)
                terminal_other_max_xy = max(terminal_other_max_xy,float(np.linalg.norm(np.asarray(observed[other_key])[:2]-np.asarray(initial[other_key])[:2])))
                highest_object = max(observed[key][2]+float(np.abs(np.asarray(rotation_xyzw(env.scene[actor].data.root_quat_w.torch[0].detach().cpu().numpy()))[2])@np.asarray(size)/2) for key,actor,size in [('box','parcel_box',(.14,.09,.045)),('mailer','mailer',(.15,.145,.04))])
                hand_bottoms = []
                for hand_side in ('left','right'):
                    hand_index = hands[hand_side]
                    hp = robot.data.body_pos_w.torch[0,hand_index].detach().cpu().numpy()
                    hr = np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,hand_index].detach().cpu().numpy()))
                    hand_bottoms.append(float((np.asarray(support_mesh()[hand_side])@hr.T+hp)[:,2].min()))
                coordinate = coordination_log[-1]
                inactive_side = 'left' if side=='right' else 'right'
                current_upper = robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy()
                readings = dict(mode=expert.mode,target_confirmed=bool(terminal_goal.observe(observed[target_key])),hand_clearance_m=min(hand_bottoms)-highest_object,load_n=float(hand_target_vertical_load(solved_contact_forces[-1] if solved_contact_forces else None,side,target_actor)),active_error_m=float(np.max(np.abs(np.asarray(coordinate['control_point_positions'][side])-expert.last_target_xyz))),inactive_error_m=float(np.max(np.abs(np.asarray(coordinate['palm_positions'][inactive_side])-coordinate['inactive_anchor']))),other_max_xy_m=terminal_other_max_xy,current_upper_q=current_upper.tolist(),previous_upper_command=(previous[12:23]+default[12:23]).tolist())
                held_command = terminal_hold.observe(**readings)
                if held_command is not None:
                    action[12:23] = np.asarray(held_command)-default[12:23]
                    coordinate['unexecuted_solver_waist_target_rad'] = coordinate['waist_target_rad']
                    coordinate['waist_target_rad'] = float(held_command[0])
                coordinate['terminal_joint_hold'] = held_command is not None
                terminal_hold_log.append(dict(step=step,**readings,consecutive_ready=terminal_hold.consecutive,held=held_command is not None,output_upper_command=(action[12:23]+default[12:23]).tolist()))
'''
replace(anchor,block+anchor)
replace("    if coordination_log:\n", "    if terminal_hold_log:\n        (folder / 'terminal_joint_hold.json').write_text(json.dumps(dict(rows=terminal_hold_log,training_ready=False),indent=2))\n    if coordination_log:\n")
replace("    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')", "    paths.append(ROOT / 'simfoundry/data/terminal_joint_hold.py')\n    paths.append(ROOT / 'simfoundry/data/confirmed_position_release.py')")
p=stage/'collect_paired_sorting.py';compile(s,str(p),'exec');p.write_text(s)
(stage/'MANIFEST.json').write_text(json.dumps(dict(source_sha256=protocol['source_sha256'],candidate_sha256={n:sha(stage/n) for n in ['collect_paired_sorting.py','terminal_joint_hold.py']},scope='Isolated default-off terminal hold candidate. Existing emergency modes revoke hold; full source frozen in live run. No physical trial or data approval.',training_ready=False),indent=2));print(stage)
