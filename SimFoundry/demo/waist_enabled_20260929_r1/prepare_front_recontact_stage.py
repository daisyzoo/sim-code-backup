"""Isolated default-off front-bag recontact centering from original2mm parent.
Retain original initial/right/rear/wait behavior; no rear cursor experiment.
Prepare source only. Full wiring/independent execution audits precede physics.
"""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;A=W/'staged_front_drive_1mm';D=W/'front_bag_recontact_center_draft_r4';B=W/'staged_front_recontact_center';assert not B.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parent=json.loads((A/'COLLECTOR_PREPARATION.json').read_text());expected=parent['stage_sha256'];assert len(expected)==71
for n,h in expected.items():assert sha(A/n)==h,n
checks=['LIFECYCLE_CHECK.json','ADAPTER_CHECK.json','ACTUAL_PREFIX_LOAD_CHECK.json','RUNTIME_CHECK.json']
for name in checks:
 d=json.loads((D/name).read_text());assert d['passed']
 for p,h in d['source_sha256'].items():assert sha(p)==h,p
s=(A/'collect_paired_sorting.py').read_text();edits=[]
def edit(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
a="parser.add_argument('--front-initial-center-landing',action='store_true',help='Diagnostic first front physical-center unloaded landing; original guards and240 ticks; default off.')"
edit(a,a+"\nparser.add_argument('--front-recontact-center-landing',action='store_true',help='Default-off left front recovery physical-center landing; real counters, original guards and240-command budget.')")
a='if args.front_corridor_midpoint_replan and not '
edit(a,"if args.front_recontact_center_landing and not (args.front_initial_center_landing and args.front_loaded_z_priority and args.front_corridor_midpoint_replan and args.front_cop_drive_step_m==.002 and args.role=='diagnostic' and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):\n    parser.error('Front recovery centering requires original2mm midpoint diagnostic profile, zero-start expert and all original capture/guard prerequisites')\n"+a)
a='    front_initial_runtime = None\n';edit(a,a+'    front_recontact_runtime = None\n')
a="                        front_initial_runtime=FrontInitialCenterRuntime(clearance_guard,side,edge_size,obstacle_size,parameters['tasks'][task_id]['decay'])\n"
edit(a,a+"""                        if args.front_recontact_center_landing and side=='left':
                            from front_recontact_center_runtime import FrontRecontactCenterRuntime
                            front_recontact_runtime=FrontRecontactCenterRuntime(clearance_guard,side,edge_size,obstacle_size,parameters['tasks'][task_id]['decay'],enabled=True)
                            frontal_plan['front_recontact_center_landing']=dict(enabled=True,side='left',real_positive_recontact_counter=True,maximum_ticks=240,actual_ready_frames=3,center_xy_m=.002,precontact_height_m=[.006,.007],measured_height_m=[.004,.010],alignment_abs_min=.8,numerical_tolerance=2e-7,wait_for_original_unloaded_geometry=True,original_guard_priority=True,predicted_capture_discarded=True,training_ready=False)
""")
a='        front_initial_override = None\n';edit(a,a+'        front_recontact_override = None\n')
a='center_local=(front_initial_runtime.center_local if front_initial_runtime is not None and front_initial_runtime.center_local is not None else region_approach.center_local'
edit(a,'center_local=(front_recontact_runtime.center_local if front_recontact_runtime is not None and front_recontact_runtime.center_local is not None else front_initial_runtime.center_local if front_initial_runtime is not None and front_initial_runtime.center_local is not None else region_approach.center_local')
a="""                    if center_event['kind']=='handover':
                        top_contact_normal_anchor=list(center_event['captured_normal_local_up'])
                        inactive_anchor[inactive_side]=list(center_event['captured_inactive_anchor_world'])
"""
edit(a,a+"""                    if front_recontact_runtime is not None:
                        waypoint,reference,front_recovery_event=front_recontact_runtime.update(waypoint,frontal_state,reference,
                            selected=bool(frontal_plan.get('front_route_selected') and side=='left'),step=step,current=center_q,
                            previous_q=np.asarray(qs[-1][12:23],dtype=float) if qs else None,previous_command=previous[12:23]+default[12:23],
                            target_xyz=parcel_xyz(env,target_actor),target_quat=target_quat,other_xyz=parcel_xyz(env,obstacle_actor),other_quat=obstacle_quat,
                            observed_load_n=load_n,observed_hand_pose=center_poses[side],observed_inactive_hand_pose=center_poses[inactive_side],
                            normal_anchor=top_contact_normal_anchor,inactive_anchor=inactive_anchor[inactive_side])
                        if front_recovery_event['kind']=='stop':
                            clearance_failure=dict(step=step,phase='front_recontact_center',reason=front_recovery_event['reason'],record=front_recovery_event)
                            break
                        if front_recovery_event['kind'] in ('command','handover'):
                            if front_initial_override is not None:raise ValueError('Competing initial and recovery front overrides')
                            front_recontact_override=front_recovery_event
                        if front_recovery_event['kind']=='handover':
                            top_contact_normal_anchor=list(front_recovery_event['captured_normal_local_up'])
                            inactive_anchor[inactive_side]=list(front_recovery_event['captured_inactive_anchor_world'])
""")
a="                    waypoint['front_initial_captured_center_local']=front_initial_runtime.center_local.tolist()\n"
edit(a,a+"""                if front_recontact_runtime is not None and front_recontact_runtime.center_local is not None:
                    waypoint['support_reference_scope']='Actual measured recovery lowest hull vertex captured as tangent reference; support plane recomputed. Current physical COP is not guaranteed.'
                    waypoint['front_recontact_captured_center_local']=front_recontact_runtime.center_local.tolist()
""")
a="                if front_initial_override is not None:\n                    clearance_kwargs['front_initial_override']=front_initial_override\n"
edit(a,a+"                if front_recontact_override is not None:\n                    clearance_kwargs['front_recontact_override']=front_recontact_override\n")
a='priority_selected=bool(front_initial_runtime is not None and front_initial_runtime.center_local is not None)'
edit(a,'priority_selected=bool((front_recontact_runtime is not None and front_recontact_runtime.center_local is not None) or (front_initial_runtime is not None and front_initial_runtime.center_local is not None))')
a="    if args.front_initial_center_landing:\n        episode.collect_meta['front_initial_center_landing']=True"
edit(a,"""    if args.front_recontact_center_landing:
        episode.collect_meta['front_recontact_center_landing']=True
        episode.collect_meta['front_recontact_center_failure']=None if front_recontact_runtime is None else front_recontact_runtime.failure
        episode.collect_meta['front_recontact_center_handovers']=0 if front_recontact_runtime is None else sum(r['kind']=='handover' for r in front_recontact_runtime.rows)
"""+a)
a="    if args.front_initial_center_landing:\n        (folder/'front_initial_center.json')"
edit(a,"""    if args.front_recontact_center_landing:
        (folder/'front_recontact_center.json').write_text(json.dumps(dict(selected=front_recontact_runtime is not None,rows=[] if front_recontact_runtime is None else front_recontact_runtime.rows,training_ready=False),indent=2))
"""+a)
helpers=['front_recontact_center_tracking.py','front_recontact_center_lifecycle_static.py','front_recontact_center_selection.py','front_recontact_center_lifecycle.py','front_recontact_center_adapter.py','front_recontact_center_runtime.py']
a="    if args.front_loaded_z_priority:\n        paths.extend(STAGE/name for name in ['front_loaded_z_priority.py','loaded_z_priority_solver.py','loaded_z_priority_checks.py','loaded_z_priority_stationarity.py'])"
edit(a,a+"\n    if args.front_recontact_center_landing:\n        paths.extend(STAGE/name for name in "+repr(helpers)+")")
restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(A/'collect_paired_sorting.py').read_text();ast.parse(s)
c=(A/'waist_coordination_clearance.py').read_text();original=c;signature='front_initial_override=None, precise_task_ik=False';replacement='front_initial_override=None, front_recontact_override=None, precise_task_ik=False';assert c.count(signature)==1;c=c.replace(signature,replacement)
start=c.index('    if front_initial_override is not None:\n');end=c.index('    if recontact_override is not None:\n',start);branch=c[start:end];added=branch.replace('front_initial_override','front_recontact_override').replace("context['recontacts']!=0", "(type(context['recontacts']) is not int or context['recontacts']<1 or state.side!='left' or front_recontact_override.get('real_recontact_index')!=context['recontacts'])").replace('front_initial_center_override=','front_recontact_center_override=').replace('verified_unloaded_front_initial_joint_path','verified_unloaded_front_recontact_joint_path').replace('Initial front','Front recovery').replace('initial front','front recovery')
conflict="    if sum(x is not None for x in (front_recontact_override,front_initial_override,recontact_override))>1:\n        raise ValueError('Competing independently declared joint-path overrides')\n"
c=c[:start]+conflict+added+c[start:];ast.parse(c);back=c.replace(conflict+added,'',1).replace(replacement,signature,1);assert back==original
B.mkdir()
for n in expected:(B/n).write_bytes((A/n).read_bytes())
(B/'collect_paired_sorting.py').write_text(s);(B/'waist_coordination_clearance.py').write_text(c)
for n in helpers:(B/n).write_bytes((D/n).read_bytes())
files={p.name:sha(p) for p in B.iterdir() if p.is_file()};assert len(files)==77
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(A),parent_manifest_sha256=sha(A/'COLLECTOR_PREPARATION.json'),source_sha256={str(p):sha(p) for p in [Path(__file__),A/'COLLECTOR_PREPARATION.json',*[D/n for n in checks],*[D/n for n in helpers]]},stage_sha256=files,collector_edits=edits,coordination_edits=dict(signature_old=signature,signature_new=replacement,added_branch=conflict+added),unchanged_parent_files=69,changed_parent_files=['collect_paired_sorting.py','waist_coordination_clearance.py'],runtime_helpers=helpers,collector_integrated=True,simulation_started=False,training_ready=False,remaining='Actual parser/dispatch/reference lifetime tests, independent audit family and complete paired physics required.')
with (B/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(stage=str(B),sources=len(files),collector_edits=len(edits),parent_files_unchanged=69)))
