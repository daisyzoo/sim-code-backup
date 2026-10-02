"""Prepare the full isolated front interval audit inventory, without physics.
Source/profile-only adapters preserve original math and all distinct checks.
Pose uses exact compact-rejection handling; task KKT uses all active vertices.
Joint-edge/clearance repair is not included in this separate controller stage.
"""
from pathlib import Path
import re,ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=['normal_live','terminal_inputs','initial_near_half','region_continuity','region_bounds','rear_xy','pose_height','micro_clearance','contacts','pressure','loaded_parent','pose_loaded_execution','source_contract','pose_self_clearance']
fixed={'audit_closed_peak_trial_pose_live':'audit_front_interval_stage_pose_live','audit_closed_peak_trial_pose_task_optimality':'audit_front_interval_stage_pose_task_optimality','closed_peak_trial_source_binding':'front_interval_stage_source_binding','audit_front_diagonal_entry_live':'audit_front_interval_diagonal_live'}
names=set();queue=['audit_closed_peak_trial_'+s for s in initial]+['closed_peak_trial_audit_context']
while queue:
 n=queue.pop()
 if n in names:continue
 names.add(n);text=(W/(n+'.py')).read_text()
 for ref in set(re.findall(r'(?:audit_closed_peak_trial_[a-z_]+|closed_peak_trial_audit_context|closed_peak_trial_source_binding)',text)):
  if ref not in fixed and ref!='audit_closed_peak_trial_refinement' and ref not in names:queue.append(ref)
mapping={n:n.replace('audit_closed_peak_trial_','audit_front_interval_stage_').replace('closed_peak_trial_audit_context','front_interval_stage_audit_context') for n in names};mapping.update(fixed)
parents={mapping[n]:n for n in names};parents.update(audit_front_interval_stage_pose_live='audit_joint_edge_stage_pose_live_v2',audit_front_interval_stage_pose_task_optimality='audit_joint_edge_stage_task_optimality',front_interval_stage_run_contract='closed_peak_trial_run_contract')
extra={'audit_joint_edge_stage_pose_live':'audit_front_interval_stage_pose_live','audit_joint_edge_stage_contract':'audit_front_interval_stage_source_contract'}
outputs={};manifest=[]
for dest,parent in sorted(parents.items()):
 original=(W/(parent+'.py')).read_text();text=original;edits=[]
 def replace(old,new):
  global text
  count=text.count(old)
  if count:
   assert new not in text,(dest,'ambiguous inverse',new);text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 for old,new in sorted(dict(mapping,**extra).items(),key=lambda x:-len(x[0])):replace(old,new)
 replace('verify_closed_peak_trial_source','verify_front_interval_stage_source');replace('verify_joint_edge_stage_source','verify_front_interval_stage_source')
 for old in ['staged_closed_peak_trial','staged_joint_edge_clearance_intersection']:replace(old,'staged_front_corridor_interval')
 replace("['role']=='pilot'","['role']=='diagnostic'")
 for old in sorted(set(re.findall(r'CLOSED_PEAK_TRIAL_[A-Z_]+',text))):replace(old,old.replace('CLOSED_PEAK_TRIAL_','FRONT_INTERVAL_STAGE_'))
 replace('JOINT_EDGE_STAGE_POSE_LIVE_V2_AUDIT.json','FRONT_INTERVAL_STAGE_POSE_LIVE_AUDIT.json');replace('JOINT_EDGE_STAGE_POSE_LIVE_AUDIT.json','FRONT_INTERVAL_STAGE_POSE_LIVE_AUDIT.json');replace('JOINT_EDGE_STAGE_TASK_OPTIMALITY_AUDIT.json','FRONT_INTERVAL_STAGE_POSE_TASK_OPTIMALITY_AUDIT.json')
 replace('FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json','FRONT_INTERVAL_DIAGONAL_LIVE_AUDIT.json')
 if parent=='audit_joint_edge_stage_task_optimality':
  # Preserve true parent auditor attribution rather than a self-reference.
  old="frozen_parent_auditor_sha256=sha(w/'audit_front_interval_stage_pose_task_optimality.py')";new="frozen_parent_auditor_sha256=sha(w/'audit_closed_peak_trial_pose_task_optimality.py')"
  assert old in text;text=text.replace(old,new);edits.append(dict(old=old,new=new,count=1))
 ast.parse(text);recovered=text
 for e in reversed(edits):assert recovered.count(e['new'])==e['count'],(dest,e['new']);recovered=recovered.replace(e['new'],e['old'])
 assert recovered==original
 p=W/(dest+'.py');assert not p.exists(),p;outputs[p]=text;manifest.append(dict(parent=parent+'.py',parent_sha256=sha(W/(parent+'.py')),new=p.name,new_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=edits,reverse_matches=True))
for p,text in outputs.items():
 with p.open('x') as f:f.write(text)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,preparer_sha256=sha(__file__),scope=__doc__,physical_validation_pending=True,inventory_check_pending=True,training_ready=False)
with (W/'FRONT_INTERVAL_REMAINING_AUDITS_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print('prepared',len(outputs),[p.name for p in outputs])
