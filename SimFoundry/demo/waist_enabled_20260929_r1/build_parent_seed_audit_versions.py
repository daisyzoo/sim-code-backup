"""Write explicit isolated audit versions; existing frozen auditors are untouched."""
from pathlib import Path
import json
w=Path(__file__).resolve().parent
old=json.loads((w/'PRECISE_INTERIOR_AUDIT_VERSION_MAP.json').read_text())
mapping={v:v.replace('audit_precise_interior_','audit_parent_seed_').replace('PRECISE_INTERIOR_','PARENT_SEED_').replace('precise_interior_audit_context','parent_seed_audit_context').replace('staged_interior_task_precision','staged_precise_parent_seed') for v in old.values()}
mapping.update(audit_precision_source_contract='audit_parent_seed_source_contract',verify_precision_source='verify_parent_seed_source')
(w/'PARENT_SEED_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2))
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
for a,b in mapping.items():
 if a.endswith('.json') or a.startswith('staged_') or a=='verify_precision_source':continue
 p=w/(b+'.py');assert not p.exists(),p
 s=rename((w/(a+'.py')).read_text())
 if a=='audit_precision_source_contract':
  s=s.replace("names=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py']", "names=['collect_paired_sorting.py','waist_coordination_clearance.py','task_ik.py','task_ik_precision.py','joint_edge_command.py','joint_edge_adapter.py']")
  s=s.replace(" assert args.get('precise_clearance_task_ik') is True", " assert args.get('rear_joint_edge_parent_seed_retry') is True,'parent-seed flag missing/disabled'\n assert args.get('rear_joint_edge_analytic_retry') is True,'parent-seed requires original analytic retry'\n assert args.get('precise_clearance_task_ik') is True")
  s=s.replace(" return dict(passed=True,ftol=1e-13", " assert meta.get('rear_joint_edge_parent_seed_retry') is True,'raw parent-seed setting missing/disabled'\n if (ep/'frontal_bypass.json').exists():\n  plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']\n  if plan.get('rear_joint_edge_command',{}).get('enabled'):\n   expected=dict(enabled=True,prior_solver_status=8,finite_endpoint_required=True,maximum_extra_retries=1,initializer='bounded_parent_delta',original_attempts_preserved=True,objective_bounds_tolerances_unchanged=True,failed_retry='preserve_parent_command')\n   assert plan.get('rear_joint_edge_parent_seed_retry')==expected\n   assert all(type(plan['rear_joint_edge_parent_seed_retry'][k]) is type(v) for k,v in expected.items())\n  else:assert 'rear_joint_edge_parent_seed_retry' not in plan\n return dict(passed=True,ftol=1e-13")
 if a=='audit_precise_interior_pose_loaded_execution':
  s=s.replace("else w/'staged_micro_clearance_return'/name", "else w/'staged_precise_parent_seed'/name")
  s=s.replace("  verify_retry_metadata(trace,retry_enabled,eligible,f['mode'])", "  verify_parent_seed_retry_metadata(trace,enabled=args['rear_joint_edge_parent_seed_retry'],analytic_enabled=retry_enabled,eligible=bool(eligible),mode=f['mode'],original_verifier=verify_retry_metadata)")
  s=s.replace('from pathlib import Path','from audit_parent_seed_retry_metadata import verify_parent_seed_retry_metadata\nfrom pathlib import Path',1)
  s=s.replace('def replay(ep,expected_collector):\n', 'def replay(ep,expected_collector):\n from audit_parent_seed_source_contract import verify_parent_seed_source\n verify_parent_seed_source(ep)\n')
  s=s.replace("retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('analytic_retry')) for c in coords)","retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('analytic_retry')) for c in coords),parent_seed_retry_attempts=sum(bool(c.get('joint_edge_refinement',{}).get('parent_seed_retry')) for c in coords)")
 compile(s,str(p),'exec');p.write_text(s)
print('created',len(mapping)-sum(k.endswith('.json') or k.startswith('staged_') or k=='verify_precision_source' for k in mapping),'explicit modules')
