"""Reversible full pose adapter: retain compact rejection and native raw actions."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
outputs=[]
def derive(parent,dest,changes):
    original=(W/parent).read_text();text=original;edits=[]
    for old,new in changes:
        count=text.count(old);assert count>0,(dest,old);assert new not in text,(dest,'inverse ambiguity',new)
        text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
    recovered=text
    for e in reversed(edits):assert recovered.count(e['new'])==e['count'];recovered=recovered.replace(e['new'],e['old'])
    assert recovered==original;ast.parse(text);p=W/dest;assert not p.exists();p.write_text(text)
    outputs.append(dict(parent=parent,parent_sha256=sha(W/parent),new=dest,new_sha256=sha(p),edits=edits,reverse_matches=True))
derive('audit_rear_corridor_transport_events.py','audit_rear_corridor_transport_events_v2.py',[
 ('from audit_closed_peak_trial_lift_events import EventAudit as ParentAudit','from audit_compact_scene_rejection import EventAudit as ParentAudit')])
derive('audit_joint_edge_stage_pose_live_v2.py','audit_rear_corridor_stage_pose_live.py',[
 ('from audit_compact_scene_rejection import EventAudit,has_compact_rejection','from audit_compact_scene_rejection import has_compact_rejection\nfrom audit_rear_corridor_transport_events_v2 import EventAudit\nfrom rear_corridor_audit_inputs import verify_inputs'),
 ("FILES=['raw.npz'","FILES=['rear_corridor_recovery.json','peak_load_updates.json','raw.npz'"),
 ('    ep=Path(ep)\n    with np.load', '    ep=Path(ep)\n    recovery=verify_inputs(ep,repo,stage)\n    with np.load'),
 ('record=audit.verify(event,step=t,','record=audit.verify(event,require_rear_transport=t in recovery.required_transport_steps,step=t,'),
 ('    normal=verify_normal_rows(q,coords,experts,set(fs),verified,audit.hand,side)','    recovery.assert_unchanged()\n    normal=verify_normal_rows(q,coords,experts,set(fs),verified,audit.hand,side)'),
 ('records=records,normal=normal,scope=__doc__','records=records,normal=normal,recovery_boundary=recovery.proof,required_transport_steps=sorted(recovery.required_transport_steps),scope=__doc__'),
 ("stage=w/'staged_joint_edge_clearance_intersection'","stage=w/'staged_rear_corridor_recovery_guarded'"),
 ('    from audit_joint_edge_stage_contract import verify_joint_edge_stage_source\n    verify_joint_edge_stage_source(ep)','    from rear_corridor_stage_source_binding import verify_observation_binding\n    verify_observation_binding(ep)'),
 ("['audit_compact_scene_rejection.py','audit_closed_peak_trial_plan.py'","['rear_corridor_audit_inputs.py','audit_rear_corridor_native_commands_v2.py','audit_rear_corridor_command_records.py','rear_corridor_stationarity.py','support_vertex_stationarity.py','rear_corridor_stage_source_binding.py','audit_rear_corridor_transport_events_v2.py','audit_rear_transport_witness.py','audit_compact_scene_rejection.py','audit_closed_peak_trial_plan.py'"),
 ('JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json','REAR_CORRIDOR_STAGE_POSE_LIVE_AUDIT.json'),
 ])
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=outputs,preparer_sha256=sha(__file__),helper_sha256=sha(W/'rear_corridor_audit_inputs.py'),training_ready=False,physical_launch_allowed=False)
with (W/'REAR_CORRIDOR_POSE_AUDIT_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print('prepared',len(outputs))
