"""Bind full original closure to front-normal trial and retain all failed conditions.
No collection, report closure, actual-image approval or data admission here.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;P=W/'front_normal_physical_preparation_r3';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=W/'close_front_effective_height_trial1_physical_v1.py';dest=W/'close_front_normal_trial1_physical_v1.py';assert not dest.exists()
s=src.read_text();mapping={
'front_effective_height_r1_v4_stage_run_contract':'front_normal_stage_run_contract_v1',
'front_loaded_z_quarter_physical_r2':'front_effective_height_physical_r1',
'audit_front_effective_height_r1_v1_stage_contacts':'audit_front_normal_contacts_v2',
'audit_front_effective_height_r1_v1_stage_pressure':'audit_front_normal_pressure_files_v1',
'audit_front_effective_height_r1_v1_stage_release':'audit_front_normal_stage_r1_v1_stage_release',
'FRONT_EFFECTIVE_HEIGHT_R1':'FRONT_NORMAL_R1',
'effective_height_against_quarter_parent':'front_normal_against_effective_height_parent',
}
for a,b in mapping.items():s=s.replace(a,b)
compile(s,str(dest),'exec');dest.write_text(s)
# Exact old algorithm after explicit names; preserve224, full groups, actual views.
assert ast.dump(ast.parse(dest.read_text()),include_attributes=False)==ast.dump(ast.parse(s),include_attributes=False)
for required in ["len(results)==10 and len(all_rows)==224", "actual['actual_visual_review'].startswith('completed_actual_view')", "len(rs)==5", "push_total=4", "training_ready=False,model_goal_achieved=False"]:assert required in s
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,binding_renames=mapping,expected_conditions=10,expected_audits=224,actual_visual_review_required=True,direct_parent='front_effective_height_physical_r1',only_prepared=True,training_ready=False,source_sha256={str(p):sha(p) for p in [Path(__file__),src,dest]})
with (P/'CLOSURE_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(dict(prepared=str(dest),actual_physical_results_available=False))
