"""Create explicit new-source audit versions; never modify frozen predecessors."""
from pathlib import Path
import json
w=Path(__file__).resolve().parent;old=json.loads((w/'PARENT_SEED_AUDIT_VERSION_MAP.json').read_text());mapping={v:v.replace('audit_parent_seed_','audit_minimum_motion_').replace('PARENT_SEED_','MINIMUM_MOTION_').replace('parent_seed_audit_context','minimum_motion_audit_context').replace('staged_precise_parent_seed','staged_minimum_motion_recontact').replace('verify_parent_seed_source','verify_minimum_motion_source') for v in old.values()}
(w/'MINIMUM_MOTION_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2))
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
for a,b in mapping.items():
 if a.endswith('.json') or a.startswith('staged_') or a=='verify_parent_seed_source':continue
 p=w/(b+'.py');assert not p.exists(),p;s=rename((w/(a+'.py')).read_text())
 if a=='audit_parent_seed_source_contract':
  s=s.replace(" assert args.get('rear_joint_edge_parent_seed_retry') is True", " assert args.get('minimum_motion_recontact') is True,'minimum-motion flag missing/disabled'\n assert args.get('rear_joint_edge_parent_seed_retry') is True")
  s=s.replace("'joint_edge_command.py','joint_edge_adapter.py']","'joint_edge_command.py','joint_edge_adapter.py','recontact_plan.py','recontact_lifecycle.py','minimum_motion_recontact.py','minimum_motion_lifecycle.py']")
  s=s.replace(" assert meta.get('rear_joint_edge_parent_seed_retry') is True", " assert meta.get('minimum_motion_recontact') is True,'raw minimum-motion flag missing/disabled'\n assert meta.get('rear_joint_edge_parent_seed_retry') is True")
  s=s.replace(" return dict(passed=True,ftol=1e-13", " if (ep/'frontal_bypass.json').exists():\n  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']\n  if plan.get('rear_joint_xy_progress',{}).get('enabled'):\n   expected=dict(enabled=True,alignment_abs_min=.8,preferred_inset_m=.020,seed_policy=['original_endpoint','current_observed'],lift_heights_m=[.015,.030,.060],original_fallback=True,whole_sampled_path_check=True,maximum_ticks=240,training_ready=False)\n   actual=plan['unloaded_recontact_pose'].get('minimum_motion_pose');assert actual==expected\n   assert all(type(actual[k]) is type(v) for k,v in expected.items())\n  else:assert 'minimum_motion_pose' not in plan.get('unloaded_recontact_pose',{})\n return dict(passed=True,ftol=1e-13")
 if a=='audit_parent_seed_pose_live':
  s=s.replace('from audit_recontact_interior_events import EventAudit','from audit_minimum_motion_events import EventAudit')
  s=s.replace("    audit=EventAudit(repo,stage);verified={};records=[];", "    for raw in evs.values():\n        if raw.get('planning') is not None:assert raw['planning'].get('minimum_motion_pose',{}).get('enabled') is True,'new planning metadata missing'\n    audit=EventAudit(repo,stage);verified={};records=[];")
  s=s.replace("['recontact_interior_preference','unloaded_recontact_pose'", "['minimum_motion_recontact','recontact_interior_preference','unloaded_recontact_pose'")
  s=s.replace("'recontact_adapter.py','elbow_torso_hulls.json']", "'recontact_adapter.py','minimum_motion_recontact.py','minimum_motion_lifecycle.py','elbow_torso_hulls.json']")
  s=s.replace("    assert meta['recontact_interior_preference'] is True", "    assert meta['minimum_motion_recontact'] is True\n    assert meta['recontact_interior_preference'] is True")
  s=s.replace("['audit_recontact_interior_events.py','audit_recontact_pose_events.py'", "['audit_minimum_motion_plan.py','audit_minimum_motion_events.py','audit_recontact_interior_events.py','audit_recontact_pose_events.py'")
 if a=='audit_parent_seed_pose_loaded_execution':
  before="   assert c['self_clearance_task']['accepted'] is True and c['self_clearance_task']['override'] is False, 'Changed loaded task IK requires dedicated nonlinear task execution audit'\n   replay_record(c,f,ex[t],q[t],u[t-1],parent,side,solver);parent_count+=1"
  assert before in s;s=s.replace(before,"   loaded_parent(c,f,ex[t],q[t],u[t-1],parent,side,solver);parent_count+=1")
  needle=" assert {r['step'] for r in fr['rows']}==set(range(1,1200))";assert needle in s;s=s.replace(needle," from audit_minimum_motion_loaded_parent import build_parent_verifier\n loaded_parent,task_evidence=build_parent_verifier(ep,expected_collector.parent)\n"+needle)
  s=s.replace("return dict(passed=True,selected=selected,parent_full_push_replay_frames=parent_count", "return dict(passed=True,selected=selected,nonlinear_task_execution=task_evidence,parent_full_push_replay_frames=parent_count")
  s=s.replace('Original full rear force/refinement audit for new clearance runs whose loaded IK remained original. Explicitly rejects a changed loaded task IK; not general clearance execution admission. Never imports candidate solver.','Full rear force/refinement audit with independently verified nonlinear task-parent execution. Original force/edge mathematics and guards remain; no candidate nonlinear solver is executed.')
 compile(s,str(p),'exec');p.write_text(s)
print('created explicit minimum-motion modules; not yet preflight-approved or physical')
