"""Bind isolated front contact-window sources and original observation streams.
Window structural binding is not independent full-stream decision auditing.
No report here proves physical task success or training admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(W),str(ROOT)]
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REPORTS=[]

QUARTER_HELPER='front_loaded_z_fraction.py'
QUARTER_META=dict(version='front_loaded_z_quarter_v1',fraction=.25,z_target='parent_linear_achieved_to_original_requested',original_task_retained=True,training_ready=False)

WINDOW_HELPERS=['front_window_native_v4.py','contact_window_evidence_v2.py','window_initial_center_top_v2.py','window_initial_center_route_v2.py','window_initial_center_cop_v2.py']
WINDOW_PLAN=dict(version='front_window_native_v4',enabled=True,selected_front=True,observable='original_absolute_vertical_hand_target_force',solver_ticks=24,loss_threshold_n=.2,minimum_contact_ticks=12,minimum_current_core_margin_m=.010,geometry='current_measured_hand_pose_actual_collision_support_vertex',current_force_and_cop_unchanged=True,original_guard_priority=True,training_ready=False)

def verify_preparation():
 from front_loaded_z_quarter_stage_source_binding_v1 import verify_preparation as parent_verify
 parent_used,bound=parent_verify();D=W/'front_contact_window_preparation_r2';C=W/'front_contact_window_candidate_v1'
 prep=json.loads((D/'STAGE_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_loaded_z_quarter_v1' and Path(prep['stage'])==S
 assert prep['helpers']==WINDOW_HELPERS and len(prep['collector_edits'])==9
 for mapping in ['source_sha256','candidate_sha256']:
  for p,h in prep[mapping].items():assert sha(p)==h,p
 restored=(S/'collect_paired_sorting.py').read_text()
 for edit in reversed(prep['collector_edits']):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'])
 assert restored==(parent/'collect_paired_sorting.py').read_text()
 for name in parent_used:
  if name!='collect_paired_sorting.py':assert sha(S/name)==sha(parent/name)
 for name in WINDOW_HELPERS:assert sha(S/name)==sha(C/name)
 used={name:sha(S/name) for name in [*parent_used,*WINDOW_HELPERS]};assert len(used)==98
 checks=[D/'COLLECTOR_WIRING_CHECK.json',D/'NATIVE_LOADED_BOUT_CHECK_V4.json',D/'CHANGED_JOINT_CHAIN_CHECK_V1.json',D/'INDEPENDENT_LOADED_RECORD_AUDIT_V2.json']
 for p in checks:
  r=json.loads(p.read_text());assert r['passed'] and r['training_ready'] is False
  for f,h in r['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 for p in [C/'NATIVE_FAMILY_DERIVATION_V2.json',C/'NATIVE_SCALAR_BINDING_FIX_V4.json']:
  for f,h in json.loads(p.read_text())['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 for p in [D/'STAGE_PREPARATION.json',Path(__file__)]:bound[str(p)]=sha(p)
 return used,bound

def verify_settings(args):
 from front_loaded_z_quarter_stage_source_binding_v1 import verify_settings as parent_verify
 args=dict(args);enabled=args.pop('front_contact_window');assert type(enabled) is bool
 if enabled:
  assert all(args[k] is True for k in ['front_loaded_z_quarter','front_initial_center_landing','peak_load_bias_guard','trace_substep_contacts'])
  assert args['expert_frontal_top_support_hysteresis_m']==0 and args['role']=='diagnostic'
  assert not any(args.get(k) for k in ['policy_port','idle','waist_probe','waist_pilot_contract'])
 return parent_verify(args)

def verify_trial_provenance(case):
 case=Path(case).resolve();expected,_=verify_preparation();prov=json.loads((case/'provenance.json').read_text());args=prov['args'];verify_settings(args)
 if not args['front_loaded_z_quarter']:expected.pop(QUARTER_HELPER)
 if not args['front_contact_window']:
  for name in WINDOW_HELPERS:expected.pop(name)
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
 quarter=json.loads((ep.parent/'provenance.json').read_text())['args']['front_loaded_z_quarter'];assert type(quarter) is bool
 if quarter:assert meta['front_loaded_z_quarter']==QUARTER_META
 else:assert 'front_loaded_z_quarter' not in meta and all('reduced_z_task' not in r for r in log['rows'])
 for r in log['rows']:
  if 'reduced_z_task' in r:assert quarter and r['reduced_z_task']['fraction']==.25
 assert meta['front_corridor_midpoint_replan'] is True
 args=json.loads((ep.parent/'provenance.json').read_text())['args'];lateral=args['front_corridor_lateral_replan'];assert type(lateral) is bool
 if lateral:
  assert meta['front_corridor_lateral_replan'] is True
  assert type(meta['front_corridor_lateral_replanned_frames']) is int
 else:assert 'front_corridor_lateral_replan' not in meta and 'front_corridor_lateral_replanned_frames' not in meta
 frontal_path=ep/'frontal_bypass.json'
 if wait:
  assert meta['front_corridor_midpoint_replanned_frames']==0
  if lateral:assert meta['front_corridor_lateral_replanned_frames']==0
  if frontal_path.exists():
   frontal=json.loads(frontal_path.read_text());assert not frontal['rows'] and not frontal.get('plan',{}).get('front_corridor_midpoint')
 else:
  frontal=json.loads(frontal_path.read_text());plan=frontal['plan'];rows=frontal['rows']
  assert [r['step'] for r in rows]==list(range(1,frames))
  assert plan==meta['frontal_bypass_plan']
  selected=bool(plan.get('front_route_selected'))
  if selected:
   assert plan['front_corridor_midpoint']['enabled'] is True
   assert plan['front_corridor_midpoint']['phase']==('front_x_and_lateral_y' if lateral else 'front_x_only')
   assert all(type(r['front_corridor_midpoint']['changed']) is bool for r in rows)
  else:
   assert 'front_corridor_midpoint' not in plan and all('front_corridor_midpoint' not in r for r in rows)
  assert meta['front_corridor_midpoint_replanned_frames']==sum(r.get('front_corridor_midpoint',{}).get('changed',False) for r in rows)
  if lateral:assert meta['front_corridor_lateral_replanned_frames']==sum(bool(r.get('front_corridor_midpoint',{}).get('changed')) and r['front_corridor_midpoint']['route_stage']=='lateral_y' for r in rows)
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


def _verify_original_transport_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_parent_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  meta=json.loads(str(z['collect_meta']));q=z['q'][:,12:23];u=z['action'][:,12:23]
 data=json.loads((ep/'joint_transport_clearance.json').read_text());spec=json.loads((W/'joint_transport_reserve_preparation_r1/RUNTIME_CONTEXT_CHECK.json').read_text())['spec']
 assert meta['joint_transport_clearance']==data['spec']==spec and data['training_ready'] is False
 rows=data['rows'];assert [r['step'] for r in rows]==list(range(len(q)))
 assert all(type(r['step']) is int and type(r['applied']) is bool and r['training_ready'] is False and r['version']==spec['version'] for r in rows)
 assert meta['joint_transport_applied_frames']==sum(r['applied'] for r in rows)
 for t,r in enumerate(rows):
  assert np.array_equal(r['output_command'],u[t])
  assert np.array_equal(r['collector_context']['current'],q[t])
  if t==0:assert r['collector_context']['previous_q'] is None and np.array_equal(q[t],np.zeros(11)) and np.array_equal(u[t],np.zeros(11))
  else:
   assert np.array_equal(r['collector_context']['previous_q'],q[t-1])
   assert np.array_equal(r['collector_context']['previous_command'],u[t-1])
 result['source_sha256'][str(ep/'joint_transport_clearance.json')]=sha(ep/'joint_transport_clearance.json')
 result['source_sha256'][str(Path(__file__))]=sha(Path(__file__))
 result['transport_full_command_stream_audit_required']=True
 return result


def verify_window_structure(*,enabled,task,frames,meta,plan,log):
 """Validate stream identity and completeness; no force/geometry truth claim."""
 assert type(enabled) is bool and type(frames) is int and frames>0
 selected=bool(task!='wait_no_package' and plan.get('front_route_selected'))
 if not enabled:
  assert log is None and 'front_contact_window' not in meta and 'front_contact_window' not in plan
  return dict(enabled=False,selected_front=False,intervals=0,independent_window_stream_audit_required=False)
 expected=dict(version='front_window_native_v4',enabled=True,selected_front=selected,recorded_intervals=frames-1 if selected else 0,training_ready=False)
 assert meta['front_contact_window']==expected
 assert log.keys()=={'version','enabled','selected_front','rows','executed_frames','training_ready'}
 assert log['version']==expected['version'] and log['enabled'] is True and log['selected_front'] is selected and log['training_ready'] is False and log['executed_frames']==frames
 if selected:assert plan['front_contact_window']==WINDOW_PLAN
 else:assert 'front_contact_window' not in plan
 rows=log['rows'];assert [r['step'] for r in rows]==(list(range(1,frames)) if selected else [])
 for r in rows:
  assert type(r['step']) is int and type(r['action_step']) is int and r['action_step']==r['step'] and r['training_ready'] is False
  assert all(type(r[k]) is str and r[k] for k in ['final_phase','output_mode'])
  assert (r['step']==1 and r['observed_phase'] is None) or (type(r['observed_phase']) is str and bool(r['observed_phase']))
  evidence=r['evidence']
  assert r['disposition']==('loss_counter_evaluated' if evidence is not None else 'original_guard_or_nonpush_no_loss_update')
  if evidence is not None:
   obs=evidence['observation'];assert evidence['enabled'] is True and evidence['selected_front'] is True and evidence['mode']=='top_push' and evidence['training_ready'] is False
   assert obs['action_step']==r['step'] and obs['after_action_step']==r['step']-1 and obs['solver_substeps']==24 and obs['training_ready'] is False
   assert evidence['current_force_preserved'] is True and evidence['current_cop_available_from_window'] is False
 return dict(enabled=enabled,selected_front=selected,intervals=len(rows),independent_window_stream_audit_required=selected)

def verify_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_original_transport_observation_binding(ep)
 args=json.loads((ep.parent/'provenance.json').read_text())['args']
 with np.load(ep/'raw.npz',allow_pickle=False) as z:meta=json.loads(str(z['collect_meta']));frames=len(z['q']);task=str(z['task_id'])
 plan={} if task=='wait_no_package' else json.loads((ep/'frontal_bypass.json').read_text())['plan'];p=ep/'front_contact_window.json';log=json.loads(p.read_text()) if p.exists() else None
 result['window_structure']=verify_window_structure(enabled=args['front_contact_window'],task=task,frames=frames,meta=meta,plan=plan,log=log)
 if p.exists():result['source_sha256'][str(p)]=sha(p)
 result['source_sha256'][str(Path(__file__))]=sha(__file__)
 result['window_full_native_stream_audit_required']=bool(args['front_contact_window'])
 return result
