"""Build quarantined default-off collector wiring without changing live sources."""
from pathlib import Path
import hashlib,json
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_contact_patch_approach'
# Preserve original positional constructor compatibility in isolated state copy.
p=stage/'region_top_contact.py';s=p.read_text();s=s.replace('    selected_surface_local_xy: tuple|None=None\n','');needle='    def _start_recontact(self,tip,reason):';s=s.replace(needle,'    selected_surface_local_xy: tuple|None=None\n\n'+needle);p.write_text(s)
s=(repo/'scripts/collect_paired_sorting.py').read_text()
def replace(old,new):
 global s
 assert s.count(old)==1,(old[:70],s.count(old));s=s.replace(old,new)
replace('ROOT = Path(__file__).resolve().parents[1]','ROOT = Path(__file__).resolve().parents[3]\nSTAGE = Path(__file__).resolve().parent\nsys.path.insert(0, str(STAGE))')
replace("parser.add_argument('--out-dir', required=True)","parser.add_argument('--out-dir', required=True)\nparser.add_argument('--region-top-approach', action='store_true', help='Quarantined rear-top near-support-set approach; default off, diagnostic only.')")
replace('args = parser.parse_args()', '''args = parser.parse_args()
if args.role != 'diagnostic' or args.waist_pilot_contract or args.spatial_pilot_contract or args.recovery_pilot_contract:
    parser.error('Isolated region collector is diagnostic only; never reuse a pilot contract')
if args.region_top_approach and not (args.bounded_coupled_ik and args.waist_coordinated_expert and args.expert_top_projected_support and args.expert_frontal_top_recontact and args.expert_frontal_top_guarded_descent and args.expert_frontal_top_continuous_drag and args.expert_top_contact_normal_hold and not args.expert_top_contact_center_calibration and not args.expert_frontal_top_visible_corner and not args.expert_frontal_top_approach_compensation and not args.expert_frontal_top_collision_core and not args.policy_port and not args.idle and not args.expert_top_object_relative_lead_m):
    parser.error('Region approach requires bounded projected guarded top expert and original normal hold, without other reference/geometry overrides')''')
replace('    top_contact_bout_yaw = None','    region_approach = None\n    region_model = None\n    region_log = []\n    top_contact_bout_yaw = None')
needle='                top_cls, top_extra = TopContactBypassState, {}'
replace(needle,needle+'''
                if args.region_top_approach and not front_route_selected and not initial_top_selected:
                    from region_top_contact import TopContactBypassState as RegionTopContactBypassState
                    from region_approach_lifecycle import RegionApproachLifecycle
                    from articulated_hand_geometry import ArticulatedHandGeometry
                    top_cls = RegionTopContactBypassState
                    region_approach = RegionApproachLifecycle()
                    region_model = ArticulatedHandGeometry(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
                    frontal_plan['region_approach'] = dict(enabled=True,near_support_band_m=.0001,planning_buffer_m=.0005,target_inset_m=.01,scope='Rear-top first unloaded approach only. No physical feasibility or training approval.')''')
replace('        active_control_offset = None','        active_control_offset = None\n        region_step = None')
replace('center_local=contact_center_calibration.center_local if contact_center_calibration is not None else None)', 'center_local=(region_approach.center_local if region_approach is not None else contact_center_calibration.center_local if contact_center_calibration is not None else None))')
needle='                if contact_center_calibration is not None and projected_support_context is not None:'
replace(needle,'''                if region_approach is not None and projected_support_context is not None:
                    q_region = robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy().astype(float)
                    target_now = np.asarray(parcel_xyz(env,target_actor),dtype=float)
                    other_now = np.asarray(parcel_xyz(env,obstacle_actor),dtype=float)
                    tq_now = np.asarray(target_quat,dtype=float);oq_now=np.asarray(obstacle_quat,dtype=float)
                    model_errors = {}
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    for check_side in ('left','right'):
                        mat,jl,jw = region_model.fk(check_side,q_region)
                        body=hands[check_side]
                        xyz=robot.data.body_pos_w.torch[0,body].detach().cpu().numpy()
                        rotation=np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,body].detach().cpu().numpy()))
                        position_error=float(np.max(abs(mat[:3,3]-xyz)));rotation_error=float(np.max(abs(mat[:3,:3]-rotation)))
                        if position_error>1e-4 or rotation_error>1e-4:
                            raise ValueError('Region articulated geometry differs from observed robot')
                        model_errors[check_side]=dict(position_max_error_m=position_error,rotation_max_error=rotation_error)
                    def geometry_region(query_q):
                        return region_model.scene_geometry(side,query_q,target_xyz=target_now,target_quat=tq_now,other_xyz=other_now,other_quat=oq_now,other_size=obstacle_size)
                    region_lower=np.asarray(U1_JOINT_LIMIT_LO)[12:23].copy();region_upper=np.asarray(U1_JOINT_LIMIT_HI)[12:23].copy()
                    region_upper[0]=args.waist_limit_rad-min(.02,.1*args.waist_limit_rad);region_lower[0]=-region_upper[0]
                    region_limits=np.full(11,.04);region_limits[0]=.015;region_damping=np.full(11,.045);region_damping[0]=.12
                    waypoint,reference,region_step=region_approach.update(waypoint,frontal_state,reference,q=q_region,geometry=geometry_region,lower=region_lower,upper=region_upper,step_limits=region_limits,damping=region_damping,inactive_anchor=inactive_anchor['right' if side=='left' else 'left'],normal_anchor=top_contact_normal_anchor,load_n=load_n)
                    projected_support_context={k:v.tolist() for k,v in reference.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')}
                    point_kwargs['control_offset_local']=tuple(reference['reference_local'])
                    if region_step is not None:region_step['runtime_fk_check']=model_errors
                    region_log.append(dict(step=step,active=region_approach.active,center_local=None if region_approach.center_local is None else region_approach.center_local.tolist(),selected_surface_local_xy=frontal_state.selected_surface_local_xy,abort_reason=region_approach.abort_reason,mode=waypoint['mode'],solver=region_step))
''' +needle)
needle='            if terminal_hold is not None:\n                from simfoundry.data.top_contact_bypass import support_mesh, rotation_xyzw'
replace(needle,'''            if region_step is not None and region_step.get('joint_override'):
                original_upper_target=(action[12:23]+default[12:23]).copy()
                action[12:23]=np.asarray(region_step['next_q'])-default[12:23]
                coordination_log[-1]['unexecuted_original_upper_target']=original_upper_target.tolist()
                coordination_log[-1]['region_joint_override']=region_step
                coordination_log[-1]['waist_target_rad']=float(region_step['next_q'][0])
            if terminal_hold is not None:
                from simfoundry.data.top_contact_bypass import support_mesh, rotation_xyzw''')
needle="    if args.trace_solved_contact_forces:\n        (folder / 'solved_contact_forces.json').write_text"
replace(needle,"    if region_approach is not None:\n        (folder/'region_approach.json').write_text(json.dumps(dict(rows=region_log,training_ready=False),indent=2))\n"+needle)
needle='    for path in paths:\n        snapshot = root'
replace(needle,"    paths.extend([STAGE/name for name in ['contact_patch_approach.py','articulated_hand_geometry.py','region_top_contact.py','region_approach_lifecycle.py']])\n    paths.extend([ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json'])\n"+needle)
dependencies=sorted(json.loads((w/'fresh_trial_contracts_v2_r1/fresh_lateral_00.json').read_text())['controller_source_sha256'])
needle2='    for path in paths:\n        snapshot = root'
replace(needle2,'    for relative in '+repr(dependencies)+':\n        if ROOT/relative not in paths:paths.append(ROOT/relative)\n'+needle2)
compile(s,str(stage/'collect_paired_sorting.py'),'exec');(stage/'collect_paired_sorting.py').write_text(s)
print(json.dumps(dict(staged_collector_sha256=hashlib.sha256(s.encode()).hexdigest(),production_collector_sha256=hashlib.sha256((repo/'scripts/collect_paired_sorting.py').read_bytes()).hexdigest(),installed=False,physics_executed=False),indent=2))
