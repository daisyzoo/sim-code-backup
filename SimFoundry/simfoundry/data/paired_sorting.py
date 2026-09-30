"""Pure, fail-closed quality checks for the paired-language sorting pilot."""
from __future__ import annotations

import numpy as np

from simfoundry.calibration.sorting_station import (
    TABLE_TOP_Z, TABLE_TOP_BOX_Z, TABLE_TOP_MAILER_Z, TABLE_FRONT_X,
)
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS


def sample_layout(layout_id: int, seed: int = 20260924) -> dict:
    rng = np.random.default_rng(np.random.SeedSequence([seed, layout_id]))
    # Conservative first-stage workspace. Both directions are unobstructed;
    # broader placement/permutations require a separate reachability pilot.
    return {
        "layout_id": layout_id,
        "seed": int(rng.integers(0, 2**31 - 1)),
        "box_xyz": [float(rng.uniform(.44, .47)), float(rng.uniform(-.15, -.125)), TABLE_TOP_BOX_Z],
        "mailer_xyz": [float(rng.uniform(.44, .47)), float(rng.uniform(.125, .15)), TABLE_TOP_MAILER_Z],
    }


def audit_rollout(task_id: str, q: np.ndarray, action: np.ndarray, trace: dict,
                  *, idle: bool = False, require_zero_action: bool = True,
                  motion_protocol: str = 'waist_locked_v1',
                  waist_limit_rad: float = .20, waist_wait_tolerance_rad: float = .01) -> dict:
    if motion_protocol not in ('waist_locked_v1', 'waist_yaw_enabled_v1'):
        raise ValueError('Unknown motion protocol')
    if not np.isfinite([waist_limit_rad, waist_wait_tolerance_rad]).all() or not 0 < waist_wait_tolerance_rad <= waist_limit_rad:
        raise ValueError('Invalid waist limits')
    reasons = []
    metrics = {'waist_max_abs_state_rad': float(np.abs(q[:, 12]).max()),
               'waist_max_abs_action_rad': float(np.abs(action[:, 12]).max())}
    if not np.isfinite(q).all() or not np.isfinite(action).all():
        reasons.append("non-finite state/action")
    if np.max(np.abs(q[0, 12:])) >= 1e-4:
        reasons.append("first-frame upper-body state is not zero")
    if require_zero_action and np.max(np.abs(action[0, 12:])) >= 1e-4:
        reasons.append("first-frame upper-body action is not zero")
    if motion_protocol == 'waist_locked_v1':
        if np.max(np.abs(action[:, 12])) >= 1e-6:
            reasons.append("waist action is not locked")
    else:
        if max(metrics.values()) > waist_limit_rad + 1e-6:
            reasons.append('waist working range exceeded')
        if idle or task_id == 'wait_no_package':
            if max(metrics.values()) > waist_wait_tolerance_rad:
                reasons.append('idle waist drift')
    if len(q) != len(action) or len(q) < (50 if idle or task_id == 'wait_no_package' else 120):
        reasons.append("short or misaligned episode")
    for key, values in trace.items():
        arr = np.asarray(values)
        if len(arr) != len(q) or not np.isfinite(arr).all():
            reasons.append(f"invalid trace {key}")
    upper_step = float(np.max(np.abs(np.diff(action[:, 12:], axis=0))))
    metrics['max_action_step_rad'] = upper_step
    if upper_step > .08:
        reasons.append(f"abrupt action step {upper_step:.4f} rad")
    palms = {s: np.asarray(trace[f'palm_{s}']) for s in ('left', 'right')}
    objects = {s: np.asarray(trace[s]) for s in ('box', 'mailer')}
    # Spatially restrict penetration checks: a zero-pose hand hanging beside
    # the torso is below table height but is not penetrating the tabletop.
    for side, p in palms.items():
        over_table = (p[:, 0] > TABLE_FRONT_X - .025) & (p[:, 0] < .9) & (np.abs(p[:, 1]) < .775)
        pen = over_table & (p[:, 2] - .049 < TABLE_TOP_Z - .004)
        metrics[f'{side}_table_pen_frames'] = int(pen.sum())
        if pen.any():
            reasons.append(f"{side} palm/table overlap proxy in {pen.sum()} frames")
    is_wait = task_id == 'wait_no_package'
    if idle or is_wait:
        for side, p in palms.items():
            spread = float(np.linalg.norm(p - p[0], axis=1).max())
            metrics[f'{side}_palm_spread_m'] = spread
            if spread > .015:
                reasons.append(f"idle {side} palm drift {spread:.4f} m")
    if is_wait:
        # Check the actual workspace footprint, not Y alone: offstage bodies
        # at x=15 m are not on the table even if their Y happens to be small.
        if any(np.any((p[:, 0] > TABLE_FRONT_X - .10) & (p[:, 0] < 1.05)
                      & (np.abs(p[:, 1]) < .90)) for p in objects.values()):
            reasons.append('wait contains a package on table')
    else:
        target = 'box' if task_id == 'push_box_to_bin' else 'mailer'
        other = 'mailer' if target == 'box' else 'box'
        hand = 'right' if target == 'box' else 'left'
        direction = -1 if target == 'box' else 1
        for key, p in objects.items():
            if abs(p[0, 1]) >= .20:
                reasons.append(f'{key} already in a sorting zone at start')
            if np.any(p[:, 2] < TABLE_TOP_Z - .01) or np.any(p[:, 0] < TABLE_FRONT_X):
                reasons.append(f'{key} dropped/off table')
            movement = float(np.linalg.norm(p[:, :2] - p[0, :2], axis=1).max())
            metrics[f'{key}_max_xy_m'] = movement
            if (idle or key == other) and movement > .015:
                reasons.append(f'non-target/idle {key} moved {movement:.4f} m > .015')
        if not idle:
            p = objects[target]
            progress = direction * (p[:, 1] - p[0, 1])
            metrics['target_final_progress_m'] = float(progress[-1])
            metrics['wrong_way_m'] = float(max(0., -progress.min()))
            if progress[-1] < .15 or not np.all(direction * p[-10:, 1] >= .20):
                reasons.append('target did not finish stably beyond +/-0.20 m with >=0.15 m progress')
            if metrics['wrong_way_m'] > .035:
                reasons.append('target wrong-way excursion > .035 m')
            if np.linalg.norm(p[-1, :2] - p[-10, :2]) > .01:
                reasons.append('target still moving at end')
            # Geometric proximity, not a measured contact force. Video review
            # is mandatory; this proxy alone never releases data to training.
            for side, palm in palms.items():
                near = (np.linalg.norm(palm[:, :2] - p[:, :2], axis=1) < .13) & (np.abs(palm[:, 2] - p[:, 2]) < .10)
                metrics[f'{side}_target_proximity_frames'] = int(near.sum())
                if side == hand and near.sum() < 3:
                    reasons.append('no sustained active-hand target proximity')
                if side != hand and near.any():
                    reasons.append('wrong hand near target')
    return {'motion_protocol': motion_protocol, 'passed': not reasons, 'reasons': reasons, 'metrics': metrics,
            'visual_review': 'pending', 'training_ready': False}


def audit_pair(first, second, *, prompts=None) -> dict:
    prompts = PAIRED_SORTING_PROMPTS if prompts is None else prompts
    reasons = []
    xyz_error = max(float(np.max(np.abs(np.asarray(first.collect_meta[k]) - second.collect_meta[k])))
                    for k in ('box_xyz', 'mailer_xyz'))
    for key in ('box_quat_xyzw', 'mailer_quat_xyzw'):
        if key in first.collect_meta or key in second.collect_meta:
            if key not in first.collect_meta or key not in second.collect_meta:
                reasons.append('paired initial orientation missing')
                continue
            a, b = (np.asarray(ep.collect_meta[key], dtype=float) for ep in (first, second))
            if a.shape != (4,) or b.shape != (4,) or not np.isfinite(a).all() or not np.isfinite(b).all():
                reasons.append('invalid paired initial quaternion')
            elif min(np.linalg.norm(a-b), np.linalg.norm(a+b)) > .002:
                reasons.append('paired initial orientations differ')
    pixel_mae = float(np.abs(first.rgb[0].astype(float) - second.rgb[0].astype(float)).mean())
    if xyz_error > .001:
        reasons.append(f'paired initial poses differ by {xyz_error:.6f} m')
    if pixel_mae > 2.0:
        reasons.append(f'paired first RGB differs by MAE {pixel_mae:.3f}')
    if np.max(np.abs(first.q[0] - second.q[0])) > 1e-4:
        reasons.append('paired initial robot states differ')
    for ep in (first, second):
        if ep.instruction != prompts[ep.task_id]:
            reasons.append('instruction/task mismatch')
    return {'passed': not reasons, 'reasons': reasons, 'xyz_error_m': xyz_error, 'pixel_mae': pixel_mae}
