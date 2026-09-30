"""Build isolated default-off contact calibration; running controller stays frozen."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent;repo=root.parents[1];stage=root/'staged_contact_center';stage.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((root/'normal_contact_groups_r1/PROTOCOL.json').read_text())
for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
sources={name:(repo/sub/name).read_text() for name,sub in [('collect_paired_sorting.py','scripts'),('projected_support_reference.py','simfoundry/data')]}
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=sources['projected_support_reference.py']
s=s.replace('Tangential position is the fixed hand-hull bounding-box center.', 'Tangential position defaults to the fixed hand-hull bounding-box center; an explicit calibrated hand-local center may replace it.')
s=replace(s,'def projected_support_reference(vertices, hand_rotation, world_normal):','def projected_support_reference(vertices, hand_rotation, world_normal, *, center_local=None):')
s=replace(s,'    center=(vertices.min(axis=0)+vertices.max(axis=0))/2','''    center=(vertices.min(axis=0)+vertices.max(axis=0))/2 if center_local is None else np.asarray(center_local,dtype=float)
    if center.shape!=(3,) or not np.isfinite(center).all() or np.any(center<vertices.min(0)-.003) or np.any(center>vertices.max(0)+.003):
        raise ValueError('Invalid measured tangential center')''')
sources['projected_support_reference.py']=s
helper=(root/'contact_center_calibration_candidate.py').read_text()
helper+='''

def apply_contact_center_step(state,row,calibration,measurement,*,vertices,hand_xyz,hand_rotation,object_xyz,object_quat,reference):
    """Called once AFTER existing guards/state update. No second update/force actuation."""
    from simfoundry.data.projected_support_reference import projected_support_reference
    from simfoundry.data.top_contact_bypass import top_surface_point,rotation_xyzw
    info=dict(committed_now=False,waiting_for_contact_center=False)
    if calibration.center_local is not None or row['mode'] not in ('top_press','top_push') or getattr(state,'stop_reason',None):
        return row,reference,info
    if measurement['ready']:
        center=calibration.commit()
        new_reference=projected_support_reference(vertices,hand_rotation,np.asarray(rotation_xyzw(object_quat))[:,2],center_local=center)
        tip=np.asarray(hand_xyz)+np.asarray(hand_rotation)@new_reference['reference_local']
        old_tip=np.asarray(row['observed_support_xyz'])
        state._start_recontact(tip,'initial_contact_center_reposition')
        state.front_inset_fraction=1.;state.push_x_anchor=None
        if hasattr(state,'relative_contact_anchor'):state.relative_contact_anchor=None
        state.mode='top_lift';state.mode_step=1
        high=max(state.recontact_travel_z,float(tip[2]))
        surface=top_surface_point(object_xyz,object_quat,state.size,front_inset_fraction=1.)
        row=dict(row,target_xyz=(*tip[:2],high),mode=state.mode,control_offset_local=tuple(new_reference['reference_local']),observed_support_xyz=tip.tolist(),parcel_top_xyz=surface,corner_local=None,approach_xy_bias_m=[0.,0.],push_x_anchor_m=None,last_recontact_reason=state.last_recontact_reason,recontacts=state.recontacts,travel_height_m=state.recontact_travel_z,contact_load=dict(row['contact_load'],applied_z_bias_m=0.,stored_z_bias_m=0.))
        for k in ('object_relative_contact_anchor_xy_m','object_relative_desired_xy_m','object_relative_lead_limit_m'):row.pop(k,None)
        info.update(committed_now=True,reference_switch_world_delta_m=(tip-old_tip).tolist(),center_local=center.tolist(),effective_top_fraction=1.)
        return row,new_reference,info
    if row['mode']=='top_push':
        # The normal-load monitor can establish push before a reliable centroid.
        # Preserve the measured press until calibration, without lateral motion.
        state.top_mode='top_press';state.mode='top_press';state.mode_step=1;state.settled=0;state.command=None;state.push_x_anchor=None
        if hasattr(state,'relative_contact_anchor'):state.relative_contact_anchor=None
        surface=row['parcel_top_xyz'];xy=[surface[i]+state.approach_xy_bias[i] for i in (0,1)]
        row=dict(row,mode='top_press',target_xyz=(*xy,surface[2]+.002+row['contact_load']['applied_z_bias_m']),push_x_anchor_m=None)
        for k in ('object_relative_contact_anchor_xy_m','object_relative_desired_xy_m','object_relative_lead_limit_m'):row.pop(k,None)
        info['waiting_for_contact_center']=True
    return row,reference,info
'''
sources['contact_center_calibration.py']=helper
s=sources['collect_paired_sorting.py']
s=replace(s,"parser.add_argument('--expert-top-contact-normal-hold'", "parser.add_argument('--expert-top-contact-center-calibration', action='store_true', help='Diagnostic initial load-centroid measurement, lift and recenter before top pushing.')\nparser.add_argument('--expert-top-contact-normal-hold'")
s=replace(s,'args = parser.parse_args()',"""args = parser.parse_args()
if args.expert_top_contact_center_calibration and not (args.role=='diagnostic' and args.expert_top_contact_normal_hold and args.expert_top_projected_support and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag and not args.expert_frontal_top_visible_corner and not args.expert_frontal_top_approach_compensation and not args.expert_frontal_top_recovery_clearance_m and not args.policy_port and not args.idle):
    parser.error('Contact center calibration requires normal-held projected guarded top diagnostic, no corner/approach/recovery-height alternatives')""")
s=replace(s,'    top_contact_normal_anchor = None',"""    top_contact_normal_anchor = None
    contact_center_calibration = None
    contact_center_log = []
    if args.expert_top_contact_center_calibration and task_id != 'wait_no_package':
        from simfoundry.data.contact_center_calibration import ContactCenterCalibration
        from simfoundry.data.top_contact_bypass import support_mesh
        contact_center_calibration = ContactCenterCalibration(support_mesh()[side])""")
a="reference = projected_support_reference(support_mesh()[side], rotation_xyzw(hand_quat), np.asarray(rotation_xyzw(target_quat))[:,2])"
b="reference = projected_support_reference(support_mesh()[side], rotation_xyzw(hand_quat), np.asarray(rotation_xyzw(target_quat))[:,2], center_local=contact_center_calibration.center_local if contact_center_calibration is not None else None)"
s=replace(s,a,b)
s=replace(s,'                waypoint = frontal_state.update(palm_xyz(robot,hands[side])',"""                center_measurement = None
                if contact_center_calibration is not None:
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    center_measurement = contact_center_calibration.observe(
                        solved_contact_forces[-1] if solved_contact_forces else None,step=step,
                        mode=frontal_state.top_mode,side=side,actor=target_actor,
                        hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy(),
                        hand_rotation=np.asarray(rotation_xyzw(hand_quat)),object_xyz=parcel_xyz(env,target_actor),
                        object_normal=np.asarray(rotation_xyzw(target_quat))[:,2])
                    center_measurement['mode_before_update'] = frontal_state.top_mode
                waypoint = frontal_state.update(palm_xyz(robot,hands[side])""")
s=replace(s,"                if args.expert_frontal_top_recontact:\n                    waypoint['observed_support_offset_local']", """                if contact_center_calibration is not None and projected_support_context is not None:
                    from simfoundry.data.contact_center_calibration import apply_contact_center_step
                    waypoint,reference,center_transition=apply_contact_center_step(
                        frontal_state,waypoint,contact_center_calibration,center_measurement,
                        vertices=support_mesh()[side],hand_xyz=robot.data.body_pos_w.torch[0,hands[side]].detach().cpu().numpy(),
                        hand_rotation=np.asarray(rotation_xyzw(hand_quat)),object_xyz=parcel_xyz(env,target_actor),
                        object_quat=target_quat,reference=reference)
                    projected_support_context={k:v.tolist() for k,v in reference.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')}
                    point_kwargs['control_offset_local']=tuple(reference['reference_local'])
                    contact_center_log.append(dict(step=step,**center_measurement,**center_transition,
                        calibrated_after=contact_center_calibration.center_local is not None,mode=waypoint['mode'],
                        reference_center_local=reference['center_local'].tolist()))
                if args.expert_frontal_top_recontact:
                    waypoint['observed_support_offset_local']""")
s=replace(s,"waypoint['support_reference_scope'] = 'Virtual plane reference: tangential fixed hull center and exact lowest normal height; not a mesh contact point. Physical lowest vertex observed separately.'", "waypoint['support_reference_scope'] = ('Virtual plane reference: calibrated initial contact tangent center and exact lowest normal height; current physical COP not guaranteed.' if contact_center_calibration is not None and contact_center_calibration.center_local is not None else 'Virtual plane reference: tangential fixed hull center and exact lowest normal height; not a mesh contact point. Physical lowest vertex observed separately.')")
s=replace(s,'    if terminal_hold_log:\n',"    if contact_center_log:\n        (folder / 'contact_center_calibration.json').write_text(json.dumps(dict(rows=contact_center_log,training_ready=False),indent=2))\n    if terminal_hold_log:\n")
s=replace(s,"    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')", "    paths.append(ROOT / 'simfoundry/data/contact_normal_constraint.py')\n    paths.append(ROOT / 'simfoundry/data/contact_center_calibration.py')")
s=replace(s,"                frontal_plan['top_recontact'] = dict(", "                frontal_plan['contact_center_calibration'] = dict(enabled=args.expert_top_contact_center_calibration,required_loaded_press_samples=3,max_local_scatter_m=.001,max_tangent_reference_shift_m=.08,calibrated_top_fraction=1.,lift_before_recenter=True,guards_take_precedence=True)\n                frontal_plan['top_recontact'] = dict(")
sources['collect_paired_sorting.py']=s
for name,content in sources.items():compile(content,str(stage/name),'exec');(stage/name).write_text(content)
manifest=dict(source_protocol_sha256=sha(root/'normal_contact_groups_r1/PROTOCOL.json'),source_sha256=protocol['source_sha256'],candidate_sha256={name:sha(stage/name) for name in sources},scope='Isolated default-off candidate; normal physical batch stays frozen. No actual CLI/lifecycle/Jacobian/default-equivalence/physics result yet.',training_ready=False)
(stage/'MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(stage)
