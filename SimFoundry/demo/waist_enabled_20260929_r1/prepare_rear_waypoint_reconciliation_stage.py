"""Prepare isolated default-off post-commit cursor stage; never launch physics."""
from pathlib import Path
import json,hashlib,datetime,ast
W=Path(__file__).resolve().parent;P=W/'staged_front_drive_1mm';D=W/'rear_waypoint_reconciliation_draft_r1';S=W/'staged_rear_waypoint_reconciliation';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[D/'POST_COMMIT_ADAPTER_CHECK.json',D/'INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json',D/'SINGLE_STEP_COMMAND_CHECK.json']
for p in checks:
 d=json.loads(p.read_text());assert d.get('passed',d.get('nominal_checks_passed')==20)
 for path,h in d['source_sha256'].items():assert sha(path)==h,path
prep=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());parent=prep['stage_sha256'];assert len(parent)==71
assert not S.exists();S.mkdir()
for name,h in parent.items():assert sha(P/name)==h;(S/name).write_bytes((P/name).read_bytes())
for a,b in [('reconcile_rear_waypoint.py','reconcile_rear_waypoint.py'),('post_commit_adapter.py','rear_post_commit_adapter.py')]:
 (S/b).write_bytes((D/a).read_bytes())
s=(P/'collect_paired_sorting.py').read_text();changes=[]
def insert(anchor,extra,after=False):
 global s
 assert s.count(anchor)==1,(anchor,s.count(anchor));replacement=anchor+extra if after else extra+anchor;s=s.replace(anchor,replacement);changes.append(dict(old=anchor,new=replacement))
insert("parser.add_argument('--rear-box-inward-correction'", "parser.add_argument('--rear-waypoint-reconciliation',action='store_true',help='Default-off post-commit rear-box future Y cursor reconciliation; original guards retained.')\n")
insert("if args.rear_box_inward_correction and not (args.rear_box_entry_lift and args.rear_joint_edge_parent_seed_retry and args.role=='diagnostic'):","""if args.rear_waypoint_reconciliation and not (args.role=='diagnostic' and args.motion_protocol=='waist_yaw_enabled_v1' and args.waist_limit_rad==1.0 and args.waist_coordinated_expert and args.bounded_coupled_ik and args.rear_box_inward_correction and args.rear_cop_centering and args.edge_clearance_intersection and args.self_clearance_task_ik and args.trace_solved_contact_forces and args.trace_hand_contact_forces and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):
    raise SystemExit('Rear waypoint reconciliation requires diagnostic original rear-box/edge/self-clearance/contact stack.')
""")
insert('    front_loaded_z_priority_log = []\n','    rear_waypoint_reconciliation_log = []\n',after=True)
insert('                frontal_state.load.desired_n=args.expert_frontal_top_load_n\n',"""                if args.rear_waypoint_reconciliation:
                    frontal_plan['rear_waypoint_reconciliation']=dict(requested=True,enabled=bool(side=='right' and frontal_plan.get('rear_cop_centering',{}).get('enabled')),post_successful_action_only=True,post_guard_required=True,changes='next_state_command_y_and_last_waypoint_y_only',current_action_unchanged=True,default_off=True,training_ready=False)
""",after=True)
insert('        if bool(terminated[0] or truncated[0]):\n            break\n',"""        if args.rear_waypoint_reconciliation:
            from rear_post_commit_adapter import apply_post_commit
            if clearance_guard is None or np.any(default[12:23]!=0):raise ValueError('Rear cursor commit requires original clearance guard and zero upper default')
            cursor_selected=bool(frontal_plan is not None and frontal_plan.get('rear_cop_centering',{}).get('enabled'))
            cursor_row=frontal_log[-1] if frontal_log and frontal_log[-1]['step']==step else None
            cursor_coordinate=coordination_log[-1] if coordination_log and coordination_log[-1]['step']==step else None
            cursor_contact=point_kwargs.get('slip_contact') if step>0 and cursor_selected else None
            cursor_record=apply_post_commit(enabled=True,step=step,side=side,rear_selected=cursor_selected,state=frontal_state,row=cursor_row,coordinate=cursor_coordinate,action=np.asarray(acts[-1])[12:23],final_guard=dict(step=step,phase='final_command',**final_clearance),post_guard=dict(step=step,phase='post',**observed_clearance),execution_completed=True,slip_contact=cursor_contact,guard=clearance_guard)
            rear_waypoint_reconciliation_log.append(cursor_record)
""")
insert("    if args.rear_box_inward_correction:\n        episode.collect_meta['rear_box_inward_correction']=True\n","""    if args.rear_waypoint_reconciliation:
        episode.collect_meta['rear_waypoint_reconciliation']=True
        episode.collect_meta['rear_waypoint_reconciliation_applied_frames']=sum(r['applied'] for r in rear_waypoint_reconciliation_log)
""",after=True)
insert("    if args.front_initial_center_landing:\n        (folder/'front_initial_center.json')", """    if args.rear_waypoint_reconciliation:
        (folder/'rear_waypoint_reconciliation.json').write_text(json.dumps(dict(rows=rear_waypoint_reconciliation_log,training_ready=False,scope='Post-successful-action future Y cursor only. Original actions and all native guards remain; independent event/state replay required.'),indent=2))
""")
insert("    if args.rear_box_inward_correction:\n        paths.extend([STAGE/'joint_edge_inward_command.py',STAGE/'joint_edge_inward_adapter.py'])\n","""    if args.rear_waypoint_reconciliation:
        paths.extend([STAGE/'reconcile_rear_waypoint.py',STAGE/'rear_post_commit_adapter.py'])
""",after=True)
ast.parse(s);restored=s
for row in reversed(changes):assert restored.count(row['new'])==1;restored=restored.replace(row['new'],row['old'])
assert restored==(P/'collect_paired_sorting.py').read_text();(S/'collect_paired_sorting.py').write_text(s)
files={p.name:sha(p) for p in S.iterdir() if p.is_file()};assert len(files)==73 and sum(files[n]==h for n,h in parent.items())==70
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(P),parent_stage_sha256=parent,stage_sha256=files,added_helper_sources={str(D/a):sha(D/a) for a in ['reconcile_rear_waypoint.py','post_commit_adapter.py']},changes=changes,original_collector_restored_byte_identical=True,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',*checks]},collector_connected=True,cli_and_hook_checks_pending=True,full_audit_family_pending=True,simulation_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(dict(runtime_files=len(files),parent_helpers_unchanged=70,collector_changes=len(changes),simulation_started=False))
