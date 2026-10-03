"""Bind self-clearance's loaded-command verifier and downstream digest to V2.
No task/geometry mathematics change; retain previous draft sources and manifests.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_center';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[]
jobs=[('audit_front_recontact_v1_stage_self_clearance.py','audit_front_recontact_v3_stage_self_clearance.py',[('from audit_front_recontact_v1_execution import inspect as inspect_priority','from audit_front_recontact_v2_execution import inspect as inspect_priority'),('FRONT_RECONTACT_V1_STAGE_SELF_CLEARANCE','FRONT_RECONTACT_V3_STAGE_SELF_CLEARANCE')]),('audit_front_recontact_v1_stage_pose_loaded_execution.py','audit_front_recontact_v3_stage_pose_loaded_execution.py',[('FRONT_RECONTACT_V1_STAGE_SELF_CLEARANCE','FRONT_RECONTACT_V3_STAGE_SELF_CLEARANCE'),('audit_front_recontact_v1_stage_self_clearance','audit_front_recontact_v3_stage_self_clearance'),('FRONT_RECONTACT_V1_STAGE_POSE_LOADED_EXECUTION','FRONT_RECONTACT_V3_STAGE_POSE_LOADED_EXECUTION')]),('front_recontact_v2_stage_run_contract.py','front_recontact_v3_stage_run_contract.py',[('audit_front_recontact_v1_stage_self_clearance','audit_front_recontact_v3_stage_self_clearance'),('FRONT_RECONTACT_V1_STAGE_SELF_CLEARANCE','FRONT_RECONTACT_V3_STAGE_SELF_CLEARANCE'),('audit_front_recontact_v1_stage_pose_loaded_execution','audit_front_recontact_v3_stage_pose_loaded_execution'),('FRONT_RECONTACT_V1_STAGE_POSE_LOADED_EXECUTION','FRONT_RECONTACT_V3_STAGE_POSE_LOADED_EXECUTION')])]
for a,b,changes in jobs:
 p=W/a;t=W/b;s=p.read_text();edits=[]
 for old,new in changes:
  count=s.count(old);assert count>0 and new not in s;s=s.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 ast.parse(s);back=s
 for e in reversed(edits):assert back.count(e['new'])==e['count'];back=back.replace(e['new'],e['old'])
 assert back==p.read_text()
 with t.open('x') as f:f.write(s)
 rows.append(dict(parent=str(p),parent_sha256=sha(p),path=str(t),sha256=sha(t),edits=edits))
with (S/'AUDIT_V3_PREPARATION.json').open('x') as f:json.dump(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,records=rows,source_sha256={str(Path(__file__)):sha(__file__)},full_audit_family_ready=False,simulation_started=False,training_ready=False),f,indent=2)
print('prepared3 dependent adapters')
