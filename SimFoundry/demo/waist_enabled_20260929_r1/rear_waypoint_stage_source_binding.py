"""Bind the isolated midpoint collector to all 71 archived sources and original observations.
No report here proves physical task success or training admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_waypoint_reconciliation';sys.path[:0]=[str(W),str(ROOT)]
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REPORTS=['COLLECTOR_WIRING_CHECK_V2.json']

def verify_preparation():
 from front_drive_1mm_v2_stage_source_binding import verify_preparation as verify_parent
 old_sources,parent_bound=verify_parent()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_drive_1mm'
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];assert len(expected)==73 and set(expected)-set(old_sources)=={'reconcile_rear_waypoint.py','rear_post_commit_adapter.py'}
 assert set(old_sources)-set(expected)==set()
 for n,h in expected.items():assert sha(S/n)==h,n
 assert {n for n in old_sources if expected[n]!=old_sources[n]}=={'collect_paired_sorting.py'}
 restored=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['changes']):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for a,b in [('reconcile_rear_waypoint.py','reconcile_rear_waypoint.py'),('post_commit_adapter.py','rear_post_commit_adapter.py')]:assert sha(W/'rear_waypoint_reconciliation_draft_r1'/a)==expected[b]
 proofs=[S/'COLLECTOR_WIRING_CHECK_V2.json',W/'rear_waypoint_reconciliation_draft_r1/COMPLETE_COMMIT_LOG_CHECK.json',W/'rear_waypoint_reconciliation_draft_r1/INDEPENDENT_POST_COMMIT_REPLAY_CHECK.json']
 for p in proofs:
  check=json.loads(p.read_text());assert check['passed']
  for name,h in check['source_sha256'].items():assert sha(name)==h,name
  parent_bound[str(p)]=sha(p)
 parent_bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,parent_bound

def verify_trial_provenance(case):
 case=Path(case).resolve();expected,_=verify_preparation()
 prov=json.loads((case/'provenance.json').read_text());args=prov['args']
 assert args['front_corridor_midpoint_replan'] is True
 assert args['rear_waypoint_reconciliation'] is True and args['front_cop_drive_step_m']==.002
 assert args['front_loaded_z_priority'] is True and args['front_initial_center_landing'] is True
 assert args['terminal_release_margin'] is True and args['expert_top_confirmed_release'] is True and args['edge_clearance_intersection'] is True and args['role']=='diagnostic' and not args['waist_pilot_contract']
 settings=semantic_settings(args)
 for n in ['front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(n) is True
 assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['resolved_settings']
 prefix=str(S.relative_to(ROOT))+'/'
 assert {Path(n).name:h for n,h in prov['source_sha256'].items() if n.startswith(prefix)}==expected
 assert [n for n in prov['source_sha256'] if Path(n).name=='collect_paired_sorting.py']==[prefix+'collect_paired_sorting.py']
 for n,h in prov['source_sha256'].items():
  rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts
  assert sha(case/'source_snapshot'/rel)==h==sha(ROOT/rel)
 return prov,None,None

def _verify_original_observation_binding(ep):
    ep = Path(ep).resolve()
    case = ep.parent
    prov, _, _ = verify_trial_provenance(case)
    args = prov['args']
    sources = prov['source_sha256']
    with np.load(ep / 'raw.npz') as z:
        meta = json.loads(str(z['collect_meta']))
        task = str(z['task_id'])
        frames = len(z['q'])
    assert meta['front_initial_center_landing'] is True
    assert meta['front_initial_center_failure'] is None
    assert meta['terminal_release_margin'] is True and meta['terminal_release_zone_m'] == 0.205 and (meta['terminal_release_progress_m'] == 0.16)
    assert meta['collection_role'] == 'diagnostic' and meta['edge_clearance_intersection'] is True and (meta['assist_frames'] == 0) and (not meta['push_assist'])
    assert frames == args['wait_steps' if task == 'wait_no_package' else 'steps']
    runtime = json.loads((case / 'SUBSTEP_RUNTIME_BINDING.json').read_text())
    record = json.loads((ep / 'SUBSTEP_CONTACT_RECORDING.json').read_text())
    assert runtime['observer_installed'] and runtime['original_graph_setting']
    assert runtime['training_ready'] is False and record['training_ready'] is False
    assert record['metadata'] == runtime['metadata']
    m = runtime['metadata']
    assert m['fixture_cpu'] is False and m['expected_substeps'] == 24 and (m['control_decimation'] == 8) and (m['substeps_per_physics_tick'] == 3) and (abs(m['solver_dt_s'] - 1 / 360) < 1e-12)
    assert m['expected_manager_steps'] == (1 if m['all_graphable'] else 8) and len(m['geom_to_shape']) == 1
    helpers = {'substep_contact_observer_prototype.py', 'substep_contact_runtime_bridge.py', 'substep_contact_recording.py', 'substep_contact_setup.py'}
    assert {Path(k).name for k in runtime['source_files']} == helpers | {'newton_manager.py', 'mjwarp_manager.py', 'solver_mujoco.py', 'support.py'}
    for path, row in runtime['source_files'].items():
        assert sha(path) == row['sha256'] == sha(case / row['snapshot'])
        if Path(path).name in helpers:
            assert Path(path).parent == S and row['sha256'] == sources[str(Path(path).relative_to(ROOT))]
    with np.load(case / 'runtime_collision_arrays.npz') as z:
        assert np.array_equal(z['shape_body'], m['shape_body'])
    assert record['recording_sha256'] == sha(ep / 'substep_contacts.npz')
    assert meta['peak_load_bias_guard'] is True
    pressure = json.loads((ep / 'peak_load_updates.json').read_text())
    assert pressure['training_ready'] is False and pressure['executed_action_count'] == frames and (pressure['wait'] == (task == 'wait_no_package'))
    if task == 'wait_no_package':
        assert not pressure['rows'] and (not pressure['final_control_states'])
    else:
        plan = json.loads((ep / 'frontal_bypass.json').read_text())['plan']
        expected = dict(enabled=True, previous_action_substeps=24, peak_threshold_multiplier=2.0, negative_increment_only=True, original_filter_and_upward_relief=True, original_guard_priority=True, training_ready=False)
        assert plan['peak_load_bias_guard'] == meta['frontal_bypass_plan']['peak_load_bias_guard'] == expected
        assert plan['top_recontact']['desired_vertical_load_n'] == 5.0
        assert plan['confirmed_release_margin'] == meta['frontal_bypass_plan']['confirmed_release_margin'] == dict(enabled=True, zone_m=0.205, minimum_progress_m=0.16, original_confirmation_window=10, original_window_xy_m=0.01, quality_thresholds_unchanged=True)
    front = json.loads((ep / 'front_initial_center.json').read_text())
    assert front['training_ready'] is False
    selected = False if task == 'wait_no_package' else bool(plan.get('front_route_selected'))
    assert front['selected'] is selected
    if selected:
        declaration = plan['front_initial_center_landing']
        assert declaration == meta['frontal_bypass_plan']['front_initial_center_landing']
        assert declaration['enabled'] is True and declaration['maximum_ticks'] == 240 and (declaration['actual_ready_frames'] == 3)
        assert declaration['center_xy_m'] == 0.002 and declaration['precontact_height_m'] == [0.006, 0.007] and (declaration['measured_height_m'] == [0.004, 0.01])
        assert declaration['alignment_abs_min'] == 0.8 and declaration['numerical_tolerance'] == 2e-07 and (declaration['causal_preflight_only'] is True)
        assert declaration['no_plan_behavior'] == 'original_parent_before_any_override' and declaration['parameter_sha256'] == sha(S / 'causal_response_parameters.json')
        assert declaration['actual_core'] == plan['front_cop_slip_following']['edge_speed']['actual_core']
        assert front['rows'] and all((r['kind'] != 'stop' for r in front['rows']))
    else:
        assert not front['rows']
        if task != 'wait_no_package':
            assert 'front_initial_center_landing' not in plan
    files = [ep / 'front_initial_center.json', S / 'COLLECTOR_WIRING_CHECK_V2.json', case / 'provenance.json', case / 'SUBSTEP_RUNTIME_BINDING.json', ep / 'SUBSTEP_CONTACT_RECORDING.json', ep / 'substep_contacts.npz', ep / 'peak_load_updates.json', ep / 'raw.npz', S / 'COLLECTOR_PREPARATION.json', Path(__file__)]
    return dict(passed=True, diagnostic_only=True, source_sha256={str(p): sha(p) for p in files}, training_ready=False)

def verify_observation_binding(ep):
 ep=Path(ep).resolve();original=_verify_original_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:meta=json.loads(str(z['collect_meta']));frames=len(z['q']);wait=str(z['task_id'])=='wait_no_package'
 log=json.loads((ep/'front_loaded_z_priority.json').read_text())
 assert meta['front_loaded_z_priority'] is True and log['training_ready'] is False
 assert [r['step'] for r in log['rows']]==list(range(frames))
 assert all(type(r['applied']) is bool for r in log['rows'])
 assert meta['front_loaded_z_priority_applied_frames']==sum(r['applied'] for r in log['rows'])
 assert meta['front_corridor_midpoint_replan'] is True
 frontal_path=ep/'frontal_bypass.json'
 if wait:
  assert meta['front_corridor_midpoint_replanned_frames']==0
  if frontal_path.exists():
   frontal=json.loads(frontal_path.read_text());assert not frontal['rows'] and not frontal.get('plan',{}).get('front_corridor_midpoint')
 else:
  frontal=json.loads(frontal_path.read_text());plan=frontal['plan'];rows=frontal['rows']
  assert [r['step'] for r in rows]==list(range(1,frames))
  assert plan==meta['frontal_bypass_plan']
  selected=bool(plan.get('front_route_selected'))
  if selected:
   assert plan['front_corridor_midpoint']['enabled'] is True
   assert all(type(r['front_corridor_midpoint']['changed']) is bool for r in rows)
  else:
   assert 'front_corridor_midpoint' not in plan and all('front_corridor_midpoint' not in r for r in rows)
  assert meta['front_corridor_midpoint_replanned_frames']==sum(r.get('front_corridor_midpoint',{}).get('changed',False) for r in rows)
  original['source_sha256'][str(frontal_path)]=sha(frontal_path)
 for p in [ep/'front_loaded_z_priority.json',S/'COLLECTOR_PREPARATION.json',*[S/n for n in REPORTS],Path(__file__)]:original['source_sha256'][str(p)]=sha(p)
 return original
