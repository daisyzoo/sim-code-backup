"""Source-bound descriptive audit of real front-route switches and COP commands.

Does not infer hypothetical dynamics or change admission/physics thresholds.
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from scipy.spatial.transform import Rotation

p = Path(sys.argv[1]).resolve()
log = json.loads((p / 'frontal_bypass.json').read_text())
assert log['plan']['front_route_selected']
rows = log['rows']
key = 'box' if 'push_box' in p.name else 'mailer'
other = 'mailer' if key == 'box' else 'box'
with np.load(p / 'trace.npz') as z:
    xyz = z[key].astype(float)
    other_xyz = z[other].astype(float)
with np.load(p / 'parcel_orientation.npz') as z:
    rotations = {k: Rotation.from_quat(z[k]).as_matrix() for k in (key, other)}
sizes = {'box': np.array([.14, .09, .045]), 'mailer': np.array([.15, .145, .04])}
radii = {k: np.abs(rotations[k]) @ (sizes[k] / 2) for k in sizes}
gap = other_xyz[:, 0] - xyz[:, 0] - radii[other][:, 0] - radii[key][:, 0]
by_step = {r['step']: r for r in rows}
assert sorted(by_step) == list(range(1, len(xyz)))
assert max(np.max(np.abs(xyz[r['step']] - r['observed_target'])) for r in rows) < 1e-7
assert max(abs(gap[r['step']] - r['measured_front_gap_m']) for r in rows) < 2e-6
moves = np.diff(xyz[:, :2], axis=0)
bins = {}
for t, move in enumerate(moves):
    r = by_step.get(t)
    name = 'unlogged_initial' if r is None else r['route_stage'] + '/' + r['mode']
    bins.setdefault(name, []).append(move)
phase_motion = {k: dict(transitions=len(v), net_xy_mm=(np.sum(v, axis=0)*1000).tolist(),
                      positive_xy_mm=(np.maximum(v, 0).sum(axis=0)*1000).tolist(),
                      negative_xy_mm=(np.minimum(v, 0).sum(axis=0)*1000).tolist())
                for k, v in bins.items()}
assert np.allclose(np.sum([v['net_xy_mm'] for v in phase_motion.values()], axis=0),
                   (xyz[-1, :2]-xyz[0, :2])*1000, atol=1e-9)
events = []
for old, r in zip(rows, rows[1:]):
    if old['route_stage'] == r['route_stage']:
        continue
    t = r['step']
    f, prev = r.get('cop_slip_following', {}), old.get('cop_slip_following', {})
    record = dict(step=t, from_stage=old['route_stage'], to_stage=r['route_stage'],
                  mode=r['mode'], independent_gap_mm=float(gap[t]*1000),
                  object_xy_mm=(xyz[t, :2]*1000).tolist(),
                  next_object_delta_xy_mm=(moves[t]*1000).tolist() if t < len(moves) else None,
                  override=bool(f.get('override')))
    if f.get('override'):
        record.update({k: f[k] for k in ['drive_xy', 'slip_correction_xy',
                      'raw_slip_correction_xy', 'object_anchor_translation_xy',
                      'command_delta_xy', 'anchor_local', 'measured_cop_local']})
        record['anchor_carried_across_switch'] = bool(prev.get('override') and
              np.array_equal(f['anchor_local'], prev['anchor_local']))
        record['correction_x_opposes_goal_error'] = bool(f['slip_correction_xy'][0] *
                                                         (r['route_goal_x']-xyz[t, 0]) < 0)
    events.append(record)
starts = [r['step'] for r in rows if r['route_stage'] == 'lateral_y' and
          (r['step'] == 1 or by_step[r['step']-1]['route_stage'] != 'lateral_y')]
bouts = []
for t in starts:
    end = t+1
    while end in by_step and by_step[end]['route_stage'] == 'lateral_y':
        end += 1
    last_obs = min(end, len(xyz)-1)
    loaded = [by_step[i]['cop_slip_following'] for i in range(t, end)
              if by_step[i].get('cop_slip_following', {}).get('override')]
    bouts.append(dict(start=t, end_exclusive=end, frames=end-t,
                      ended_by_front_recovery=end in by_step,
                      gap_start_mm=float(gap[t]*1000), gap_end_mm=float(gap[last_obs]*1000),
                      object_delta_xy_mm=((xyz[last_obs, :2]-xyz[t, :2])*1000).tolist(),
                      loaded_steps=len(loaded),
                      median_correction_x_mm=float(np.median([f['slip_correction_xy'][0] for f in loaded])*1000) if loaded else None))
entries = [e for e in events if e['to_stage'] == 'lateral_y' and e['override']]
summary = dict(route_switches=len(events), lateral_bouts=len(bouts),
               lateral_bout_frames=[b['frames'] for b in bouts],
               first_lateral_step=starts[0] if starts else None,
               entries_with_anchor_carried=sum(e['anchor_carried_across_switch'] for e in entries),
               entries_with_correction_x_opposing_goal=sum(e['correction_x_opposes_goal_error'] for e in entries),
               lateral_entry_correction_x_mm=[e['slip_correction_xy'][0]*1000 for e in entries],
               total_net_xy_mm=((xyz[-1, :2]-xyz[0, :2])*1000).tolist(),
               non_target_max_xy_mm=float(np.max(np.linalg.norm(other_xyz[:, :2]-other_xyz[0, :2], axis=1))*1000))
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
result = dict(summary=summary, phase_motion=phase_motion, events=events, lateral_bouts=bouts,
              source_sha256={f:sha(p/f) for f in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json']},
              auditor_sha256=sha(__file__), training_ready=False,
              scope='Actual full trace: t command paired with t->t+1 displacement; independent AABB clearance from poses/quaternions; all transitions telescope to net XY. Command terms are logged values; independent COP auditor required. Association does not establish alternate-controller success. Original gates unchanged.')
(p / 'FRONT_ROUTE_FEEDBACK_DIAGNOSIS.json').write_text(json.dumps(result, indent=2))
print(json.dumps(dict(summary=summary,phase_motion=phase_motion),indent=2))
