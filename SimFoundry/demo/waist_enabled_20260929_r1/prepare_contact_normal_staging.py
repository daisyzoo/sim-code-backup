"""Stage optional top-contact tilt preservation without changing live sources."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_normal';stage.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((root/'terminal_hold_front09_groups_r1/PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert sha(p)==h,p

def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
shutil.copyfile(root/'contact_normal_constraint_candidate.py',stage/'contact_normal_constraint.py')
s=(repo/'simfoundry/data/waist_coordination.py').read_text()
s=once(s,'active_support_reference=None):','active_support_reference=None, active_normal_anchor_local=None):')
s=once(s,'    jac = torch.cat(rows)\n    error = torch.cat(errors)', '''    position_jac = torch.cat(rows)
    normal_record = None
    if active_normal_anchor_local is not None:
        from simfoundry.data.contact_normal_constraint import contact_normal_constraint
        from simfoundry.data.top_contact_bypass import rotation_xyzw
        body = hands[state.side]
        normal_rotation = rotation_xyzw(robot.data.body_quat_w.torch[0,body].detach().cpu().numpy())
        angular_jac = robot.data.body_link_jacobian_w.torch[0,body-1 if robot.is_fixed_base else body,3:,cols]
        constraint = contact_normal_constraint(normal_rotation,angular_jac.detach().cpu().numpy(),active_normal_anchor_local)
        rows.append(position_jac.new_tensor(constraint['jacobian']))
        errors.append(position_jac.new_tensor(constraint['error']))
        normal_record = {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in constraint.items()}
    jac = torch.cat(rows)
    error = torch.cat(errors)''')
s=once(s,"'full_arm_clearance_verified':False, 'active_support_reference':active_support_reference}","'full_arm_clearance_verified':False, 'active_support_reference':active_support_reference, 'contact_normal_tracking':normal_record}")
s=once(s,"result['control_jacobian_world']=jac.detach().cpu().numpy().tolist()", "result['control_jacobian_world']=position_jac.detach().cpu().numpy().tolist()")
(stage/'waist_coordination.py').write_text(s)
s=(repo/'scripts/collect_paired_sorting.py').read_text()
s=once(s,"parser.add_argument('--expert-terminal-joint-hold',", "parser.add_argument('--expert-top-contact-normal-hold', action='store_true', help='Diagnostic top routes: latch hand-local world-up on first press, preserve tilt through recontacts while world yaw remains free. Original guards keep precedence.')\nparser.add_argument('--expert-terminal-joint-hold',")
s=once(s,'if args.expert_terminal_joint_hold and not', "if args.expert_top_contact_normal_hold and not (args.role=='diagnostic' and args.expert_frontal_top_recontact and args.waist_coordinated_expert and args.bounded_coupled_ik and args.trace_solved_contact_forces and not args.policy_port and not args.idle):\n    parser.error('Front contact normal hold requires traced bounded coordinated top diagnostic expert')\nif args.expert_terminal_joint_hold and not")
s=once(s,'    terminal_hold = None','    top_contact_normal_anchor = None\n    terminal_hold = None')
s=once(s,"            if args.waist_coordinated_expert:\n                from simfoundry.data.waist_coordination import coordinated_step", """            active_normal_anchor = None
            if args.expert_top_contact_normal_hold and frontal_plan is not None:
                if top_contact_normal_anchor is None and expert.mode in ('top_press','top_push'):
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    actual_hand_rotation = np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,hands[side]].detach().cpu().numpy()))
                    top_contact_normal_anchor = (actual_hand_rotation.T@np.array([0.,0.,1.])).tolist()
                if top_contact_normal_anchor is not None and expert.mode in ('top_lift','top_cross','top_descend','top_press','top_push'):
                    active_normal_anchor = top_contact_normal_anchor
            if args.waist_coordinated_expert:
                from simfoundry.data.waist_coordination import coordinated_step""")
s=once(s,"waist_preference=waist_preference, trace_jacobian=", "waist_preference=waist_preference, active_normal_anchor_local=active_normal_anchor, trace_jacobian=")
s=once(s,"    paths.append(ROOT / 'simfoundry/data/terminal_joint_hold.py')", "    paths.append(ROOT / 'simfoundry/data/terminal_joint_hold.py')\n    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')")
(stage/'collect_paired_sorting.py').write_text(s)
for name in ['collect_paired_sorting.py','waist_coordination.py','contact_normal_constraint.py']:compile((stage/name).read_text(),str(stage/name),'exec')
manifest=dict(source_sha256=protocol['source_sha256'],candidate_sha256={name:sha(stage/name) for name in ['collect_paired_sorting.py','waist_coordination.py','contact_normal_constraint.py']},scope='Isolated default-off candidate. Preserve hand-local world-up (two attitude axes), free world yaw, all top routes after first press; across recontacts, disabled on guard/release. No direct parcel/force changes, same original gates. Wiring/actual staged solver/physical tests pending.',training_ready=False)
(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(stage)
