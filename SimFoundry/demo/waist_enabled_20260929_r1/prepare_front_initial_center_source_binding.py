"""Versioned source binding retains original margin/substep/force requirements."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;A=W/'terminal_margin_stage_source_binding.py';B=W/'front_initial_center_stage_source_binding.py';assert not B.exists();s=A.read_text();edits=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def edit(old,new):
 global s
 assert s.count(old)==1,old;s=s.replace(old,new);edits.append(dict(old=old,new=new))
edit("S=W/'staged_terminal_release_margin'","S=W/'staged_front_initial_center'")
a=" assert sha(W/'joint_edge_intersection_physical_r1/RESULT_WITH_SUPPLEMENT.json')==prep['parent_closed_result_sha256']\n assert sha(W/'CONFIRMED_RELEASE_MARGIN_HISTORY_CHECK.json')==prep['history_check_sha256']"
b=" assert sha(W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json')=="+repr(sha(W/'terminal_margin_physical_r1/RESULT_WITH_SUPPLEMENT.json'))+"\n check=json.loads((S/'CHECK.json').read_text());assert check['passed'] is True and check['stage_sha256']==prep['stage_sha256']"
edit(a,b)
a=" for name in prep['stage_sha256']:\n  if name not in ['collect_paired_sorting.py',*prep['new_helpers']]:assert sha(S/name)==sha(parent/name)"
b=""" coordinated=(S/'waist_coordination_clearance.py').read_text();e=prep['coordination_edits']
 assert coordinated.count(e['added_branch'])==1
 assert coordinated.replace(e['added_branch'],'').replace(e['signature_new'],e['signature_old'])==(parent/'waist_coordination_clearance.py').read_text()
 helpers={Path(name).name for name in prep['helper_source_sha256']}
 for name in prep['stage_sha256']:
  if name not in {'collect_paired_sorting.py','waist_coordination_clearance.py'}|helpers:assert sha(S/name)==sha(parent/name)
 for original,h in prep['helper_source_sha256'].items():
  assert sha(original)==h
  name=Path(original).name;content=Path(original).read_text()
  if name=='front_initial_center_top_contact.py':content=content.replace('Path(__file__).resolve().parents[2]','Path(__file__).resolve().parents[3]')
  assert (S/name).read_text()==content
"""
edit(a,b)
edit("args=prov['args'];assert args['terminal_release_margin']", "args=prov['args'];assert args['front_initial_center_landing'] is True;assert args['terminal_release_margin']")
edit("settings=semantic_settings(args);assert settings.pop('terminal_release_margin')", "settings=semantic_settings(args);assert settings.pop('front_initial_center_landing') is True;assert settings.pop('terminal_release_margin')")
edit(" for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py']:"," for name in ['joint_edge_clearance_intersection_candidate.py','joint_edge_clearance_adapter_candidate.py','margin_confirmed_position_release.py',*sorted(helpers)]:")
edit(" assert meta['terminal_release_margin'] is True", " assert meta['front_initial_center_landing'] is True;assert meta['front_initial_center_failure'] is None;assert meta['terminal_release_margin'] is True")
a=" files=[case/'provenance.json'"
b=""" front=json.loads((ep/'front_initial_center.json').read_text());assert front['training_ready'] is False
 selected=False if task=='wait_no_package' else bool(plan.get('front_route_selected'))
 assert front['selected'] is selected
 if selected:
  declaration=plan['front_initial_center_landing'];assert declaration==meta['frontal_bypass_plan']['front_initial_center_landing']
  assert declaration['enabled'] is True and declaration['maximum_ticks']==240 and declaration['actual_ready_frames']==3
  assert declaration['center_xy_m']==.002 and declaration['precontact_height_m']==[.006,.007] and declaration['measured_height_m']==[.004,.010]
  assert declaration['alignment_abs_min']==.8 and declaration['numerical_tolerance']==2e-7 and declaration['causal_preflight_only'] is True
  assert declaration['no_plan_behavior']=='original_parent_before_any_override' and declaration['parameter_sha256']==sha(S/'causal_response_parameters.json')
  assert declaration['actual_core']==plan['front_cop_slip_following']['edge_speed']['actual_core']
  assert front['rows'] and all(r['kind']!='stop' for r in front['rows'])
 else:
  assert not front['rows']
  if task!='wait_no_package':assert 'front_initial_center_landing' not in plan
 files=[ep/'front_initial_center.json',S/'CHECK.json',case/'provenance.json'"""
edit(a,b)
B.write_text(s);(W/'FRONT_INITIAL_CENTER_SOURCE_BINDING_PREPARATION.json').write_text(json.dumps(dict(parent=str(A),parent_sha256=sha(A),source_binding=str(B),source_binding_sha256=sha(B),edits=edits,scope='Original source, full horizon, all24substeps and pressure requirements retained. New collector/coordination/helper sources and declared front metadata additionally required. Not yet exercised on physical run.',training_ready=False),indent=2))
