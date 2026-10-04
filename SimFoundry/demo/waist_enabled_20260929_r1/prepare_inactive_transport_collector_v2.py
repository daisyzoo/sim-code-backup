"""Stage bilateral inactive-arm transport hook after parent refinements, before final guard.
Does not change any frozen parent or enable physics. All parent edits invert exactly.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;P=W/'staged_front_box_recenter_v3';D=W/'inactive_transport_clearance_bilateral_draft_r1';S=W/'staged_inactive_transport_v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not S.exists()
parent=json.loads((P/'COLLECTOR_PREPARATION.json').read_text());hashes=parent['stage_sha256'];assert len(hashes)==81
for name,h in hashes.items():assert sha(P/name)==h,name
probe=json.loads((D/'EARLY_CAPTURE_RUNTIME_PROBE.json').read_text());assert probe['passed']
for path,h in probe['source_sha256'].items():assert sha(path)==h,path
texts={name:(P/name).read_text() for name in hashes};name='collect_paired_sorting.py';edits=[]
def replace(old,new):
 assert texts[name].count(old)==1,old[:120]
 texts[name]=texts[name].replace(old,new);edits.append(dict(old=old,new=new))
spec=dict(version='inactive_transport_clearance_bilateral_v1',enabled=True,measured_inactive_floor_m=.840,nominal_predicted_floor_m=.8415,inactive_parcel_gap_m=.010,elbow_gap_m=.005,stationarity_max=1e-6,fixed='waist_and_active_five_bit_exact',original_joint_path_priority=True,static_path_not_dynamic_certificate=True,training_ready=False)
line=next(x for x in texts[name].splitlines() if x.startswith("parser.add_argument('--front-box-recenter'"))
replace(line,line+"\nparser.add_argument('--inactive-transport-clearance',action='store_true',help='Default-off bilateral inactive-five transport clearance; original final guard retained.')")
line='if args.front_box_recenter and not args.front_recontact_center_landing:'
replace(line,"if args.inactive_transport_clearance and not args.front_box_recenter:\n    parser.error('Inactive transport clearance requires complete front box recenter profile')\n"+line)
replace('    front_loaded_z_priority_log = []','    front_loaded_z_priority_log = []\n    inactive_transport_controller = None\n    inactive_transport_log = []')
hook='''        if args.inactive_transport_clearance:
            from inactive_transport_runtime import InactiveTransportRuntime
            if clearance_guard is None or np.any(default[12:23]!=0):raise ValueError('Inactive transport requires original zero default and clearance guard')
            if inactive_transport_controller is None:inactive_transport_controller=InactiveTransportRuntime(clearance_guard,ROOT,STAGE,enabled=True)
            transport_selected=bool((front_recontact_runtime is not None and front_recontact_runtime.center_local is not None) or (front_initial_runtime is not None and front_initial_runtime.center_local is not None))
            transport_row=frontal_log[-1] if frontal_log and frontal_log[-1]['step']==step else None
            transport_coordinate=coordination_log[-1] if coordination_log and coordination_log[-1]['step']==step else None
            transport_scene=None
            transport_decay=None
            if transport_selected:
                from recontact_scene import RecontactScene
                transport_target_actor='parcel_box' if side=='right' else 'mailer'
                transport_other_actor='mailer' if side=='right' else 'parcel_box'
                transport_scene=RecontactScene(clearance_guard,side,parcel_xyz(env,transport_target_actor),env.scene[transport_target_actor].data.root_quat_w.torch[0].detach().cpu().numpy(),edge_size,parcel_xyz(env,transport_other_actor),env.scene[transport_other_actor].data.root_quat_w.torch[0].detach().cpu().numpy(),obstacle_size)
                transport_decay=parameters['tasks'][task_id]['decay']
            transport_current=robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy()
            transport_previous_q=qs[-1][12:23] if qs else None
            transport_command,transport_record=inactive_transport_controller.refine(step=step,selected=transport_selected,side=side,row=transport_row,coordinate=transport_coordinate,scene=transport_scene,current=transport_current,previous_q=transport_previous_q,previous_command=previous[12:23],parent_command=action[12:23],decay=transport_decay)
            transport_record['collector_context']=dict(side=side,current=np.asarray(transport_current).tolist(),previous_q=None if transport_previous_q is None else np.asarray(transport_previous_q).tolist(),previous_command=previous[12:23].tolist(),scene=None if transport_scene is None else transport_scene.record(),decay=transport_decay)
            action[12:23]=transport_command
            inactive_transport_log.append(transport_record)
            if transport_coordinate is not None:coordination_log[-1]['inactive_transport_clearance']=transport_record
'''
line='        if clearance_guard is not None:\n            final_clearance = clearance_guard.command'
replace(line,hook+line)
line="    if args.front_loaded_z_priority:\n        episode.collect_meta['front_loaded_z_priority']=True"
replace(line,"    if args.inactive_transport_clearance:\n        episode.collect_meta['inactive_transport_clearance']="+repr(spec)+"\n        episode.collect_meta['inactive_transport_applied_frames']=sum(r['applied'] for r in inactive_transport_log)\n"+line)
line="    if args.front_loaded_z_priority:\n        (folder/'front_loaded_z_priority.json').write_text"
replace(line,"    if args.inactive_transport_clearance:\n        (folder/'inactive_transport_clearance.json').write_text(json.dumps(dict(rows=inactive_transport_log,spec="+repr(spec)+",training_ready=False),indent=2))\n"+line)
helpers=['inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py']
geometry=['audit_front_recontact_center_events.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py']
line=next(x for x in texts[name].splitlines() if 'paths.extend(STAGE/name' in x and 'front_loaded_z_priority.py' in x)
replace(line,line+'\n    if args.inactive_transport_clearance:\n        paths.extend(STAGE/name for name in '+repr(helpers+geometry)+')')
S.mkdir()
for n,text in texts.items():
 if n.endswith('.py'):ast.parse(text)
 with (S/n).open('x') as f:f.write(text)
for n in helpers+geometry:
 src=(D if n in helpers else W)/n
 assert n not in hashes
 ast.parse(src.read_text())
 with (S/n).open('xb') as f:f.write(src.read_bytes())
restored=(S/name).read_text()
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==(P/name).read_text()
unchanged=[n for n in hashes if sha(S/n)==hashes[n]];assert len(unchanged)==80
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent=str(P),parent_manifest_sha256=sha(P/'COLLECTOR_PREPARATION.json'),stage_sha256={n:sha(S/n) for n in list(hashes)+helpers+geometry},edits={name:edits},spec=spec,changed_parent_files=[name],unchanged_parent_files=unchanged,source_sha256={str(p):sha(p) for p in [Path(__file__),P/'COLLECTOR_PREPARATION.json',D/'EARLY_CAPTURE_RUNTIME_PROBE.json',*[D/n for n in helpers],*[W/n for n in geometry]]},collector_integrated=True,native_hook_checked=False,full_stream_audit_ready=False,physics_started=False,training_ready=False)
with (S/'COLLECTOR_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(sources=len(out['stage_sha256']),unchanged_parent=len(unchanged),physics_started=False)))
