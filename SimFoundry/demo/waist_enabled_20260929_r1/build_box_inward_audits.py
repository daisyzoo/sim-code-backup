"""Version complete original audit inventory for fixed nominal inward correction.
Preserve frozen parents. Native height uses separately verified measured pose.
Only loaded edge inequality and explicit metadata change; no quality relaxation.
"""
from pathlib import Path
import json,ast
w=Path(__file__).resolve().parent
mapping={v:v.replace('box_entry','box_inward').replace('BOX_ENTRY','BOX_INWARD') for v in json.loads((w/'BOX_ENTRY_AUDIT_VERSION_MAP.json').read_text()).values()}
mapping['staged_box_entry_lift']='staged_box_inward_correction'
mapping.update({x:x.replace('box_entry','box_inward') for x in ['box_entry_run_contract','run_box_entry_groups','watch_box_entry_audits','close_box_entry_groups','audit_box_entry_lift_events']})
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s.replace('BOX_ENTRY_','BOX_INWARD_')
for a,b in mapping.items():
 src=w/(a+'.py')
 if not src.exists():continue
 if a=='audit_box_entry_lift_events':src=w/'audit_box_entry_lift_events_measured.py'
 s=rename(src.read_text())
 if a=='audit_box_entry_source_contract':
  s=s.replace(" assert args.get('rear_box_entry_lift') is True,", " assert args.get('rear_box_inward_correction') is True,'inward option missing'\n assert args.get('rear_box_entry_lift') is True,")
  s=s.replace("'box_entry_lift_recontact_guarded.py'];bound={}","'box_entry_lift_recontact_guarded.py','joint_edge_inward_command.py','joint_edge_inward_adapter.py'];bound={}")
  s=s.replace(" assert meta.get('rear_box_entry_lift') is True,", " assert meta.get('rear_box_inward_correction') is True,'raw inward option missing'\n assert meta.get('rear_box_entry_lift') is True,")
  s=s.replace('  else:assert entry is None','  else:assert entry is None\n  from audit_box_inward_refinement import verify_plan\n  verify_plan(args,plan,meta)')
 if a=='audit_box_entry_pose_loaded_execution':
  # Original function retained for independent unchanged-left comparison.
  s=s.replace('def verify_refinement(', 'def verify_original_refinement(')
  s=s.replace('def replay(ep,expected_collector):','from audit_box_inward_refinement import verify_refinement,normalized_trace\n\ndef replay(ep,expected_collector):')
  s=s.replace("  verify_parent_seed_retry_metadata(trace,enabled=", "  if selected:normalized_trace(trace,inward_enabled)\n  verify_parent_seed_retry_metadata(trace,enabled=")
  s=s.replace(" lower=np.asarray(U1_JOINT_LIMIT_LO)"," inward_enabled=bool(plan.get('rear_box_inward_correction',{}).get('enabled'))\n lower=np.asarray(U1_JOINT_LIMIT_LO)")
  s=s.replace('local,core,direction,active);records.append','local,core,direction,active,inward_enabled=inward_enabled);records.append')
 if a in ['close_box_entry_groups','run_box_entry_groups']:
  s=s.replace("assert prov['args']['rear_box_entry_lift'] is True", "assert prov['args']['rear_box_inward_correction'] is True and prov['args']['rear_box_entry_lift'] is True")
  s=s.replace("assert meta['rear_box_entry_lift'] is True", "assert meta['rear_box_inward_correction'] is True and meta['rear_box_entry_lift'] is True")
 dest=w/(b+'.py');assert not dest.exists(),dest;ast.parse(s);dest.write_text(s)
(w/'BOX_INWARD_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2));print('Prepared independent audit versions, not validated, frozen or launched.')
