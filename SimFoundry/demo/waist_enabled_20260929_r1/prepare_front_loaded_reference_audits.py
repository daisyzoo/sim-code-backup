"""Name-isolated original audit adapters plus material-cap-aware COP admission.
Original formulas and thresholds stay intact. The missing region causal helper
is explicitly included now, while the old run's missing dependency stays absent.
No report here claims new-source native fixtures or physical launch readiness.
"""
from pathlib import Path
import ast,datetime,hashlib,json
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();records=[]
replacements=[('audit_front_initial_center_live_v2','audit_front_loaded_initial_live'),('front_initial_stage','front_loaded_stage'),('FRONT_INITIAL_STAGE','FRONT_LOADED_STAGE'),('staged_front_initial_center','staged_front_loaded_reference')]
def rename(s):
 for a,b in replacements:s=s.replace(a,b)
 return s

def write(parent,dest,s,edits=None):
 dest=W/dest;assert not dest.exists(),dest;ast.parse(s);dest.write_text(s);records.append(dict(parent=str(parent.resolve()),parent_sha256=sha(parent),path=str(dest.resolve()),sha256=sha(dest),edits=edits or [],global_replacements=replacements))
for p in sorted(W.glob('audit_front_initial_stage_*.py')):
 write(p,p.name.replace('front_initial_stage','front_loaded_stage'),rename(p.read_text()))
for name in ['front_initial_stage_audit_context.py','audit_front_initial_center_live_v2.py']:
 p=W/name;write(p,rename(name),rename(p.read_text()))
# Recover the original missing helper from its reviewed, unchanged margin parent.
p=W/'audit_terminal_margin_stage_region_causal.py';s=p.read_text().replace('terminal_margin_stage','front_loaded_stage').replace('TERMINAL_MARGIN_STAGE','FRONT_LOADED_STAGE').replace('staged_terminal_release_margin','staged_front_loaded_reference');write(p,'audit_front_loaded_stage_region_causal.py',s,[dict(kind='name_only_terminal_margin_parent')])
# The new stage changes only the collector and adds two audited helpers.
p=W/'front_initial_center_stage_source_binding.py';s=p.read_text().replace('staged_front_initial_center','staged_front_loaded_reference');edits=[]
def edit(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);edits.append(dict(old=a,new=b))
a=" coordinated=(S/'waist_coordination_clearance.py').read_text();e=prep['coordination_edits']\n assert coordinated.count(e['added_branch'])==1\n assert coordinated.replace(e['added_branch'],'').replace(e['signature_new'],e['signature_old'])==(parent/'waist_coordination_clearance.py').read_text()"
edit(a," assert (S/'waist_coordination_clearance.py').read_bytes()==(parent/'waist_coordination_clearance.py').read_bytes()\n assert json.loads((parent/'CHECK.json').read_text())['stage_sha256']==parent_prep['stage_sha256']")
a=" settings=semantic_settings(args);assert settings.pop('front_initial_center_landing') is True;"
# This source deliberately uses one long line; replace its exact unique fragment.
a="settings=semantic_settings(args);assert settings.pop('front_initial_center_landing') is True;"
edit(a,"assert args['front_loaded_reference_cap'] is True;settings=semantic_settings(args);assert settings.pop('front_loaded_reference_cap') is True;assert settings.pop('front_initial_center_landing') is True;")
a=" for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py',*sorted(helpers)]:"
edit(a," inherited_helpers={Path(name).name for name in parent_prep['helper_source_sha256']}\n for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py',*sorted(helpers|inherited_helpers)]:")
a=" assert meta['front_initial_center_landing'] is True;"
edit(a," assert meta['front_loaded_reference_cap'] is True\n"+a)
a=" if selected:\n  declaration=plan['front_initial_center_landing'];"
edit(a,""" if selected:
  cap_expected=dict(enabled=True,cap_world_xy_axis_m=.010,max_command_step_axis_m=.003,max_hand_reference_lead_axis_m=.030,min_normal_load_n=.3,scope='Only measured initial-front capture, loaded top_push, after parent safety/COP',empty_intersection='stop_before_current_action_and_record_failed_episode',parent_pressure_and_z_unchanged=True,no_physical_success_claim=True,training_ready=False)
  assert plan['front_loaded_reference_cap']==meta['frontal_bypass_plan']['front_loaded_reference_cap']==cap_expected
  declaration=plan['front_initial_center_landing'];""")
a="  if task!='wait_no_package':assert 'front_initial_center_landing' not in plan"
edit(a,"  if task!='wait_no_package':assert 'front_initial_center_landing' not in plan and 'front_loaded_reference_cap' not in plan")
write(p,'front_loaded_stage_source_binding.py',s,edits)
# Source-specific full COP CLI keeps original config/asset checks and uses the
# independently reconstructed parent waypoint before material-cap verification.
p=W/'audit_front_diagonal_entry_live.py';main=p.read_text().split("if __name__=='__main__':",1)[1];main="if __name__=='__main__':"+main
s='''"""Independent parent COP and material-cap audit, full native/source binding."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from audit_front_loaded_reference_cop_math import reconstruct
from audit_front_loaded_material_cap import MaterialCapAudit
from audit_unloaded_wrist_prior_live import HandModel
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
'''+main;edits=[]
a=" p=Path(sys.argv[1]).resolve();log="
edit(a," p=Path(sys.argv[1]).resolve()\n from front_loaded_stage_source_binding import verify_observation_binding\n from front_loaded_stage_audit_context import verified_front_events\n source_binding=verify_observation_binding(p);front_events=verified_front_events(p);cap_result=None\n log=")
a="  packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']};records,errors=reconstruct(log['rows'],log['plan'],tr,ori,packets,'box' if 'push_box' in p.name else 'mailer')"
edit(a,"""  packets={x['after_action_step']:x for x in json.loads((p/'solved_contact_forces.json').read_text())['rows']}
  with np.load(p/'raw.npz') as z:q=z['q'][:,12:23].astype(float)
  key='box' if 'push_box' in p.name else 'mailer'
  hand=HandModel(ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',ROOT/'assets/robots/g1_hand_support_vertices.json')
  cap_audit=MaterialCapAudit(log['rows'],log['plan'],tr[key],ori[key],packets,key,q,hand,front_events,enabled=args['front_loaded_reference_cap'])
  records,errors=reconstruct(log['rows'],log['plan'],tr,ori,packets,key,material_cap_audit=cap_audit);cap_result=cap_audit.finish()""")
a=" else:\n  errors=[[r['step'],'unexpected_COP_trace']"
edit(a," else:\n  assert all('loaded_reference_cap' not in r for r in log['rows'])\n  errors=[[r['step'],'unexpected_COP_trace']")
s=s.replace('FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json','FRONT_LOADED_STAGE_COP_AUDIT.json').replace('report=dict(passed=not errors,','report=dict(material_cap=cap_result,source_binding=source_binding,dependent_auditors_sha256={str(W/n):hashlib.sha256((W/n).read_bytes()).hexdigest() for n in [\'audit_front_loaded_reference_cop_math.py\',\'audit_front_loaded_material_cap.py\',\'front_initial_center_reference_ledger.py\',\'audit_unloaded_wrist_prior_live.py\']},passed=not errors,')
write(p,'audit_front_loaded_stage_cop.py',s,edits)
# Do not write or repair the old omitted path.
assert not (W/'audit_front_initial_stage_region_causal.py').exists()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adapters=records,generator_sha256=sha(__file__),syntax_passed=True,new_source_native_fixture_tested=False,transitive_dependencies_tested=False,simulation_started=False,training_ready=False)
dest=W/'FRONT_LOADED_STAGE_AUDITS_PREPARATION.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2));print('Prepared',len(records),'new audit modules; no physics readiness claim')
