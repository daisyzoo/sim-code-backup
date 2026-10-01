"""Stage default-off per-push-bout yaw anchor. Never install into live sources."""
from pathlib import Path
import hashlib,json
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_contact_bout_yaw';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=json.loads((w/'y_path_nearhalf_groups_r1/PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert sha(Path(p))==h,p

def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=(repo/'simfoundry/data/waist_coordination.py').read_text();s=once(s,'active_normal_anchor_local=None):','active_normal_anchor_local=None, active_bout_yaw_anchor=None):')
s=once(s,'    jac = torch.cat(rows)\n    error = torch.cat(errors)', '''    yaw_record = None
    if active_bout_yaw_anchor is not None:
        if active_normal_anchor_local is None:
            raise ValueError('Contact-bout yaw requires original normal tracking')
        from simfoundry.data.contact_bout_yaw import contact_bout_yaw_constraint
        constraint = contact_bout_yaw_constraint(normal_rotation, angular_jac.detach().cpu().numpy(), active_bout_yaw_anchor)
        rows.append(position_jac.new_tensor(constraint['jacobian']))
        errors.append(position_jac.new_tensor(constraint['error']))
        yaw_record = {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in constraint.items()}
    jac = torch.cat(rows)
    error = torch.cat(errors)''')
s=once(s,"'contact_normal_tracking':normal_record}","'contact_normal_tracking':normal_record, 'contact_bout_yaw_tracking':yaw_record}");(stage/'waist_coordination.py').write_text(s)
s=(repo/'scripts/collect_paired_sorting.py').read_text();s=once(s,"parser.add_argument('--expert-top-contact-normal-hold',", "parser.add_argument('--expert-top-contact-bout-yaw-hold', action='store_true', help='Diagnostic top pushes: latch hand heading each push bout, reset on recovery/guard/release. Retain original normal tracking and quality gates.')\nparser.add_argument('--expert-top-contact-normal-hold',")
s=once(s,'if args.expert_top_contact_normal_hold and not',"if args.expert_top_contact_bout_yaw_hold and not (args.role=='diagnostic' and args.expert_top_contact_normal_hold and args.expert_top_projected_support and args.waist_coordinated_expert and args.bounded_coupled_ik and args.trace_solved_contact_forces and not args.policy_port and not args.idle):\n    parser.error('Contact-bout yaw requires traced bounded coordinated diagnostic top expert with original normal/projected support')\nif args.expert_top_contact_normal_hold and not")
s=once(s,'    top_contact_normal_anchor = None','    top_contact_bout_yaw = None\n    top_contact_normal_anchor = None')
needle="            if args.waist_coordinated_expert:\n                from simfoundry.data.waist_coordination import coordinated_step"
s=once(s,needle,"""            active_bout_yaw_anchor = None
            if args.expert_top_contact_bout_yaw_hold and frontal_plan is not None:
                from simfoundry.data.contact_bout_yaw import ContactBoutYaw
                from simfoundry.data.top_contact_bypass import rotation_xyzw
                if top_contact_bout_yaw is None:
                    top_contact_bout_yaw = ContactBoutYaw()
                bout_rotation = rotation_xyzw(robot.data.body_quat_w.torch[0,hands[side]].detach().cpu().numpy()) if expert.mode=='top_push' else None
                active_bout_yaw_anchor = top_contact_bout_yaw.update(expert.mode, bout_rotation)
"""+needle)
s=once(s,'active_normal_anchor_local=active_normal_anchor, trace_jacobian=','active_normal_anchor_local=active_normal_anchor, active_bout_yaw_anchor=active_bout_yaw_anchor, trace_jacobian=')
s=once(s,"    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')","    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')\n    paths.append(ROOT / 'simfoundry/data/contact_bout_yaw.py')");(stage/'collect_paired_sorting.py').write_text(s)
files=['collect_paired_sorting.py','waist_coordination.py','contact_bout_yaw.py']
for name in files:compile((stage/name).read_text(),name,'exec')
report=dict(installed=False,source_sha256=protocol['source_sha256'],candidate_sha256={name:sha(stage/name) for name in files},scope='Default-off diagnostic-only flag; applies same top_push rule to both arms and all top routes, latch most horizontal local hand axis on each first push, keep heading during bout, reset whenever mode is not top_push. Adds1weighted angular task while retaining original normal task, position Jacobian trace, limits, action filtering, guards, zero start, release and hold. Does not alter object state/force/camera. Historical full-episode orientation holds failed; this per-bout candidate still needs actual staged wiring and independent live audit and complete-group physics. Pilot enablement requires explicit future protocol/schema update, no silent fresh admission.',training_ready=False)
(stage/'MANIFEST.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
