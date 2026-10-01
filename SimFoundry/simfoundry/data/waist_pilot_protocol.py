"""Explicit admission for a fresh waist-enabled pilot; no diagnostic promotion.

Prepared independently of the collector. A contract cannot activate collection
until the collector and converter explicitly call this validator.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from simfoundry.data.diverse_layouts import validate_diagnostic_layout
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
from simfoundry.data.paired_sorting import audit_rollout
from simfoundry.data.search_reward import terminal_search_scores
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS

PROTOCOL = 'waist_yaw_enabled_v1'
TASKS = {'push_box_to_bin', 'nudge_mailer_to_bin'}
# Scheduling/admission switches do not change controller kinematics. Everything
# else in argparse/provenance, including source seed/budgets/camera, stays exact.
SCHEDULING_KEYS = {'out_dir', 'role', 'layout_start', 'layouts', 'wait_layout_start',
    'wait_episodes', 'diagnostic_layout_json', 'waist_pilot_contract',
    'extended_waist_diagnostic'}
REQUIRED_SOURCES = {'simfoundry/calibration/sorting_station.py', 'simfoundry/robots/g1_assets.py',
    'simfoundry/data/waist_coordination.py', 'simfoundry/data/bounded_ik.py',
    'simfoundry/data/top_contact_bypass.py', 'simfoundry/data/frontal_bypass.py',
    'simfoundry/data/sorting_cartesian_expert.py', 'simfoundry/data/paired_sorting.py',
    'simfoundry/scene_bridge/isaac_cfg.py', 'scenes/sorting_station_g1_23/twin/layout.json',
    'simfoundry/data/front_top_route.py', 'simfoundry/data/front_clearance_progress.py',
    'simfoundry/data/tabletop_route_candidates.py', 'simfoundry/data/projected_support_reference.py',
    'assets/robots/g1_hand_support_vertices.json', 'simfoundry/data/object_relative_push.py',
    'simfoundry/data/confirmed_position_release.py', 'simfoundry/data/initial_top_route.py',
    'simfoundry/data/initial_top_route_candidate.py', 'simfoundry/data/terminal_joint_hold.py', 'simfoundry/data/contact_normal_constraint.py', 'simfoundry/data/contact_center_calibration.py', 'simfoundry/data/bounded_top_lead.py'}
GATES = dict(zero_first_state=True, zero_first_action=True, assist_frames=0,
             non_target_max_xy_m=.015, max_action_step_rad=.08, policy_horizon=10)


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def semantic_settings(settings):
    # JSON canonicalization also normalizes Paths before exact comparison.
    return json.loads(json.dumps({k:v for k,v in settings.items()
                                  if k not in SCHEDULING_KEYS}, default=str))


def _bound_json(root, name, expected):
    path = root/name
    if file_sha256(path) != expected:
        raise ValueError(f'Changed waist evidence: {path}')
    return json.loads(path.read_text())


def validate_manifest(c):
    if (type(c.get('version')) is not int or c['version'] not in (1,2) or c.get('motion_protocol') != PROTOCOL
            or c.get('approved_for_pilot') is not True or c.get('gates') != GATES):
        raise ValueError('Unapproved waist contract or changed original gates')
    settings = c.get('collector_settings', {})
    if semantic_settings(settings) != settings:
        raise ValueError('Contract mixes scheduling fields with controller settings')
    if (settings.get('motion_protocol') != PROTOCOL
            or settings.get('policy_port') != 0 or settings.get('idle') is not False
            or settings.get('waist_probe') is not False
            or settings.get('newton_contacts') is not True
            or settings.get('wait_force_n') != 0 or settings.get('push_force_n') != 0
            or settings.get('waist_coordinated_expert') is not True
            or settings.get('bounded_coupled_ik') is not True):
        raise ValueError('Unregistered waist expert/physics/assistance settings')
    for key, minimum in (('steps', 120), ('wait_steps', 50)):
        if type(settings.get(key)) is not int or settings[key] < minimum:
            raise ValueError('Invalid recorded frame budget')
    if (not np.isfinite([settings.get('waist_limit_rad', float('nan')),
                        settings.get('waist_wait_tolerance_rad', float('nan'))]).all()
            or not 0 < settings['waist_wait_tolerance_rad'] <= settings['waist_limit_rad'] <= 1.):
        raise ValueError('Invalid explicitly reviewed waist limits')
    if type(settings.get('environment_seed')) is not int or not 0 <= settings['environment_seed'] < 2**31:
        raise ValueError('Fresh waist pilot requires explicit environment seed')
    layouts = c.get('layouts', [])
    groups = validate_complete_swap_layouts(layouts)
    for d in layouts:
        validate_diagnostic_layout(d, d['layout_id'])
        if d['planned_split'] not in ('train', 'validation'):
            raise ValueError('Fresh pilot layouts must preassign train/validation')
    ids = {d['layout_id'] for d in layouts}
    waits = c.get('wait_layouts', [])
    if not waits:
        raise ValueError('Fresh shared pilot must explicitly include waits')
    for d in waits:
        if (type(d.get('layout_id')) is not int or d['layout_id'] in ids
                or d.get('planned_split') not in ('train', 'validation')):
            raise ValueError('Duplicate or unassigned waiting layout')
        validate_diagnostic_layout(d, d['layout_id'])
        ids.add(d['layout_id'])
    if (c['version']==1 and not c.get('feasibility')) or not REQUIRED_SOURCES <= set(c.get('controller_source_sha256', {})):
        raise ValueError('Missing physical evidence or controller source bindings')
    for path, digest in c['controller_source_sha256'].items():
        if Path(path).is_absolute() or '..' in Path(path).parts or len(digest) != 64:
            raise ValueError('Invalid relative controller source binding')
    if len(c.get('pilot_collector_sha256', '')) != 64:
        raise ValueError('Missing exact fresh collector source binding')
    if c['version']==2:
        from simfoundry.data.waist_trial_collection import validate_trial_schedule
        validate_trial_schedule(c)
    return groups


def validate_feasibility(source, settings, controller_hashes, *, require_live_sources=True):
    root = Path(source['root'])
    ready = _bound_json(root, 'COMPLETE_GROUP_READINESS.json', source['readiness_sha256'])
    result = _bound_json(root, 'RESULT.json', source['result_sha256'])
    protocol = _bound_json(root, 'PROTOCOL.json', source['protocol_sha256'])
    if type(require_live_sources) is not bool:
        raise ValueError('Explicit boolean source-validation mode required')
    repo = Path(__file__).resolve().parents[2]
    cases = {Path(row['path']).parent for row in ready.get('rows', [])}
    for source_path, digest in protocol['source_sha256'].items():
        if Path(source_path).name == 'collect_paired_sorting.py':
            continue  # Exact historical collector snapshots checked below.
        if require_live_sources:
            if file_sha256(source_path) != digest:
                raise ValueError('Feasibility expert/asset source has changed')
        else:
            # Recorded data follows its exact saved source, not a later expert.
            # Assets never snapshotted still require matching current bytes.
            try:
                relative = Path(source_path).relative_to(repo)
            except ValueError as exc:
                raise ValueError('Feasibility source outside the recorded repository') from exc
            for case in cases:
                if not case.resolve().is_relative_to(root.resolve()):
                    raise ValueError('Feasibility snapshot outside the bound run')
                provenance = json.loads((case/'provenance.json').read_text())
                recorded = provenance['source_sha256'].get(str(relative))
                snapshot = case/'source_snapshot'/relative
                if recorded is not None:
                    if recorded != digest or file_sha256(snapshot) != digest:
                        raise ValueError('Archived feasibility source snapshot differs')
                elif file_sha256(source_path) != digest:
                    raise ValueError('Unsnapshotted feasibility asset/source has changed')
    if not ready.get('complete_group_feasibility_passed') or ready.get('errors'):
        raise ValueError('Incomplete or failed waist feasibility group')
    rows = ready.get('rows', [])
    if len(rows) < 4 or len(rows) % 4:
        raise ValueError('Incomplete waist feasibility task coverage')
    seen = set(); layouts = {}; reviewed = {r['episode']:r for r in result.get('rows', [])}
    if len(reviewed) != len(rows):
        raise ValueError('Actual visual review coverage differs from feasibility')
    for row in rows:
        ep = Path(row['path'])
        if not ep.resolve().is_relative_to(root.resolve()):
            raise ValueError('Feasibility trajectory outside the bound run')
        for name, key in [('raw.npz','raw_sha256'), ('trace.npz','trace_sha256'),
                          ('parcel_orientation.npz','orientation_sha256')]:
            if file_sha256(ep/name) != row[key]:
                raise ValueError('Changed feasibility trajectory/pose')
        review = reviewed.get(ep.name, {})
        if (review.get('raw_sha256') != row['raw_sha256']
                or not str(review.get('actual_sampled_visual_review','')).startswith('completed')
                or review.get('review_sheet_sha256') != file_sha256(ep/'REVIEW_EVEN.jpg')):
            raise ValueError('Missing or changed actual sampled visual evidence')
        provenance = json.loads((ep.parent/'provenance.json').read_text())
        collector_key = 'scripts/collect_paired_sorting.py'
        collector_sha = protocol['source_sha256'].get(str(Path(__file__).resolve().parents[2]/collector_key))
        if (not collector_sha or provenance['source_sha256'].get(collector_key) != collector_sha
                or file_sha256(ep.parent/'source_snapshot'/collector_key) != collector_sha):
            raise ValueError('Frozen feasibility collector snapshot changed')
        if semantic_settings(provenance['args']) != settings:
            raise ValueError('Expert settings differ from successful feasibility')
        for relative, digest in controller_hashes.items():
            # The frozen collector snapshot is verified separately; these are
            # physics/controller dependencies that must not silently change.
            if (provenance['source_sha256'].get(relative) != digest
                    or file_sha256(ep.parent/'source_snapshot'/relative) != digest):
                raise ValueError('Feasibility controller snapshot differs')
        with np.load(ep/'raw.npz') as raw, np.load(ep/'trace.npz') as tr, np.load(ep/'parcel_orientation.npz') as ori:
            meta = json.loads(str(raw['collect_meta'])); task = str(raw['task_id'])
            if (task not in TASKS or str(raw['instruction']) != PAIRED_SORTING_PROMPTS[task]
                    or meta.get('assist_frames') != 0 or meta.get('push_assist') is not False
                    or meta.get('motion_protocol') != PROTOCOL):
                raise ValueError('Feasibility task/protocol/assistance mismatch')
            layout = meta['layout']; key = (layout['layout_id'], task)
            if key in seen:raise ValueError('Duplicate feasibility task')
            seen.add(key);layouts[layout['layout_id']] = layout
            report = audit_rollout(task, raw['q'], raw['action'], dict(tr),
                motion_protocol=PROTOCOL, waist_limit_rad=settings['waist_limit_rad'],
                waist_wait_tolerance_rad=settings['waist_wait_tolerance_rad'])
            _, fit = terminal_search_scores([report], [0 if task=='push_box_to_bin' else 1],
                {k:tr[k][:,None] for k in tr.files}, {k:ori[k][:,None] for k in ori.files})
            if (len(raw['q']) != settings['steps'] or not report['passed']
                    or not fit[0]['search_success']):
                raise ValueError('Recomputed feasibility task/pose gate failed')
    validate_complete_swap_layouts(list(layouts.values()))
    if seen != {(identifier, task) for identifier in layouts for task in TASKS}:
        raise ValueError('Missing task within feasibility swap')
    declared = set(protocol.get('layout_ids', [protocol.get('layout_id')]))
    if declared != set(layouts):raise ValueError('Feasibility coverage differs from frozen protocol')
    return set(layouts)


def validate_waist_contract(path, *, settings=None, layout_id=None, require_live_sources=True):
    path = Path(path); c = json.loads(path.read_text()); validate_manifest(c)
    if settings is not None and semantic_settings(settings) != c['collector_settings']:
        raise ValueError('Fresh collector settings differ from waist contract')
    if c['version']==2:
        from simfoundry.data.waist_trial_collection import validate_trial_schedule, validate_trial_sources
        ids=validate_trial_schedule(c)
        validate_trial_sources(c,Path(__file__).resolve().parents[2],require_live_sources=require_live_sources)
        if layout_id is not None and layout_id not in ids:
            raise ValueError('Layout outside frozen trial contract')
        return c, file_sha256(path)
    diagnostic_ids = set()
    for source in c['feasibility']:
        diagnostic_ids.update(validate_feasibility(source, c['collector_settings'], c['controller_source_sha256'], require_live_sources=require_live_sources))
    all_layouts = c['layouts'] + c['wait_layouts']
    if diagnostic_ids & {d['layout_id'] for d in all_layouts}:
        raise ValueError('Fresh pilot cannot reuse diagnostic layout IDs')
    if layout_id is not None and sum(d['layout_id']==layout_id for d in all_layouts) != 1:
        raise ValueError('Layout is not registered in fresh waist contract')
    return c, file_sha256(path)
