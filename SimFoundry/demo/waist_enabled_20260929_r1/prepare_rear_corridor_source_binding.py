"""Prepare strict source binding for the new rear recovery diagnostic stage.
Source checks and component checks do not grant physical/training admission.
"""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;parent=W/'joint_edge_stage_source_binding.py';dest=W/'rear_corridor_stage_source_binding.py';assert not dest.exists();text=parent.read_text();edits=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace(old,new):
 global text
 assert old in text;count=text.count(old);text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
replace('isolated edge/clearance diagnostic stage','isolated rear corridor recovery diagnostic stage')
replace('edge_clearance_intersection','rear_corridor_recovery')
replace('staged_joint_rear_corridor_recovery','staged_rear_corridor_recovery_guarded')
replace("for name in ['joint_rear_corridor_recovery_candidate.py','joint_edge_clearance_adapter_candidate.py']", "for name in prep['helpers']")
anchor=" return prov,None,None\n"
replace(anchor,""" checks=[Path(prep['previous_stage'])/'CHECK_V2.json',S/'PENDING_GATE_CHECK.json',W/'REAR_CORRIDOR_INDEPENDENT_RECORD_CHECK.json']
 for check in checks:
  report=json.loads(check.read_text());assert report.get('passed') is True and report.get('status','complete')=='complete',str(check)
  for field in ['frozen_sha256','source_sha256']:
   for path,h in report.get(field,{}).items():assert sha(path)==h,path
 return prov,None,None
""")
ast.parse(text);restored=text
for e in reversed(edits):assert restored.count(e['new'])==e['count'];restored=restored.replace(e['new'],e['old'])
assert restored==parent.read_text();dest.write_text(text)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent=str(parent),parent_sha256=sha(parent),new=str(dest),new_sha256=sha(dest),edits=edits,reverse_matches=True,scope=__doc__,full_audit_adapters_pending=True,physical_launched=False,training_ready=False)
(W/'REAR_CORRIDOR_SOURCE_BINDING_PREPARATION.json').write_text(json.dumps(out,indent=2));print('SOURCE_BINDING_PREPARED_FULL_AUDITS_PENDING')
