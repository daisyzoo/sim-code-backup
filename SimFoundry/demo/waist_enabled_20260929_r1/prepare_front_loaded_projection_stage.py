"""Prepare isolated, default-off material projection and stop-observation archive.
No live source edits, physics launch, data admission or success claim.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;A=W/'staged_front_loaded_reference';B=W/'staged_front_loaded_projection';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parent=json.loads((A/'PREPARATION.json').read_text());check=json.loads((W/'FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json').read_text());assert check['passed']
for name,h in parent['stage_sha256'].items():assert sha(A/name)==h
for name,h in check['source_sha256'].items():assert sha(name)==h
texts={name:(A/name).read_text() for name in parent['stage_sha256']};edits=[]
def edit(file,old,new):
 assert texts[file].count(old)==1,(file,old);texts[file]=texts[file].replace(old,new);edits.append(dict(file=file,old=old,new=new))
f='collect_paired_sorting.py';old="parser.add_argument('--front-loaded-reference-cap',action='store_true',help='Diagnostic post-capture10mm world-axis material cap; original3mm slew/30mm hand lead; empty intersection stops; default off.')";edit(f,old,old+"\nparser.add_argument('--front-loaded-material-projection',action='store_true',help='Use bounded nearest-parent material projection; requires reference-cap; default off.')")
old='if args.front_loaded_reference_cap and not args.front_initial_center_landing:';edit(f,old,"if args.front_loaded_material_projection and not args.front_loaded_reference_cap:\n    raise ValueError('Material projection requires loaded reference cap protocol')\n"+old)
old="                        frontal_plan['front_initial_center_landing']=dict(enabled=True,";edit(f,old,"                        if args.front_loaded_material_projection:\n                            frontal_plan['front_loaded_reference_cap']['projection_strategy']='nearest_parent_in_slew_hand_material_intersection'\n                            frontal_plan['front_loaded_reference_cap']['stop_observation_archive']=True\n"+old)
old='waypoint,cap_stop=admit_loaded_reference(enabled=True,row=waypoint,state=frontal_state,runtime=front_initial_runtime,previous_xy=cap_previous_xy,normal_load_n=cap_normal,step=step)';edit(f,old,old[:-1]+',material_projection=args.front_loaded_material_projection)')
old='''                    if cap_stop is not None:
                        clearance_failure=cap_stop
                        break''';new='''                    if cap_stop is not None:
                        clearance_failure=cap_stop
                        if args.front_loaded_material_projection:
                            clearance_failure=dict(cap_stop,stop_observation=dict(
                                timing='current_pre_action_no_action_issued',step=step,
                                recorded_frames=len(qs),previous_solved_action_step=solved_contact_forces[-1]['after_action_step'],
                                upper_q_waist_left_right=center_q.tolist(),
                                previous_upper_command=(previous[12:23]+default[12:23]).tolist(),
                                target_actor=target_actor,other_actor=obstacle_actor,
                                target_xyz=list(parcel_xyz(env,target_actor)),target_quat_xyzw=list(target_quat),
                                other_xyz=list(parcel_xyz(env,obstacle_actor)),other_quat_xyzw=list(obstacle_quat),
                                hand_pose_world={name:pose.tolist() for name,pose in center_poses.items()},
                                projected_support_context=projected_support_context))
                        break''';edit(f,old,new)
old="    if args.front_loaded_reference_cap:\n        episode.collect_meta['front_loaded_reference_cap']=True";edit(f,old,"    if args.front_loaded_material_projection:\n        episode.collect_meta['front_loaded_material_projection']=True\n        episode.collect_meta['front_loaded_projection_strategy']='nearest_parent_in_slew_hand_material_intersection'\n"+old)
old="    if args.front_loaded_reference_cap:\n        paths.extend([STAGE/'front_loaded_reference_adapter.py',STAGE/'front_initial_loaded_reference_cap.py'])";edit(f,old,old+"\n    if args.front_loaded_material_projection:\n        paths.append(STAGE/'front_loaded_material_projection.py')")
f='front_loaded_reference_adapter.py';old='def admit(*, enabled, row, state, runtime, previous_xy, normal_load_n, step):';edit(f,old,'def admit(*, enabled, row, state, runtime, previous_xy, normal_load_n, step, material_projection=False):')
old='    if type(enabled) is not bool:';edit(f,old,"    if type(material_projection) is not bool:\n        raise ValueError('Explicit material projection flag required')\n"+old)
old='    advice = cap_loaded_reference(';edit(f,old,"    selected_cap = cap_loaded_reference\n    if material_projection:\n        from front_loaded_material_projection import cap_loaded_reference as selected_cap\n    advice = selected_cap(")
for file in ['collect_paired_sorting.py','front_loaded_reference_adapter.py']:
 recovered=texts[file]
 for change in reversed(edits):
  if change['file']==file:assert recovered.count(change['new'])==1;recovered=recovered.replace(change['new'],change['old'])
 assert recovered==(A/file).read_text();ast.parse(texts[file])
B.mkdir()
for name,text in texts.items():(B/name).write_text(text)
(B/'front_loaded_material_projection.py').write_bytes((W/'front_loaded_material_projection.py').read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(A),parent_preparation_sha256=sha(A/'PREPARATION.json'),parent_stage_sha256=parent['stage_sha256'],edits=edits,new_helper_source_sha256={str(W/'front_loaded_material_projection.py'):sha(W/'front_loaded_material_projection.py')},stage_sha256={p.name:sha(p) for p in B.iterdir()},math_check_sha256=sha(W/'FRONT_LOADED_MATERIAL_PROJECTION_CHECK.json'),generator_sha256=sha(__file__),collector_integrated=True,simulation_started=False,training_ready=False,remaining=['Actual parser and collector AST branch checks','Independent projection audit and short-stop pose/force binding','Complete69-file source/profile and original194-audit dependency preparation','Current full8push2wait closure and actual visual evidence','Matched physical test including stagnation; mathematical repair is not task success'])
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(stage=str(B),files=len(report['stage_sha256']),collector_edits=sum(e['file']=='collect_paired_sorting.py' for e in edits),adapter_edits=sum(e['file']=='front_loaded_reference_adapter.py' for e in edits),simulation_started=False),indent=2))
