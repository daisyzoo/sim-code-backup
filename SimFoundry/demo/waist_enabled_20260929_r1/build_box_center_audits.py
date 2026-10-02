"""Prepare isolated full audit versions; no old source edits and no launch."""
from pathlib import Path
import json,ast
w=Path(__file__).resolve().parent
mapping={v:v.replace('slow_drag','box_center').replace('SLOW_DRAG','BOX_CENTER') for v in json.loads((w/'SLOW_DRAG_AUDIT_VERSION_MAP.json').read_text()).values()}
mapping['staged_rear_slow_drag']='staged_box_center_preference';mapping['slow_drag_step_contract']='box_center_step_contract'
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
for a,b in mapping.items():
 if not (w/(a+'.py')).exists() or a in ['audit_slow_drag_plan','audit_slow_drag_events','slow_drag_step_contract']:continue
 s=rename((w/(a+'.py')).read_text())
 if a=='audit_slow_drag_source_contract':
  s=s.replace(" assert args.get('rear_slow_drag') is True,", " assert args.get('rear_box_center_preference') is True,'box center option missing'\n assert args.get('rear_slow_drag') is True,")
  s=s.replace("'rear_cop_route.py'];bound={}","'rear_cop_route.py','box_center_preference_plan.py'];bound={}")
  s=s.replace(" assert meta.get('rear_slow_drag') is True,", " assert meta.get('rear_box_center_preference') is True,'raw box center option missing'\n assert meta.get('rear_slow_drag') is True,")
  needle="  verify_declared_step(args,plan,meta)"
  s=s.replace(needle,needle+"\n  expected_center=dict(enabled=True,center_weight_per_m2=400.,parent='same_observation_minimum_motion',side='right',original_fallback=True,original_constraints_unchanged=True)\n  center=plan.get('unloaded_recontact_pose',{}).get('box_center_preference')\n  enabled=plan.get('rear_joint_xy_progress',{}).get('enabled',False) and plan['direction']==-1\n  if enabled:\n   assert center==expected_center and all(type(center[k]) is type(v) for k,v in expected_center.items())\n  else:assert center is None")
 if a=='audit_slow_drag_pose_live':
  s=s.replace("raw['planning'].get('minimum_motion_pose',{})", "raw['planning'].get('box_center_preference_pose' if side=='right' else 'minimum_motion_pose',{})")
  s=s.replace("'minimum_motion_lifecycle.py','elbow_torso_hulls.json'", "'minimum_motion_lifecycle.py','box_center_preference_plan.py','elbow_torso_hulls.json'")
  s=s.replace("'audit_box_center_plan.py','audit_box_center_events.py'", "'audit_box_center_plan.py','audit_box_center_preference_plan.py','audit_slow_drag_plan.py','audit_box_center_events.py'")
 p=w/(b+'.py');assert not p.exists(),p;ast.parse(s);p.write_text(s)
s=(w/'box_rate_step_contract.py').read_text().replace('(.001,.003)','(.0015,.003)').replace('rear_box_slow_drag','rear_box_center_preference').replace('expected=.001 if','expected=.0015 if');s=s.replace(" assert args['expert_frontal_top_drag_step_m']==.003", " assert args.get('rear_slow_drag') is True and meta.get('rear_slow_drag') is True\n assert args['expert_frontal_top_drag_step_m']==.003");ast.parse(s);p=w/'box_center_step_contract.py';assert not p.exists();p.write_text(s)
for a,b in {'slow_drag_run_contract':'box_center_run_contract','run_slow_drag_groups':'run_box_center_groups','watch_slow_drag_audits':'watch_box_center_audits','close_slow_drag_groups':'close_box_center_groups'}.items():
 s=rename((w/(a+'.py')).read_text()).replace('slow_drag_run_contract','box_center_run_contract')
 s=s.replace("assert prov['args']['rear_slow_drag'] is True", "assert prov['args']['rear_box_center_preference'] is True and prov['args']['rear_slow_drag'] is True")
 s=s.replace("assert meta['rear_slow_drag'] is True", "assert meta['rear_box_center_preference'] is True and meta['rear_slow_drag'] is True")
 p=w/(b+'.py');assert not p.exists();ast.parse(s);p.write_text(s)
(w/'BOX_CENTER_AUDIT_VERSION_MAP.json').write_text(json.dumps(mapping,indent=2));print('Audit/driver versions prepared; require math/source/metadata/protocol/native/lifecycle checks before freeze/launch')
