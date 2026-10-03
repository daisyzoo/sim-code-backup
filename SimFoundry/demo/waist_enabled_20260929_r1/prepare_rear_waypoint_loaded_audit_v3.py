"""Close one additional caller of rear state replay; no runtime edits.
The loaded joint-execution auditor also reconstructs rear waypoints and must
consume independently verified post-commit state. Keep all its math unchanged.
"""
from pathlib import Path
import json,ast,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
p=W/'audit_rear_waypoint_v2_stage_pose_loaded_execution.py';s=p.read_text();a=" reference=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover);assert reference['passed'],reference['errors'];overrides={v['step'] for v in reference['records'] if v['joint_xy_override']}";b=" from audit_rear_waypoint_v2_commit import inspect_episode\n commit=inspect_episode(ep);verified=commit['independently_verified_events']['verified_post_commit']\n reference=reconstruct(fr['rows'],plan,xyz,quat,packets,key,handover,verified_post_commit=verified);assert reference['passed'],reference['errors'];overrides={v['step'] for v in reference['records'] if v['joint_xy_override']}";assert s.count(a)==1;s=s.replace(a,b);old_report='REAR_WAYPOINT_V2_STAGE_POSE_LOADED_EXECUTION_V2_AUDIT.json';new_report='REAR_WAYPOINT_V3_STAGE_POSE_LOADED_EXECUTION_V2_AUDIT.json';assert old_report in s;s=s.replace(old_report,new_report);assert s.replace(new_report,old_report).replace(b,a)==p.read_text();dst=W/'audit_rear_waypoint_v3_stage_pose_loaded_execution.py';ast.parse(s)
with dst.open('x') as f:f.write(s)
records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dst),sha256=sha(dst),replacements=[[a,b],[old_report,new_report]],exact_reverse_restore=True))
p=W/'rear_waypoint_v2_stage_run_contract.py';s=p.read_text();old='audit_rear_waypoint_v2_stage_pose_loaded_execution.py';new=dst.name;assert old in s and old_report in s;s=s.replace(old,new).replace(old_report,new_report);assert s.replace(new_report,old_report).replace(new,old)==p.read_text();dst=W/'rear_waypoint_v3_stage_run_contract.py';ast.parse(s)
with dst.open('x') as f:f.write(s)
records.append(dict(parent=str(p),parent_sha256=sha(p),path=str(dst),sha256=sha(dst),replacements=[[old,new],[old_report,new_report]],exact_reverse_restore=True))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,source_sha256={str(p):sha(p) for p in [Path(__file__),W/'REAR_WAYPOINT_V2_AUDIT_FAMILY_PREPARATION.json',W/'rear_waypoint_preparation_r1/CONFIGURATION_SOURCE_AUDIT_CHECK.json']},parent_family_preserved=True,full_inventory_still=214,physics_started=False,training_ready=False)
with (W/'REAR_WAYPOINT_LOADED_AUDIT_V3_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(dict(new_adapters=2,original_loaded_math_preserved=True))
