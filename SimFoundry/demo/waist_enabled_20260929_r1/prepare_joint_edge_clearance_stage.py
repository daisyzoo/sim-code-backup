"""Prepare an isolated default-off diagnostic stage; never start a simulator.
Parent peak expert is byte-bound to the ongoing frozen fresh baseline. Admission
is diagnostic only; no existing source, data or frozen audit is rewritten.
"""
from pathlib import Path
import hashlib,json,datetime,ast
W=Path(__file__).resolve().parent;PARENT=W/'staged_peak_load_guard';DEST=W/'staged_joint_edge_clearance_intersection';RUN=W/'fresh_closed_peak_trials_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((RUN/'PROTOCOL.json').read_text());assert not DEST.exists();sources={}
for p in PARENT.iterdir():
 if p.is_file() and (p.suffix=='.py' or p.name in ['causal_response_parameters.json','elbow_torso_hulls.json']):
  assert sha(p)==protocol['frozen_files_sha256'][str(p.resolve())];sources[p.name]=sha(p)
s=(PARENT/'collect_paired_sorting.py').read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new);edits.append(dict(old=old,new=new))
replace('parser = argparse.ArgumentParser()\n',"parser = argparse.ArgumentParser()\nparser.add_argument('--edge-clearance-intersection',action='store_true',help='Diagnostic original final edge command with joint elbow-clearance constraints; default off.')\n")
replace('args = parser.parse_args()\n',"""args = parser.parse_args()
if args.edge_clearance_intersection and not (args.role=='diagnostic' and args.rear_joint_edge_command and args.rear_box_inward_correction and args.self_clearance_task_ik and args.trace_substep_contacts and not args.policy_port and not args.idle and not args.waist_probe and not args.waist_pilot_contract):
    parser.error('Edge-clearance intersection requires original diagnostic edge+inward+clearance+substep configuration; no policy or pilot.')
""")
marker="            coordination_log[-1]['joint_edge_refinement']=refinement\n"
replace(marker,marker+"""            if args.edge_clearance_intersection and refinement.get('override'):
                from joint_edge_clearance_adapter_candidate import repair_record
                repaired,repair_trace=repair_record(guard=clearance_guard,row=frontal_log[-1],coordinate=coordination_log[-1],current=robot.data.joint_pos.torch[0,ordered_ids[12:23]].detach().cpu().numpy(),previous=previous[12:23],command=action[12:23],object_rotation=rotation_xyzw(target_quat),object_xyz=parcel_xyz(env,target_actor),core_size=frontal_plan['region_causal_response']['actual_core']['collision_core_size_xyz'])
                coordination_log[-1]['joint_edge_clearance_intersection']=repair_trace
                if repaired is not None:
                    action[12:23]=repaired
                else:
                    # Retain the rejected command only for the immediately following
                    # original final guard to record and stop. Never execute it.
                    assert not clearance_guard.command(action[12:23],coordination_log[-1]['upper_q'],previous[12:23])['accepted']
""")
marker="    if args.rear_box_inward_correction:\n        episode.collect_meta['rear_box_inward_correction']=True\n"
replace(marker,marker+"    if args.edge_clearance_intersection:\n        episode.collect_meta['edge_clearance_intersection']=True\n")
marker="    if args.rear_box_inward_correction:\n        paths.extend([STAGE/'joint_edge_inward_command.py',STAGE/'joint_edge_inward_adapter.py'])\n"
replace(marker,marker+"    if args.edge_clearance_intersection:\n        paths.extend([STAGE/'joint_edge_clearance_intersection_candidate.py',STAGE/'joint_edge_clearance_adapter_candidate.py'])\n")
ast.parse(s);recovered=s
for e in reversed(edits):assert recovered.count(e['new'])==1;recovered=recovered.replace(e['new'],e['old'])
assert recovered==(PARENT/'collect_paired_sorting.py').read_text()
DEST.mkdir()
for name in sources:(DEST/name).write_bytes((PARENT/name).read_bytes())
(DEST/'collect_paired_sorting.py').write_text(s)
for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py']:(DEST/name).write_bytes((W/name).read_bytes())
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(PARENT.resolve()),stage=str(DEST.resolve()),parent_protocol_sha256=sha(RUN/'PROTOCOL.json'),parent_source_sha256=sources,edits=edits,reverse_reconstruction_matches=True,stage_sha256={p.name:sha(p) for p in DEST.iterdir() if p.is_file()},default_off=True,simulation_started=False,training_ready=False,next='Full CLI rejection/acceptance, actual record adapter replay, independent joint-constraint/source audit, then original complete paired diagnostic conditions after current collector stops.')
(DEST/'PREPARATION.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['edits','parent_source_sha256','stage_sha256']},indent=2))
