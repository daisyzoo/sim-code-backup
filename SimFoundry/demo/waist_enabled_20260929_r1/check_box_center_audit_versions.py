"""Check unchanged independent audit mathematics, explicit native metadata delta.
New planning objective is validated separately against actual causal inputs.
"""
from pathlib import Path
import json,ast,sys
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_box_center_source_contract import verify_box_center_source
from box_center_step_contract import verify_declared_step
import hashlib
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapping=json.loads((w/'BOX_CENTER_AUDIT_VERSION_MAP.json').read_text());same=[];sources=[]
def rename(s):
 for a,b in sorted(mapping.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 return s
for a,b in mapping.items():
 p=w/(a+'.py');q=w/(b+'.py')
 if not p.exists() or a in ['audit_slow_drag_plan','audit_slow_drag_events','slow_drag_step_contract','audit_slow_drag_source_contract']:continue
 expected=rename(p.read_text())
 if a=='audit_slow_drag_pose_live':
  expected=expected.replace("raw['planning'].get('minimum_motion_pose',{})", "raw['planning'].get('box_center_preference_pose' if side=='right' else 'minimum_motion_pose',{})")
  expected=expected.replace("'minimum_motion_lifecycle.py','elbow_torso_hulls.json'", "'minimum_motion_lifecycle.py','box_center_preference_plan.py','elbow_torso_hulls.json'")
  expected=expected.replace("'audit_box_center_plan.py','audit_box_center_events.py'", "'audit_box_center_plan.py','audit_box_center_preference_plan.py','audit_slow_drag_plan.py','audit_box_center_events.py'")
 assert ast.dump(ast.parse(expected))==ast.dump(ast.parse(q.read_text())),b;same.append(b);sources.extend([p,q])
old=ast.parse((w/'audit_slow_drag_events.py').read_text().replace('from audit_slow_drag_plan import PlanAudit','from audit_box_center_plan import PlanAudit'));assert ast.dump(old)==ast.dump(ast.parse((w/'audit_box_center_events.py').read_text()))
legacy=[]
for ep in sorted((w/'rear_slow_drag_groups_r1').glob('case_*/layout_*')):
 if not (ep/'raw.npz').exists():continue
 try:verify_box_center_source(ep)
 except AssertionError as exc:assert str(exc)=='box center option missing';legacy.append(ep.name)
 else:raise AssertionError('Old source admitted as new')
assert len(legacy)==10
for f in [Path(__file__),w/'build_box_center_audits.py',w/'BOX_CENTER_AUDIT_VERSION_MAP.json',w/'audit_box_center_source_contract.py',w/'box_center_step_contract.py',w/'audit_box_center_plan.py',w/'audit_box_center_preference_plan.py',w/'audit_box_center_events.py']:sources.append(f)
(w/'staged_box_center_preference/AUDIT_VERSION_CHECK.json').write_text(json.dumps(dict(passed=True,scope=__doc__,audit_versions_same_math_or_explicit_native_metadata=same,full_event_audit_unchanged_except_plan_dispatch=True,legacy_source_rejections=legacy,source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False),indent=2));print('PASS',len(same),'versions;10old sources rejected')
