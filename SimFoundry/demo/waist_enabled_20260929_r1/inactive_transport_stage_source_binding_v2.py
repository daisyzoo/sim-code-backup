"""Bind the isolated midpoint collector to all 81 archived sources and original observations.
No report here proves physical task success or training admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_inactive_transport_v2';sys.path[:0]=[str(W),str(ROOT)]
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REPORTS=[]

def verify_preparation():
 from front_box_recenter_stage_source_binding import verify_preparation as verify_parent
 old,bound=verify_parent();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_box_recenter_v3'
 assert sha(parent/'COLLECTOR_PREPARATION.json')==prep['parent_manifest_sha256']
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];helpers={'inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py'};geometry={'audit_front_recontact_center_events.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py'}
 assert len(expected)==88 and set(expected)==set(old)|helpers|geometry
 assert {n for n in old if expected[n]!=old[n]}==set(prep['changed_parent_files'])=={'collect_paired_sorting.py'}
 assert set(prep['edits'])==set(prep['changed_parent_files'])
 for n,h in expected.items():assert sha(S/n)==h,n
 for n,changes in prep['edits'].items():
  restored=(S/n).read_text()
  for e in reversed(changes):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(parent/n).read_text()
 for n in helpers:assert sha(S/n)==sha(W/'inactive_transport_clearance_bilateral_draft_r1'/n)
 for n in geometry:assert sha(S/n)==sha(W/n)
 for n in ['PARSER_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json']:
  proof=json.loads((S/n).read_text());assert proof['passed']
  for p,h in proof['source_sha256'].items():assert sha(p)==h,p
  bound[str(S/n)]=sha(S/n)
 bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,bound

def verify_settings(args):
 from front_box_recenter_stage_source_binding import verify_settings as verify_parent
 assert args['inactive_transport_clearance'] is True
 args=dict(args);args.pop('inactive_transport_clearance')
 return verify_parent(args)

def verify_trial_provenance(case):
 case=Path(case).resolve();expected,_=verify_preparation()
 prov=json.loads((case/'provenance.json').read_text());args=prov['args']
 verify_settings(args)
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
    files = [ep / 'front_initial_center.json', W / 'staged_front_recontact_center/PARSER_DISPATCH_CHECK.json', case / 'provenance.json', case / 'SUBSTEP_RUNTIME_BINDING.json', ep / 'SUBSTEP_CONTACT_RECORDING.json', ep / 'substep_contacts.npz', ep / 'peak_load_updates.json', ep / 'raw.npz', S / 'COLLECTOR_PREPARATION.json', Path(__file__)]
    return dict(passed=True, diagnostic_only=True, source_sha256={str(p): sha(p) for p in files}, training_ready=False)

def _verify_midpoint_observation_binding(ep):
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


def _verify_parent_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_midpoint_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:meta=json.loads(str(z['collect_meta']));frames=len(z['q']);task=str(z['task_id'])
 assert meta['front_recontact_center_landing'] is True and meta['front_recontact_center_failure'] is None
 spec=json.loads((W/'staged_front_box_recenter_v3/COLLECTOR_PREPARATION.json').read_text())['box_recenter'];assert meta['front_box_recenter']==spec
 assert meta['front_recontact_planning_headroom']=={'version': 'front_recontact_headroom_v1', 'entry_inactive_height_m': 0.841, 'nominal_predicted_inactive_height_m': 0.8405, 'original_measured_inactive_height_m': 0.84, 'original_numerical_tolerance_m': 2e-07, 'waiting_consumes_no_attempt': True}
 data=json.loads((ep/'front_recontact_center.json').read_text());assert data['training_ready'] is False
 plan={} if task=='wait_no_package' else json.loads((ep/'frontal_bypass.json').read_text())['plan']
 selected=bool(task in ('nudge_mailer_to_bin','push_box_to_bin') and plan.get('front_route_selected'));assert data['selected'] is selected
 assert meta['front_recontact_center_handovers']==sum(r['kind']=='handover' for r in data['rows'])
 if selected:
  assert [r['step'] for r in data['rows']]==list(range(1,frames)) and not any(r['kind']=='stop' for r in data['rows'])
  expected=dict(enabled=True,side='left',real_positive_recontact_counter=True,maximum_ticks=240,actual_ready_frames=3,center_xy_m=.002,precontact_height_m=[.006,.007],measured_height_m=[.004,.010],alignment_abs_min=.8,numerical_tolerance=2e-7,wait_for_original_unloaded_geometry=True,original_guard_priority=True,predicted_capture_discarded=True,training_ready=False,planning_headroom={'version': 'front_recontact_headroom_v1', 'entry_inactive_height_m': 0.841, 'nominal_predicted_inactive_height_m': 0.8405, 'original_measured_inactive_height_m': 0.84, 'original_numerical_tolerance_m': 2e-07, 'waiting_consumes_no_attempt': True})
  if task=='nudge_mailer_to_bin':
   assert plan['front_recontact_center_landing']==expected and 'front_box_recenter' not in plan
   assert all('front_box_recenter_version' not in r for r in data['rows'])
  else:
   assert plan['front_box_recenter']==spec and 'front_recontact_center_landing' not in plan
   assert all(r.get('front_box_recenter_version')=='front_box_recenter_v1' for r in data['rows'])
 else:assert not data['rows'] and 'front_recontact_center_landing' not in plan and 'front_inactive_clearance' not in plan
 result['source_sha256'][str(ep/'front_recontact_center.json')]=sha(ep/'front_recontact_center.json')
 return result


def verify_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_parent_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  meta=json.loads(str(z['collect_meta']));q=z['q'][:,12:23];u=z['action'][:,12:23]
 data=json.loads((ep/'inactive_transport_clearance.json').read_text());spec=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['spec']
 assert meta['inactive_transport_clearance']==data['spec']==spec and data['training_ready'] is False
 rows=data['rows'];assert [r['step'] for r in rows]==list(range(len(q)))
 assert all(type(r['step']) is int and type(r['applied']) is bool and r['training_ready'] is False and r['version']==spec['version'] for r in rows)
 assert meta['inactive_transport_applied_frames']==sum(r['applied'] for r in rows)
 for t,r in enumerate(rows):
  assert np.array_equal(r['output_command'],u[t])
  assert np.array_equal(r['collector_context']['current'],q[t])
  if t==0:assert r['collector_context']['previous_q'] is None and np.array_equal(q[t],np.zeros(11)) and np.array_equal(u[t],np.zeros(11))
  else:
   assert np.array_equal(r['collector_context']['previous_q'],q[t-1])
   assert np.array_equal(r['collector_context']['previous_command'],u[t-1])
 result['source_sha256'][str(ep/'inactive_transport_clearance.json')]=sha(ep/'inactive_transport_clearance.json')
 result['source_sha256'][str(Path(__file__))]=sha(Path(__file__))
 result['transport_full_command_stream_audit_required']=True
 return result
