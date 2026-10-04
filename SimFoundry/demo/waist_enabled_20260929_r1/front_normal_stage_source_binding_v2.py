"""Bind normal-planning v3 to101active sources and explicitly separate final actions.
No report here proves physical task success or training admission.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_normal_nondegradation_v3';sys.path[:0]=[str(W),str(ROOT)]
from simfoundry.data.waist_pilot_protocol import semantic_settings
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REPORTS=[]

QUARTER_HELPER='front_loaded_z_fraction.py'
QUARTER_META=dict(version='front_loaded_z_quarter_v1',fraction=.25,z_target='parent_linear_achieved_to_original_requested',original_task_retained=True,training_ready=False)

EFFECTIVE_HELPERS=['effective_loaded_contact_task_v1.py','joint_transport_effective_height_solver_v1.py','joint_transport_effective_height_certificate_v1.py','joint_transport_effective_height_runtime_v1.py']

NORMAL_HELPERS=['front_normal_nondegradation_runtime_candidate_v1.py','front_normal_nondegradation_solver_candidate_v1.py','audit_front_exact_normal_planning_v1.py','independent_cross_track_assets_v1.py','audit_unloaded_wrist_prior_live.py']
NORMAL_META=dict(version='front_normal_nondegradation_v1',planning_policy='exact_normal_parent_to_zero_and_original_forecast_nondegradation_v1',measured_hold_then_original_recovery=True,mode='top_push',route_stage='lateral_y',stationarity_max=1e-6,rounding_tolerance_m=2e-7,failed_refinement_stops_before_emission=True,training_ready=False)

def verify_preparation():
 import ast,copy
 from front_effective_height_stage_source_binding_v1 import verify_preparation as parent_preparation
 parent_used,bound=parent_preparation()
 for path in [W/'front_normal_preparation_r2/STAGE_PREPARATION.json',W/'front_normal_preparation_r3/STAGE_PREPARATION.json']:
  p=json.loads(path.read_text());assert p['defaultoff_exact_parent_ast'] is True and p['independent_inodes'] is True
  for key in ['parent_sources_sha256','stage_sources_sha256']:
   for name,h in p[key].items():assert sha(name)==h,name
  bound[str(path)]=sha(path)
 class Strip(ast.NodeTransformer):
  def visit_If(self,n):
   if 'args.front_normal_nondegradation' in ast.unparse(n.test):return None
   return self.generic_visit(n)
  def visit_Expr(self,n):
   if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='parser.add_argument' and n.value.args and isinstance(n.value.args[0],ast.Constant) and n.value.args[0].value=='--front-normal-nondegradation':return None
   return self.generic_visit(n)
 tree=ast.parse((S/'collect_paired_sorting.py').read_text());parent=W/'staged_front_effective_height_v1'
 assert ast.dump(Strip().visit(copy.deepcopy(tree)),include_attributes=False)==ast.dump(ast.parse((parent/'collect_paired_sorting.py').read_text()),include_attributes=False)
 for n,h in parent_used.items():
  if n!='collect_paired_sorting.py':assert sha(S/n)==h,n
 for n in NORMAL_HELPERS:assert sha(S/n)==sha(W/n),n
 used={n:sha(S/n) for n in [*parent_used,*NORMAL_HELPERS]};assert len(used)==101
 bound[str(Path(__file__))]=sha(__file__)
 return used,bound

def verify_settings(args):
 from front_effective_height_stage_source_binding_v1 import verify_settings as parent_settings
 args=dict(args);enabled=args.pop('front_normal_nondegradation');assert type(enabled) is bool
 if enabled:
  assert args['role']=='diagnostic'
  assert all(args.get(k) is True for k in ['joint_transport_clearance','joint_transport_effective_quarter_height','front_loaded_z_quarter','self_clearance_task_ik','front_cop_route_axis','peak_load_bias_guard'])
  assert not any(args.get(k) for k in ['policy_port','idle','waist_probe','waist_pilot_contract'])
 return parent_settings(args)

def verify_trial_provenance(case):
 case=Path(case).resolve();expected,_=verify_preparation()
 prov=json.loads((case/'provenance.json').read_text());args=prov['args']
 verify_settings(args)
 if not args['front_normal_nondegradation']:expected={k:v for k,v in expected.items() if k not in set(NORMAL_HELPERS)-{'audit_unloaded_wrist_prior_live.py'}}
 if not args['front_loaded_z_quarter']:expected={k:v for k,v in expected.items() if k!=QUARTER_HELPER}
 if not args['joint_transport_effective_quarter_height']:expected={k:v for k,v in expected.items() if k not in EFFECTIVE_HELPERS}
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


def verify_observation_binding(ep):
 ep=Path(ep).resolve();args=json.loads((ep.parent/'provenance.json').read_text())['args'];enabled=args['front_normal_nondegradation'];assert type(enabled) is bool
 with np.load(ep/'raw.npz',allow_pickle=False) as z:meta=json.loads(str(z['collect_meta']));normal_u=z['action'][:,12:23].astype(float);normal_n=len(z['q']);normal_wait=str(z['task_id'])=='wait_no_package'
 normal=None
 if enabled:
  assert meta['front_normal_nondegradation']==NORMAL_META
  assert all(type(meta['front_normal_nondegradation'][k]) is type(v) for k,v in NORMAL_META.items())
  data=json.loads((ep/'front_normal_nondegradation.json').read_text());assert data['training_ready'] is False
  normal=data['rows'];assert [r['step'] for r in normal]==list(range(normal_n))
  coords={} if normal_wait else {c['step']:c for c in json.loads((ep/'coordination.json').read_text())}
  for t,r in enumerate(normal):
   assert type(r['step']) is int and r['enabled'] is True and r['requires_stop'] is False and r['training_ready'] is False
   for k in ['selected','applied','requires_recovery']:assert type(r[k]) is bool
   output=np.asarray(r['output_command'],float);parent=np.asarray(r['parent_command'],float)
   assert output.shape==parent.shape==(11,) and np.isfinite(output).all() and np.isfinite(parent).all()
   assert np.array_equal(output,normal_u[t])
   if t in coords:assert coords[t]['front_normal_nondegradation']==r
   if r['requires_recovery']:assert r['recovery_committed'] is True and r['applied'] is True
   else:assert 'recovery_committed' not in r and 'recovery_transition' not in r
  assert type(meta['front_normal_planning_applied_frames']) is int and meta['front_normal_planning_applied_frames']==sum(r['applied'] for r in normal)
 else:
  assert 'front_normal_nondegradation' not in meta and 'front_normal_planning_applied_frames' not in meta
  assert not (ep/'front_normal_nondegradation.json').exists()
 ep=Path(ep).resolve();result=_verify_parent_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  meta=json.loads(str(z['collect_meta']));q=z['q'][:,12:23];u=z['action'][:,12:23]
 data=json.loads((ep/'joint_transport_clearance.json').read_text());spec=json.loads((W/'joint_transport_reserve_preparation_r1/RUNTIME_CONTEXT_CHECK.json').read_text())['spec']
 quarter_enabled=json.loads((ep.parent/'provenance.json').read_text())['args']['joint_transport_effective_quarter_height'];assert type(quarter_enabled) is bool
 if quarter_enabled:
  spec=dict(spec,version='joint_transport_clearance_effective_quarter_v1',effective_quarter_height=True,contact_height_target='verified_effective_quarter_task',original_full_task_objective=True,original_height_tolerance_m=2e-7)
  assert meta['joint_transport_effective_quarter_height'] is True
 else:assert 'joint_transport_effective_quarter_height' not in meta
 assert meta['joint_transport_clearance']==data['spec']==spec and data['training_ready'] is False
 rows=data['rows'];assert [r['step'] for r in rows]==list(range(len(q)))
 assert all(type(r['step']) is int and type(r['applied']) is bool and r['training_ready'] is False and r['version']==spec['version'] for r in rows)
 assert meta['joint_transport_applied_frames']==sum(r['applied'] for r in rows)
 if quarter_enabled:assert all(r['effective_quarter_height'] is True for r in rows)
 else:assert all('effective_quarter_height' not in r for r in rows)
 for t,r in enumerate(rows):
  expected_parent=normal[t]['parent_command'] if enabled else u[t]
  assert np.array_equal(r['output_command'],expected_parent)
  assert np.array_equal(r['collector_context']['current'],q[t])
  if t==0:assert r['collector_context']['previous_q'] is None and np.array_equal(q[t],np.zeros(11)) and np.array_equal(u[t],np.zeros(11))
  else:
   assert np.array_equal(r['collector_context']['previous_q'],q[t-1])
   assert np.array_equal(r['collector_context']['previous_command'],u[t-1])
 result['source_sha256'][str(ep/'joint_transport_clearance.json')]=sha(ep/'joint_transport_clearance.json')
 result['source_sha256'][str(Path(__file__))]=sha(Path(__file__))
 if enabled:result['source_sha256'][str(ep/'front_normal_nondegradation.json')]=sha(ep/'front_normal_nondegradation.json')
 result['transport_full_command_stream_audit_required']=True
 result['normal_final_command_and_pressure_audits_required']=enabled
 return result
