"""Isolated first-front real-center landing integration; no launch permission implied.
Frozen margin parent is copied, all edits are invertible and separately bound.
"""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;A=W/'staged_terminal_release_margin';B=W/'staged_front_initial_center';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parent=json.loads((A/'PREPARATION.json').read_text())
for n,h in parent['stage_sha256'].items():assert sha(A/n)==h,n
for name in ['FRONT_INITIAL_CENTER_STATE_CHECK.json','FRONT_INITIAL_CENTER_SELECTION_CHECK.json']:
 d=json.loads((W/name).read_text());assert d.get('passed') is True or d.get('status')=='complete'
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);edits.append(dict(old=a,new=b))
a="parser.add_argument('--terminal-release-margin',action='store_true',help='Diagnostic confirmed release also requires existing5mm zone/10mm progress margins; default off.')"
edit(a,a+"\nparser.add_argument('--front-initial-center-landing',action='store_true',help='Diagnostic first front physical-center unloaded landing; original guards and240 ticks; default off.')")
a='if args.terminal_release_margin and not ('
edit(a,"if args.front_initial_center_landing and not (args.terminal_release_margin and args.front_micro_repair_retention and args.front_cop_edge_speed and args.peak_load_bias_guard and args.trace_substep_contacts and args.self_clearance_task_ik and args.expert_top_projected_support and args.expert_top_contact_normal_hold and args.waist_coordinated_expert and args.bounded_coupled_ik and args.waist_limit_rad==1.0 and args.expert_frontal_top_load_n==5. and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract and not args.expert_frontal_top_visible_corner and not args.expert_frontal_top_forward_margin_m and not args.expert_top_contact_center_calibration and not args.expert_top_object_relative_lead_m and not args.expert_top_contact_bout_yaw_hold):\n    raise ValueError('Initial front center requires original diagnostic micro/edge/peak margin protocol without competing contact reference')\n"+a)
a='    region_model = None\n';edit(a,a+'    front_initial_runtime = None\n')
a='                    frontal_plan[\'front_route_live_guards\'] = dict('
edit(a,"""                    if args.front_initial_center_landing:
                        from front_initial_center_cop_route import FrontCopRouteState as CenterFrontState
                        from front_initial_center_runtime import FrontInitialCenterRuntime
                        parameters=json.loads((STAGE/'causal_response_parameters.json').read_text())
                        if parameters['schema_version']!=1:raise ValueError('Invalid initial-front response schema')
                        if clearance_guard is None:raise ValueError('Initial front landing requires final clearance guard')
                        top_cls=CenterFrontState
                        front_initial_runtime=FrontInitialCenterRuntime(clearance_guard,side,edge_size,obstacle_size,parameters['tasks'][task_id]['decay'])
                        frontal_plan['front_initial_center_landing']=dict(enabled=True,actual_core=edge_core,maximum_ticks=240,actual_ready_frames=3,center_xy_m=.002,precontact_height_m=[.006,.007],measured_height_m=[.004,.010],alignment_abs_min=.8,numerical_tolerance=2e-7,parameter_sha256=hashlib.sha256((STAGE/'causal_response_parameters.json').read_bytes()).hexdigest(),causal_preflight_only=True,no_plan_behavior='original_parent_before_any_override',source_scope='First front unloaded only; actual handover captures physical hull reference, surface and anchors; no training admission.')
"""+a)
a='        region_step = None\n';edit(a,a+'        front_initial_override = None\n')
a="center_local=(region_approach.center_local if region_approach is not None else contact_center_calibration.center_local if contact_center_calibration is not None else None)"
edit(a,"center_local=(front_initial_runtime.center_local if front_initial_runtime is not None and front_initial_runtime.center_local is not None else region_approach.center_local if region_approach is not None else contact_center_calibration.center_local if contact_center_calibration is not None else None)")
a='                if region_approach is not None and projected_support_context is not None:\n'
edit(a,"""                if front_initial_runtime is not None:
                    if projected_support_context is None or region_approach is not None:raise ValueError('Initial front reference missing or competing rear controller')
                    from simfoundry.data.top_contact_bypass import rotation_xyzw
                    center_q=robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy().astype(float)
                    center_poses={}
                    for center_side in ('left','right'):
                        center_pose=np.eye(4);center_body=hands[center_side]
                        center_pose[:3,3]=robot.data.body_pos_w.torch[0,center_body].detach().cpu().numpy()
                        center_pose[:3,:3]=np.asarray(rotation_xyzw(robot.data.body_quat_w.torch[0,center_body].detach().cpu().numpy()))
                        center_poses[center_side]=center_pose
                    inactive_side='right' if side=='left' else 'left'
                    waypoint,reference,center_event=front_initial_runtime.update(waypoint,frontal_state,reference,
                        step=step,current=center_q,previous_q=np.asarray(qs[-1][12:23],dtype=float) if qs else None,
                        previous_command=previous[12:23]+default[12:23],target_xyz=parcel_xyz(env,target_actor),target_quat=target_quat,
                        other_xyz=parcel_xyz(env,obstacle_actor),other_quat=obstacle_quat,observed_load_n=load_n,
                        observed_hand_pose=center_poses[side],observed_inactive_hand_pose=center_poses[inactive_side],
                        normal_anchor=top_contact_normal_anchor,inactive_anchor=inactive_anchor[inactive_side])
                    if center_event['kind']=='stop':
                        clearance_failure=dict(step=step,phase='front_initial_center',reason=center_event['reason'],record=center_event)
                        break
                    if center_event['kind'] in ('command','handover'):
                        front_initial_override=center_event
                    if center_event['kind']=='handover':
                        top_contact_normal_anchor=list(center_event['captured_normal_local_up'])
                        inactive_anchor[inactive_side]=list(center_event['captured_inactive_anchor_world'])
                    projected_support_context={k:v.tolist() for k,v in reference.items() if k in ('reference_local','center_local','lowest_vertex_local','world_normal')}
                    point_kwargs['control_offset_local']=tuple(reference['reference_local'])
"""+a)
a="                if support_selection is not None:\n"
edit(a,"""                if front_initial_runtime is not None and front_initial_runtime.center_local is not None:
                    waypoint['support_reference_scope']='Actual measured initial lowest hull vertex captured as tangent reference; subsequent support plane recomputed. Current physical COP is not guaranteed.'
                    waypoint['front_initial_captured_center_local']=front_initial_runtime.center_local.tolist()
"""+a)
a="                coordination_log.append(dict(step=step, **coordinated_step("
edit(a,"                if front_initial_override is not None:\n                    clearance_kwargs['front_initial_override']=front_initial_override\n"+a)
a="    if args.unloaded_recontact_pose:\n        episode.collect_meta['unloaded_recontact_pose']=True"
edit(a,"    if args.front_initial_center_landing:\n        episode.collect_meta['front_initial_center_landing']=True\n        episode.collect_meta['front_initial_center_failure']=None if front_initial_runtime is None else front_initial_runtime.lifecycle.failure\n"+a)
a="    if region_approach is not None:\n        (folder/'region_approach.json')"
edit(a,"    if args.front_initial_center_landing:\n        (folder/'front_initial_center.json').write_text(json.dumps(dict(selected=front_initial_runtime is not None,rows=[] if front_initial_runtime is None else front_initial_runtime.rows,training_ready=False),indent=2))\n"+a)
helpers=['front_initial_center_plan.py','front_initial_center_tracking.py','front_initial_center_selection.py','front_initial_center_lifecycle_v3.py','front_initial_center_lifecycle_v2.py','front_initial_center_top_contact.py','front_initial_center_route.py','front_initial_center_cop_route.py','front_initial_center_adapter.py','front_initial_center_runtime.py']
a="    if args.terminal_release_margin:\n        paths.append(STAGE/'margin_confirmed_position_release.py')"
edit(a,a+"\n    if args.front_initial_center_landing:\n        paths.extend([STAGE/name for name in "+repr(helpers)+"])\n        paths.extend([STAGE/name for name in ['minimum_motion_recontact.py','recontact_scene.py','causal_response_parameters.json']])")
back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'collect_paired_sorting.py').read_text();ast.parse(s)
# Separate front command type: retain original rear branch byte-for-byte.
c=(A/'waist_coordination_clearance.py').read_text();old='recontact_override=None, precise_task_ik=False';new='recontact_override=None, front_initial_override=None, precise_task_ik=False';assert c.count(old)==1;c=c.replace(old,new)
start=c.index('    if recontact_override is not None:\n');end=c.index('    position_jac = torch.cat(rows)',start);branch=c[start:end]
front=branch.replace('recontact_override','front_initial_override').replace("context['recontacts']<1","context['recontacts']!=0").replace('recontact_pose_override=','front_initial_center_override=').replace('verified_unloaded_recontact_joint_path','verified_unloaded_front_initial_joint_path').replace('Recovery','Initial front').replace('recovery','initial front')
front="    if front_initial_override is not None and recontact_override is not None:\n        raise ValueError('Competing initial front and rear recovery overrides')\n"+front
c=c[:start]+front+c[start:];ast.parse(c)
B.mkdir()
for n in parent['stage_sha256']:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s);(B/'waist_coordination_clearance.py').write_text(c)
for n in helpers:(B/n).write_bytes((W/n).read_bytes())
# Copy location differs by one directory; support mesh asset root must remain ROOT.
p=B/'front_initial_center_top_contact.py';original=p.read_text();assert original.count('Path(__file__).resolve().parents[2]')==1;p.write_text(original.replace('Path(__file__).resolve().parents[2]','Path(__file__).resolve().parents[3]'))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(A),parent_preparation_sha256=sha(A/'PREPARATION.json'),edits=edits,coordination_edits=dict(signature_old=old,signature_new=new,added_branch=front),helper_source_sha256={str(W/n):sha(W/n) for n in helpers},asset_root_adjustment=dict(file='front_initial_center_top_contact.py',old='parents[2]',new='parents[3]'),stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},collector_integrated=True,simulation_started=False,training_ready=False,remaining='Actual parser/runtime/coordination tests, independent new measurement/source audits, unchanged original audit adapters; complete original paired-group physics required.')
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('prepared',len(report['stage_sha256']),'stage files')
