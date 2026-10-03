"""Isolated loaded material-reference cap integration; not a physics launch.
Exact parent controller remains unchanged. Admission runs after initial capture
and COP, before downstream joint IK, slew and physical clearance verification.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;A=W/'staged_front_initial_center';B=W/'staged_front_loaded_reference';assert not B.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((A/'PREPARATION.json').read_text())
for name,h in prep['stage_sha256'].items():assert sha(A/name)==h,name
checks=['FRONT_INITIAL_LOADED_REFERENCE_CAP_CHECK.json','FRONT_LOADED_REFERENCE_HISTORY_CHECK.json']
for name in checks:
 d=json.loads((W/name).read_text());assert d.get('passed') is True
 # The pure helper test and state-history test record their exact source inputs.
 for p,h in d.get('source_sha256',{}).items():assert sha(p)==h,p
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(old,new):
 global s
 assert s.count(old)==1,old;s=s.replace(old,new);edits.append(dict(old=old,new=new))
a="parser.add_argument('--front-initial-center-landing',action='store_true',help='Diagnostic first front physical-center unloaded landing; original guards and240 ticks; default off.')"
edit(a,a+"\nparser.add_argument('--front-loaded-reference-cap',action='store_true',help='Diagnostic post-capture10mm world-axis material cap; original3mm slew/30mm hand lead; empty intersection stops; default off.')")
a='if args.front_initial_center_landing and not ('
edit(a,"if args.front_loaded_reference_cap and not args.front_initial_center_landing:\n    raise ValueError('Loaded material cap requires measured initial-front center protocol')\n"+a)
a="                        frontal_plan['front_initial_center_landing']=dict(enabled=True,"
# Add a separate declaration before the unchanged initial landing declaration.
edit(a,"""                        if args.front_loaded_reference_cap:
                            frontal_plan['front_loaded_reference_cap']=dict(enabled=True,cap_world_xy_axis_m=.010,max_command_step_axis_m=.003,max_hand_reference_lead_axis_m=.030,min_normal_load_n=.3,scope='Only measured initial-front capture, loaded top_push, after parent safety/COP',empty_intersection='stop_before_current_action_and_record_failed_episode',parent_pressure_and_z_unchanged=True,no_physical_success_claim=True,training_ready=False)
"""+a)
a='                waypoint = frontal_state.update(palm_xyz(robot,hands[side]),parcel_xyz(env,target_actor),parcel_xyz(env,obstacle_actor),'
edit(a,"                cap_previous_xy = getattr(frontal_state,'last_emitted_xy',None) if args.front_loaded_reference_cap else None\n"+a)
a='                if region_approach is not None and projected_support_context is not None:\n'
edit(a,"""                if args.front_loaded_reference_cap and front_initial_runtime is not None:
                    from front_loaded_reference_adapter import admit as admit_loaded_reference
                    cap_contact=point_kwargs.get('slip_contact')
                    cap_normal=cap_contact['normal_load_n'] if cap_contact and cap_contact.get('valid') else 0.
                    waypoint,cap_stop=admit_loaded_reference(enabled=True,row=waypoint,state=frontal_state,runtime=front_initial_runtime,previous_xy=cap_previous_xy,normal_load_n=cap_normal,step=step)
                    if cap_stop is not None:
                        clearance_failure=cap_stop
                        break
"""+a)
a="    if args.front_initial_center_landing:\n        episode.collect_meta['front_initial_center_landing']=True"
edit(a,"    if args.front_loaded_reference_cap:\n        episode.collect_meta['front_loaded_reference_cap']=True\n"+a)
a='    for path in paths:\n        snapshot = root / \'source_snapshot\' / path.relative_to(ROOT)'
edit(a,"    if args.front_loaded_reference_cap:\n        paths.extend([STAGE/'front_loaded_reference_adapter.py',STAGE/'front_initial_loaded_reference_cap.py'])\n"+a)
restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(A/'collect_paired_sorting.py').read_text();ast.parse(s)
B.mkdir()
for name in prep['stage_sha256']:(B/name).write_bytes((A/name).read_bytes())
(B/'collect_paired_sorting.py').write_text(s)
helpers=['front_loaded_reference_adapter.py','front_initial_loaded_reference_cap.py']
for name in helpers:(B/name).write_bytes((W/name).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_stage=str(A),parent_preparation_sha256=sha(A/'PREPARATION.json'),parent_stage_sha256=prep['stage_sha256'],edits=edits,helper_source_sha256={str(W/n):sha(W/n) for n in helpers},checks_sha256={str(W/n):sha(W/n) for n in checks},generator_sha256=sha(__file__),stage_sha256={p.name:sha(p) for p in B.iterdir() if p.is_file()},collector_integrated=True,simulation_started=False,training_ready=False,remaining=['Actual collector parser and extracted admission/stop AST checks','Independent cap audit using native capture and material reference binding','Complete transitive original audit dependencies before future physical launch','Current candidate final original and supplementary comparison','Matched complete-group physical validation of cap including possible stalls; original gates unchanged'])
(B/'PREPARATION.json').write_text(json.dumps(report,indent=2));print('Prepared',len(report['stage_sha256']),'files; physical launch not performed')
