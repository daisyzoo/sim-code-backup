"""Real-history predicate replay plus boundary checks, not a physics forecast."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

w = Path(__file__).resolve().parent
repo = w.parents[1]
sys.path.insert(0, str(repo))
from simfoundry.data.confirmed_position_release import ConfirmedPositionRelease as Original
from simfoundry.data.reach_sweep import ready_to_release

stage = w/'staged_confirmed_release_margin_probe'
candidate = stage/'confirmed_position_release.py'
spec = importlib.util.spec_from_file_location('release_margin_probe', candidate)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Proposed = module.ConfirmedPositionRelease
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = []
for run in ['region_causal_response_groups_r1', 'region_causal_xy_groups_r2']:
    for ep in sorted((w/run).glob('case_*/layout_*')):
        if not (ep/'frontal_bypass.json').exists():
            continue
        trace_path = ep/'trace.npz'
        fr = json.loads((ep/'frontal_bypass.json').read_text())
        direction = fr['plan']['direction']
        initial_y = fr['plan']['initial_target_xyz'][1]
        key = 'box' if 'push_box' in ep.name else 'mailer'
        with np.load(trace_path) as data:
            xyz = data[key].astype(float)
        # Observe only when the actual parent updater observed a point.
        steps = [r['step'] for r in fr['rows']]
        assert steps == sorted(set(steps))
        old = Original(initial_y, direction)
        default = Proposed(initial_y, direction)
        enabled = Proposed(initial_y, direction, require_expert_margin=True)
        old_ready, new_ready = [], []
        for t in steps:
            point = xyz[t]
            a, b, c = old.observe(point), default.observe(point), enabled.observe(point)
            assert a == b
            assert c == (a and ready_to_release(initial_y, point[1], direction))
            if a: old_ready.append(t)
            if c: new_ready.append(t)
        actual = next((r for r in fr['rows'] if r['mode']=='top_release'), None)
        rows.append(dict(run=run, episode=ep.name, observed_steps=len(steps),
            default_exact=True, old_first_ready=next(iter(old_ready), None),
            candidate_first_ready_on_recorded_history=next(iter(new_ready), None),
            actual_first_release_step=actual['step'] if actual else None,
            actual_first_release_reason=actual.get('release_reason') if actual else None,
            source_sha256={f:sha(ep/f) for f in ['trace.npz','frontal_bypass.json','raw.npz']}))

fixtures = []
for direction in [-1, 1]:
    for initial_signed in [0., .10]:
        initial = direction*initial_signed
        threshold = max(.205, initial_signed+.16)
        for delta in [-1e-7, 0., 1e-7]:
            monitor = Proposed(initial, direction, require_expert_margin=True)
            result = [monitor.observe((.5, direction*(threshold+delta), .77)) for _ in range(10)]
            assert not any(result[:9])
            assert result[-1] == (delta >= 0)
            fixtures.append(dict(direction=direction,initial_signed=initial_signed,
                                 threshold_delta=delta,ready=result[-1]))
        # Current point beyond the margin cannot bypass prior zone/stability checks.
        for bad_history in ['outside_zone', 'moving']:
            monitor = Proposed(initial, direction, require_expert_margin=True)
            first = (.48 if bad_history=='moving' else .5,
                     direction*(.19 if bad_history=='outside_zone' else threshold), .77)
            monitor.observe(first)
            for _ in range(9): value=monitor.observe((.5,direction*threshold,.77))
            assert not value
            fixtures.append(dict(direction=direction,initial_signed=initial_signed,
                                 retained_guard=bad_history,ready=value))
for invalid in [None, 0, 1, 'yes']:
    try: Proposed(0., 1, require_expert_margin=invalid)
    except ValueError: pass
    else: raise AssertionError('Nonboolean flag accepted')
report = dict(passed=True, actual_history_rows=rows, boundary_fixtures=fixtures,
    nonboolean_rejections=4, total_real_observations=sum(r['observed_steps'] for r in rows),
    candidate_sha256=sha(candidate), checker_sha256=sha(Path(__file__)),
    original_source_sha256=sha(repo/'simfoundry/data/confirmed_position_release.py'),
    expert_margin_source_sha256=sha(repo/'simfoundry/data/reach_sweep.py'),
    collector_wired=False, physical_started=False, training_ready=False,
    scope='Exact default predicate replay on recorded observations, candidate subset and '
          'existing margin independently checked. Post-release recorded states are not '
          'a forecast of continued pushing. Does not prove improved physics, lifecycle '
          'guard ordering, reachable buffered targets, or successful sorting.')
(stage/'CHECK.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['actual_history_rows','boundary_fixtures']}))
for row in rows:
    print(row['run'], row['episode'], row['old_first_ready'], row['candidate_first_ready_on_recorded_history'])
