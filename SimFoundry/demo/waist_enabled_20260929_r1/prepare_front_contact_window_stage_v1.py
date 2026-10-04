"""Isolate default-off contact window collector from quarter-Z parent.
No production source or running stage modified, no physical launch.
"""
from pathlib import Path
import ast,shutil,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'staged_front_loaded_z_quarter_v1';S=W/'staged_front_contact_window_v1';D=W/'front_contact_window_preparation_r1';C=W/'front_contact_window_candidate_v1';S.mkdir(exist_ok=False);D.mkdir(exist_ok=False);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};copies=[]
for p in P.iterdir():
 if p.is_file():shutil.copy2(p,S/p.name);copies.append(p.name);sources[str(p)]=sha(p)
helpers=['front_window_native_v3.py','contact_window_evidence_v2.py','window_initial_center_top_v2.py','window_initial_center_route_v2.py','window_initial_center_cop_v2.py']
for name in helpers:shutil.copy2(C/name,S/name);sources[str(C/name)]=sha(C/name)
p=S/'collect_paired_sorting.py';s=p.read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
anchor="parser.add_argument('--front-loaded-z-quarter',action='store_true',help='Diagnostic quarter interpolation of captured-front loaded Z target; original guards, default off.')"
replace(anchor,anchor+"\nparser.add_argument('--front-contact-window',action='store_true',help='Diagnostic front-only immediately preceding24tick contact evidence for loss counter; actual physical support10mm inside core; default off.')")
anchor='if args.front_loaded_z_quarter and not (';line=next(x for x in s.splitlines() if x.startswith(anchor))
replace(line,"if args.front_contact_window and not (args.front_loaded_z_quarter and args.front_initial_center_landing and args.peak_load_bias_guard and args.trace_substep_contacts and args.expert_frontal_top_support_hysteresis_m==0 and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Front contact window requires original quarter-Z diagnostic, initial-center front, complete substeps, peak guard and exact physical lowest support; no policy/training or hysteresis')\n"+line)
anchor='    front_loaded_z_priority_log = []';replace(anchor,anchor+'\n    if args.front_contact_window:\n        front_contact_window_log = []')
anchor='                        top_cls=CenterFrontState'
replace(anchor,anchor+"\n                        if args.front_contact_window:\n                            from front_window_native_v3 import WindowFrontCopRouteState\n                            top_cls=WindowFrontCopRouteState\n                            top_extra.update(contact_window_enabled=True,contact_window_selected_front=True)\n                            frontal_plan['front_contact_window']=dict(version='front_window_native_v3',enabled=True,selected_front=True,observable='original_absolute_vertical_hand_target_force',solver_ticks=24,loss_threshold_n=.2,minimum_contact_ticks=12,minimum_current_core_margin_m=.010,geometry='current_measured_hand_pose_actual_collision_support_vertex',current_force_and_cop_unchanged=True,original_guard_priority=True,training_ready=False)")
anchor='                waypoint = frontal_state.update(palm_xyz(robot,hands[side]),parcel_xyz(env,target_actor),parcel_xyz(env,obstacle_actor),'
replace(anchor,"                if args.front_contact_window and front_route_selected:\n                    frontal_state.observe_contact_window(action_step=step,after_action_step=step-1,vertical_load_n=peak_observation['vertical_load_n'],instantaneous_load_n=load_n)\n                    point_kwargs.update(observed_hand_xyz=hand_xyz,observed_hand_quat_xyzw=hand_quat)\n"+anchor)
anchor='                                                extent_x_from_quat(target_size,target_quat),extent_x_from_quat(obstacle_size,obstacle_quat),**point_kwargs)'
replace(anchor,anchor+"\n                if args.front_contact_window and front_route_selected:\n                    interval=waypoint['contact_window_interval']\n                    if interval['action_step']!=step or frontal_state._window_pending is not None or frontal_state._window_active is not None:raise ValueError('Contact window must consume current interval once before downstream control')\n                    front_contact_window_log.append(dict(step=step,**interval))")
anchor="    if args.front_loaded_z_quarter:\n        episode.collect_meta['front_loaded_z_quarter']=";line=next(x for x in s.splitlines() if x.startswith("        episode.collect_meta['front_loaded_z_quarter']="))
replace("    if args.front_loaded_z_quarter:\n"+line,"    if args.front_contact_window:\n        episode.collect_meta['front_contact_window']=dict(version='front_window_native_v3',enabled=True,selected_front=bool(front_route_selected),recorded_intervals=len(front_contact_window_log),training_ready=False)\n    if args.front_loaded_z_quarter:\n"+line)
anchor="    # SUBSTEP_OBSERVER_BEGIN\n    if args.trace_substep_contacts:\n        substep_recording.save(folder,len(qs))"
assert anchor in s
replace(anchor,"    if args.front_contact_window:\n        (folder/'front_contact_window.json').write_text(json.dumps(dict(version='front_window_native_v3',enabled=True,selected_front=bool(front_route_selected),rows=front_contact_window_log,executed_frames=len(qs),training_ready=False),indent=2))\n"+anchor)
anchor="    if args.front_loaded_z_quarter:\n        paths.append(STAGE/'front_loaded_z_fraction.py')"
replace(anchor,anchor+"\n    if args.front_contact_window:\n        paths.extend(STAGE/name for name in "+repr(helpers)+")")
ast.parse(s);p.write_text(s);back=s
for e in reversed(edits):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(P/'collect_paired_sorting.py').read_text()
for name in copies:
 if name!='collect_paired_sorting.py':assert sha(S/name)==sha(P/name)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),stage=str(S),parent_files=len(copies),helpers=helpers,collector_edits=edits,reverse_exact_parent=True,other_parent_files_unchanged=True,source_sha256=sources,candidate_sha256={str(p):sha(p) for p in S.iterdir() if p.is_file()},collector_wired=True,parser_runtime_checked=False,physical_launch_ready=False,physics_started=False,training_ready=False)
with (D/'STAGE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(stage=str(S),parent_files=len(copies),collector_edits=len(edits),reverse_exact_parent=True,physical_launch_ready=False)))
