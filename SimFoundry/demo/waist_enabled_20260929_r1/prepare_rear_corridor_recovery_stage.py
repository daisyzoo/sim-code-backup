"""Create an isolated, default-off rear recovery collector. Never launch physics.
All previous frozen source and diagnostic outcomes remain unchanged.
"""
from pathlib import Path
import hashlib,json,datetime,ast
W=Path(__file__).resolve().parent; P=W/'staged_peak_load_guard'; D=W/'staged_rear_corridor_recovery'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
HELPERS=['rear_corridor_joint_recovery_reserve_candidate.py','rear_corridor_unload_candidate.py',
         'rear_corridor_recovery_state.py','rear_corridor_collector_adapter.py',
         'rear_recontact_transport_witness.py','rear_transport_recontact_plan.py',
         'rear_transport_recontact_lifecycle.py','rear_transport_entry_lift_lifecycle.py']

def construct():
 s=(P/'collect_paired_sorting.py').read_text(); edits=[]
 def replace(old,new):
  nonlocal s
  assert s.count(old)==1,(old,s.count(old)); s=s.replace(old,new); edits.append(dict(old=old,new=new))
 anchor='parser = argparse.ArgumentParser()\n'
 replace(anchor,anchor+"parser.add_argument('--rear-corridor-recovery',action='store_true',help='Diagnostic measured rear corridor recovery with verified unload and directional recontact; default off.')\n")
 anchor='args = parser.parse_args()\n'
 replace(anchor,anchor+"""if args.rear_corridor_recovery and not (args.role=='diagnostic' and args.peak_load_bias_guard and args.rear_joint_xy_progress and args.rear_cop_centering and args.rear_joint_edge_command and args.rear_box_inward_correction and args.self_clearance_task_ik and args.minimum_motion_recontact and args.unloaded_recontact_pose and args.trace_substep_contacts and args.motion_protocol=='waist_yaw_enabled_v1' and args.waist_limit_rad==1.0 and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract and not args.spatial_pilot_contract):
    parser.error('Rear corridor recovery requires complete original diagnostic peak/rear/edge/clearance/recontact configuration; no policy/pilot/idle/probe.')
""")
 anchor="        recontact_lifecycle=RecontactLifecycle(enabled=True,prefer_interior=args.recontact_interior_preference,**recontact_extra)\n"
 replace(anchor,"""        if args.rear_corridor_recovery:
            from rear_transport_recontact_lifecycle import RecontactLifecycle
            if args.rear_box_entry_lift and side=='right':
                from rear_transport_entry_lift_lifecycle import RecontactLifecycle
"""+anchor)
 anchor='    coordination_log = []\n'
 replace(anchor,anchor+"    if args.rear_corridor_recovery:\n        rear_corridor_log=[]\n        rear_corridor_handovers=[]\n")
 anchor='                            recontact_event=recontact_lifecycle.update('
 replace(anchor,"""                            rear_transport_kwargs={}
                            if args.rear_corridor_recovery:
                                rear_transport_kwargs['require_rear_transport']=bool(getattr(frontal_state,'rear_corridor_recontact_pending',False))
                            recontact_event=recontact_lifecycle.update(**rear_transport_kwargs,""")
 anchor="                            if recontact_event['kind']=='handover':\n                                top_contact_normal_anchor=list(recontact_event['captured_normal_local_up'])\n"
 replace(anchor,"""                            if recontact_event['kind']=='handover':
                                if args.rear_corridor_recovery:
                                    from rear_corridor_collector_adapter import complete_handover
                                    rear_handover=complete_handover(frontal_state,recontact_event)
                                    if rear_handover is not None:rear_corridor_handovers.append(rear_handover)
                                top_contact_normal_anchor=list(recontact_event['captured_normal_local_up'])
""")
 anchor="        if clearance_guard is not None:\n            final_clearance = clearance_guard.command("
 replace(anchor,"""        rear_recovery_record=None
        if args.rear_corridor_recovery and step>0 and frontal_plan is not None and frontal_plan.get('rear_joint_xy_progress',{}).get('enabled'):
            from rear_corridor_collector_adapter import propose as propose_rear_recovery
            from simfoundry.data.top_contact_bypass import rotation_xyzw
            if np.any(default[12:23]!=0):raise ValueError('Rear recovery requires original zero upper default')
            rear_current=robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy()
            rear_command,rear_recovery_record=propose_rear_recovery(enabled=True,step=step,selected=True,guard=clearance_guard,row=frontal_log[-1],coordinate=coordination_log[-1],current=rear_current,previous=previous[12:23],parent_command=action[12:23],target_xyz=parcel_xyz(env,target_actor),obstacle_xyz=parcel_xyz(env,obstacle_actor),target_rotation=rotation_xyzw(target_quat),obstacle_rotation=rotation_xyzw(obstacle_quat),target_size=target_size,obstacle_size=obstacle_size,core_size=frontal_plan['region_causal_response']['actual_core']['collision_core_size_xyz'])
            rear_corridor_log.append(rear_recovery_record)
            if rear_command is None:
                clearance_failure=dict(step=step,phase='rear_corridor_recovery',reason=rear_recovery_record['reason'],record=rear_recovery_record)
                break
            action[12:23]=rear_command
        if clearance_guard is not None:
            final_clearance = clearance_guard.command(""")
 anchor='        previous = action.copy()\n'
 replace(anchor,"""        if rear_recovery_record is not None and rear_recovery_record['kind'] in ('loaded_recovery','unload'):
            from rear_corridor_collector_adapter import commit as commit_rear_recovery
            frontal_log[-1]=commit_rear_recovery(state=frontal_state,guard=clearance_guard,row=frontal_log[-1],coordinate=coordination_log[-1],current=rear_current,previous=previous[12:23],command=action[12:23],record=rear_recovery_record)
            expert.mode,expert.mode_step=frontal_state.mode,frontal_state.mode_step
            expert.last_target_xyz=tuple(frontal_log[-1]['target_xyz'])
            if args.peak_load_bias_guard:
                if peak_load_frame_log[-1]['step']!=step:raise ValueError('Missing current pressure state')
                rear_recovery_record['parent_pressure_final_state']=dict(peak_load_frame_log[-1])
                peak_load_frame_log[-1].update(mode=frontal_state.mode,top_mode=frontal_state.top_mode,bias_m=frontal_state.load.bias_m,filtered_n=frontal_state.load.filtered_n)
            coordination_log[-1]['rear_corridor_override']=dict(kind=rear_recovery_record['kind'],step=step,record_file='rear_corridor_recovery.json')
"""+anchor)
 anchor="    if args.peak_load_bias_guard:\n        episode.collect_meta['peak_load_bias_guard']=True\n"
 replace(anchor,anchor+"    if args.rear_corridor_recovery:\n        episode.collect_meta['rear_corridor_recovery']=True\n")
 anchor="    (folder / 'quality.json').write_text(json.dumps(report, indent=2))\n"
 replace(anchor,"""    if args.rear_corridor_recovery:
        (folder/'rear_corridor_recovery.json').write_text(json.dumps(dict(rows=rear_corridor_log,handovers=rear_corridor_handovers,executed_action_count=len(qs),pending_recontact=bool(getattr(frontal_state,'rear_corridor_recontact_pending',False)),training_ready=False,scope='Parent evidence and actual verified command commits; nominal motion is not measured parcel motion.'),indent=2))
"""+anchor)
 anchor='    for path in paths:\n'
 replace(anchor,"    if args.rear_corridor_recovery:\n        paths.extend([STAGE/name for name in "+repr(HELPERS)+"])\n"+anchor)
 ast.parse(s);restored=s
 for e in reversed(edits):
  assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(P/'collect_paired_sorting.py').read_text()
 return s,edits

def main():
 assert not D.exists()
 protocol=json.loads((W/'fresh_closed_peak_trials_r1/PROTOCOL.json').read_text());parent={}
 for p in P.iterdir():
  if p.is_file() and (p.suffix=='.py' or p.name in ['causal_response_parameters.json','elbow_torso_hulls.json']):
   assert sha(p)==protocol['frozen_files_sha256'][str(p.resolve())];parent[p.name]=sha(p)
 reports=['REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json','REAR_CORRIDOR_UNLOAD_CHECK.json','REAR_CORRIDOR_STATE_COMMIT_V2_CHECK.json','REAR_RECONTACT_TRANSPORT_WITNESS_V2_CHECK.json','REAR_TRANSPORT_LIFECYCLE_CHECK.json']
 for name in reports:
  report=json.loads((W/name).read_text());assert report.get('passed') or report.get('status')=='complete',name
  for field in ['source_sha256','frozen_sha256']:
   for path,digest in report.get(field,{}).items():
    p=Path(path);p=p if p.is_absolute() else W/p;assert sha(p)==digest,str(p)
 source,edits=construct();D.mkdir()
 for name in parent:(D/name).write_bytes((P/name).read_bytes())
 for name in HELPERS:(D/name).write_bytes((W/name).read_bytes())
 (D/'collect_paired_sorting.py').write_text(source)
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(P),stage=str(D),parent_source_sha256=parent,helpers=HELPERS,edits=edits,reverse_reconstruction_matches=True,stage_sha256={p.name:sha(p) for p in D.iterdir() if p.is_file()},prerequisite_reports_sha256={n:sha(W/n) for n in reports},default_off=True,simulation_started=False,training_ready=False,remaining='Actual CLI/disabled equivalence, adapter independent all-stream verification and complete original audit adapters before physical paired comparison')
 (D/'PREPARATION.json').write_text(json.dumps(result,indent=2));print('PREPARED_NOT_LAUNCHED',D)
if __name__=='__main__':main()
