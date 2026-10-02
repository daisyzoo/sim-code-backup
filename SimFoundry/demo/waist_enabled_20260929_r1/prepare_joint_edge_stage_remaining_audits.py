"""Create isolated diagnostic audit adapters; retain reversible parent changes."""
from pathlib import Path
import re,ast,json,hashlib,datetime
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=['normal_live','terminal_inputs','initial_near_half','region_continuity','region_bounds','rear_xy','pose_height','micro_clearance','contacts','pressure','loaded_parent','pose_loaded_execution']
names=set();queue=['audit_closed_peak_trial_'+s for s in initial]+['closed_peak_trial_audit_context']
preexisting={'audit_closed_peak_trial_pose_live':'audit_joint_edge_stage_pose_live','audit_closed_peak_trial_pose_self_clearance':'audit_joint_edge_stage_self_clearance','audit_closed_peak_trial_pose_task_optimality':'audit_joint_edge_stage_task_optimality','audit_closed_peak_trial_source_contract':'audit_joint_edge_stage_contract','closed_peak_trial_source_binding':'joint_edge_stage_source_binding'}
while queue:
 n=queue.pop()
 if n in names:continue
 names.add(n);t=(W/(n+'.py')).read_text()
 for ref in set(re.findall(r'(?:audit_closed_peak_trial_[a-z_]+|closed_peak_trial_audit_context|closed_peak_trial_source_binding)',t)):
  if ref not in preexisting and ref!='audit_closed_peak_trial_refinement' and ref not in names:queue.append(ref)
mapping={n:n.replace('audit_closed_peak_trial_','audit_joint_edge_stage_').replace('closed_peak_trial_audit_context','joint_edge_stage_audit_context') for n in names};mapping.update(preexisting)
manifest=[]
for n in sorted(names):
 original=(W/(n+'.py')).read_text();text=original;edits=[]
 def replace(old,new,required=False):
  global text
  count=text.count(old)
  if required:assert count,(n,old)
  if count:
   assert new not in text,(n,'ambiguous inverse',new)
   text=text.replace(old,new);edits.append(dict(old=old,new=new,count=count))
 for old,new in sorted(mapping.items(),key=lambda x:-len(x[0])):replace(old,new)
 replace('verify_closed_peak_trial_source','verify_joint_edge_stage_source')
 replace('CLOSED_PEAK_TRIAL_POSE_SELF_CLEARANCE_AUDIT.json','JOINT_EDGE_STAGE_SELF_CLEARANCE_AUDIT.json')
 replace('CLOSED_PEAK_TRIAL_POSE_TASK_OPTIMALITY_AUDIT.json','JOINT_EDGE_STAGE_TASK_OPTIMALITY_AUDIT.json')
 for report in sorted(set(re.findall(r'CLOSED_PEAK_TRIAL_[A-Z_]+',text))):replace(report,report.replace('CLOSED_PEAK_TRIAL_','JOINT_EDGE_STAGE_'))
 replace("['role']=='pilot'","['role']=='diagnostic'")
 replace("w/'staged_closed_peak_trial'","w/'staged_joint_edge_clearance_intersection'")
 if n=='audit_closed_peak_trial_pose_loaded_execution':
  replace("assert not any('joint_edge_refinement' in c for c in coords)","assert not any('joint_edge_refinement' in c or 'joint_edge_clearance_intersection' in c for c in coords)",True)
  replace(" loaded_parent,task_evidence=build_parent_verifier(ep,expected_collector.parent)",""" loaded_parent,task_evidence=build_parent_verifier(ep,expected_collector.parent)
 from audit_unloaded_wrist_prior_live import HandModel
 from audit_self_clearance_task_optimality import IndependentElbows
 from audit_joint_edge_clearance_record import verify as verify_intersection
 independent_hand_model=HandModel(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
 elbows=IndependentElbows(expected_collector.parent/'elbow_torso_hulls.json',repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf')
 intersection_checks=[]""",True)
  replace("near(trace['final_upper_command'],u[t],0)","edge_final=np.asarray(trace['final_upper_command'],dtype=np.float32);near(edge_final,trace['final_upper_command'],0)",True)
  replace("  else:assert trace is None;parent=u[t]","""  else:assert trace is None;parent=u[t];edge_final=u[t]
  needs_intersection=bool(trace and trace['override'])
  assert ('joint_edge_clearance_intersection' in c)==needs_intersection
  if not needs_intersection:near(edge_final,u[t],0)""",True)
  replace("verify_refinement(trace,parent,u[t],u[t-1]","verify_refinement(trace,parent,edge_final,u[t-1]",True)
  replace("inward_enabled=inward_enabled);records.append(dict(step=t,**check))","""inward_enabled=inward_enabled);records.append(dict(step=t,**check))
  if needs_intersection:
   proof=verify_intersection(hand=independent_hand_model,elbows=elbows,coordinate=c,row=f,trace=c['joint_edge_clearance_intersection'],q=q[t].astype(float),previous=u[t-1].astype(float),command=u[t].astype(float),object_xyz=xyz[t],object_rotation=R[t],core_size=plan['region_causal_response']['actual_core']['collision_core_size_xyz'],lower=lower,upper=upper,limits=limits)
   assert proof['passed'];intersection_checks.append(dict(step=t,**proof))""",True)
  replace('nonlinear_task_execution=task_evidence,','nonlinear_task_execution=task_evidence,final_intersection_records=intersection_checks,final_intersection_changed=sum(v["changed"] for v in intersection_checks),',True)
 ast.parse(text)
 recovered=text
 for e in reversed(edits):
  assert recovered.count(e['new'])==e['count'],(n,e)
  recovered=recovered.replace(e['new'],e['old'])
 assert recovered==original
 path=W/(mapping[n]+'.py');assert not path.exists(),'do not overwrite prepared audits'
 path.write_text(text)
 manifest.append(dict(parent=n+'.py',parent_sha256=sha(W/(n+'.py')),new=path.name,new_sha256=sha(path),changes=edits,reverse_matches=True))
# Preserve the declared inventory, including all unmodified common audits.
n='closed_peak_trial_run_contract';original=(W/(n+'.py')).read_text();text=original
for old,new in sorted(mapping.items(),key=lambda x:-len(x[0])):text=text.replace(old,new)
text=text.replace('CLOSED_PEAK_TRIAL_POSE_SELF_CLEARANCE_AUDIT.json','JOINT_EDGE_STAGE_SELF_CLEARANCE_AUDIT.json').replace('CLOSED_PEAK_TRIAL_POSE_TASK_OPTIMALITY_AUDIT.json','JOINT_EDGE_STAGE_TASK_OPTIMALITY_AUDIT.json')
text=text.replace('CLOSED_PEAK_TRIAL_','JOINT_EDGE_STAGE_');ast.parse(text)
p=W/'joint_edge_stage_run_contract.py';assert not p.exists();p.write_text(text)
manifest.append(dict(parent=n+'.py',parent_sha256=sha(W/(n+'.py')),new=p.name,new_sha256=sha(p),scope='Declared audit inventory renamed for isolated reports; original common audit inventory preserved.'))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest,training_ready=False,physical_validation_pending=True,scope='Original mathematics retained. Final executed action is checked against the independent joint-intersection certificate, while original edge refinement is checked against its own unchanged recorded output. No old audit or runtime file modified.')
(W/'JOINT_EDGE_STAGE_REMAINING_AUDITS_PREPARATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(prepared=len(manifest),physical_validation_pending=True)))
