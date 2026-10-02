"""Preserve original KKT and clearance math across the verified recovery boundary.
Actual q and previous u are untouched. Parent task objective is reconstructed
before the override; final executed geometry remains independently checked.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();outputs=[]
def derive(parent,dest,changes):
 original=(W/parent).read_text();text=original;edits=[]
 for old,new in changes:
  count=text.count(old);assert count>0,(dest,old);assert new not in text,(dest,'inverse ambiguity',new)
  text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 recovered=text
 for e in reversed(edits):assert recovered.count(e['new'])==e['count'];recovered=recovered.replace(e['new'],e['old'])
 assert recovered==original;ast.parse(text);p=W/dest;assert not p.exists();p.write_text(text);outputs.append(dict(parent=parent,parent_sha256=sha(W/parent),new=dest,new_sha256=sha(p),edits=edits,reverse_matches=True))
derive('audit_joint_edge_stage_task_optimality.py','audit_rear_corridor_stage_pose_task_optimality.py',[
 ('def verify_task_rows(ep,geom,verified_events):','def verify_task_rows(ep,geom,verified_events):\n from rear_corridor_audit_inputs import verify_inputs\n recovery=verify_inputs(ep,repo,w/\'staged_rear_corridor_recovery_guarded\')'),
 (" lo=np.asarray(U1_JOINT_LIMIT_LO)"," experts={t:recovery.parent_expert(t,x) for t,x in experts.items()}\n lo=np.asarray(U1_JOINT_LIMIT_LO)"),
 (" bad=[r for r in records", " recovery.assert_unchanged()\n bad=[r for r in records"),
 ('audit_joint_edge_stage_pose_live','audit_rear_corridor_stage_pose_live'),
 ('JOINT_EDGE_STAGE_POSE_LIVE_AUDIT.json','REAR_CORRIDOR_STAGE_POSE_LIVE_AUDIT.json'),
 ('JOINT_EDGE_STAGE_TASK_OPTIMALITY_AUDIT.json','REAR_CORRIDOR_STAGE_POSE_TASK_OPTIMALITY_AUDIT.json'),
 ("out.update(stationarity_version=VERSION", "out.update(recovery_input_auditor_sha256=sha(w/'rear_corridor_audit_inputs.py'),recovery_log_sha256=sha(ep/'rear_corridor_recovery.json'),stationarity_version=VERSION"),
 ])
derive('audit_closed_peak_trial_pose_self_clearance.py','audit_rear_corridor_stage_pose_self_clearance.py',[
 (" ep=Path(ep).resolve();case=ep.parent;", " ep=Path(ep).resolve()\n from rear_corridor_audit_inputs import verify_inputs\n recovery=verify_inputs(ep,repo,w/'staged_rear_corridor_recovery_guarded')\n case=ep.parent;"),
 ('audit_closed_peak_trial_pose_live','audit_rear_corridor_stage_pose_live'),
 ('CLOSED_PEAK_TRIAL_POSE_LIVE_AUDIT.json','REAR_CORRIDOR_STAGE_POSE_LIVE_AUDIT.json'),
 ('CLOSED_PEAK_TRIAL_POSE_SELF_CLEARANCE_AUDIT.json','REAR_CORRIDOR_STAGE_POSE_SELF_CLEARANCE_AUDIT.json'),
 ('  near(target,u[t],0);controller_frames+=1',"  if t in recovery.overrides:\n   override=recovery.overrides[t];near(target,override['parent_command'],0);target=np.array(override['emitted_command'],dtype=np.float32)\n  near(target,u[t],0);controller_frames+=1"),
 (" return dict(passed=True,executed_frames=count", " recovery.assert_unchanged()\n return dict(passed=True,recovery_overrides=len(recovery.overrides),recovery_input_auditor_sha256=sha(w/'rear_corridor_audit_inputs.py'),executed_frames=count"),
 ])
with (W/'REAR_CORRIDOR_COMMAND_AUDITS_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=outputs,preparer_sha256=sha(__file__),training_ready=False,physical_launch_allowed=False),f,indent=2)
print('prepared',len(outputs))
